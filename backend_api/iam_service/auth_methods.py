# backend_api/iam_service/auth_methods.py
import os
import uuid
import pyotp
import base64
import secrets
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from jose import JWTError, jwt
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import hashes
import httpx

from backend_api.shared.secret_manager import get_secret
from backend_api.shared.database import (
    User,
    SessionToken,
    RecoveryCode,
    get_db
)
from backend_api.shared.schemas import TokenData
from backend_api.core.logging import logger as pn_logger

# Password hashing
def get_password_hash(password: str) -> bytes:
    salt = os.urandom(16)
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    hashed_password = kdf.derive(password.encode())
    return salt + hashed_password

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    if not hashed_password:
        return False
    salt = hashed_password[:16]
    stored_hash = hashed_password[16:]
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    try:
        kdf.verify(plain_password.encode(), stored_hash)
        return True
    except InvalidKey:
        return False

# JWT settings
SECRET_KEY = get_secret("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    USER = "user"

# Recovery Code functions
RECOVERY_CODE_LENGTH = 10
RECOVERY_CODE_COUNT = 8

def generate_recovery_code():
    return "".join(
        secrets.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for i in range(RECOVERY_CODE_LENGTH)
    )

def hash_recovery_code(code: str):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(code.encode())
    return digest.finalize().hex()

def verify_recovery_code(plain_code: str, hashed_code: str):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(plain_code.encode())
    return digest.finalize().hex() == hashed_code

async def calculate_anomaly_score(
    db: AsyncSession,
    user_id: int,
    ip_address: str,
    device_fingerprint: str,
    city: Optional[str] = None,
    country: Optional[str] = None,
) -> float:
    """
    Calculates an anomaly score based on historical session data.
    """
    stmt = select(SessionToken).where(SessionToken.user_id == user_id).order_by(SessionToken.created_at.desc()).limit(10)
    result = await db.execute(stmt)
    historical_sessions = result.scalars().all()

    if not historical_sessions:
        return 0.0

    score = 0.0

    # Check for new IP
    if not any(session.ip == ip_address for session in historical_sessions):
        score += 0.5

    # Check for new device fingerprint
    if device_fingerprint and not any(
        session.device_fingerprint == device_fingerprint
        for session in historical_sessions
    ):
        score += 0.7 

    # Check for new city
    if city and not any(session.city == city for session in historical_sessions):
        score += 0.2

    return min(score, 1.0)

async def create_access_token(
    db: AsyncSession,
    user_id: int,
    data: dict,
    expires_delta: Optional[timedelta] = None,
    request: Optional[Request] = None,
    device_fingerprint: Optional[str] = None,
    anomaly_score: Optional[float] = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Generate JTI
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Create session token record in the database
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("User-Agent") if request and request.headers else None

    # Fetch geolocation data (async)
    city, region, country, latitude, longitude = None, None, None, None, None

    if ip_address and ip_address not in ["127.0.0.1", "localhost", "::1"]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://ip-api.com/json/{ip_address}", timeout=2.0)
                if response.status_code == 200:
                    geo_data = response.json()
                    if geo_data.get("status") == "success":
                        city = geo_data.get("city")
                        region = geo_data.get("regionName")
                        country = geo_data.get("country")
                        latitude = geo_data.get("lat")
                        longitude = geo_data.get("lon")
        except Exception as e:
            pn_logger.warning(f"Geolocation lookup failed for {ip_address}: {str(e)}")

    session_token = SessionToken(
        jti=jti,
        user_id=user_id,
        created_at=datetime.utcnow(),
        expires_at=expire,
        ip=ip_address,
        user_agent=user_agent,
        device_fingerprint=device_fingerprint,
        anomaly_score=anomaly_score,
        is_valid=True,
        city=city,
        region=region,
        country=country,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(session_token)
    await db.flush() # Ensure it's ready for commit by caller

    return encoded_jwt

def generate_totp_secret():
    return base64.b32encode(os.urandom(10)).decode("utf-8")

def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

async def get_user(db: AsyncSession, username: str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
    totp_code: Optional[str] = None,
    recovery_code: Optional[str] = None,
):
    user = await get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None, None

    # Check for 2FA
    if user.twofa_enforced or user.totp_secret:
        if totp_code:
            if not user.totp_secret or not verify_totp_code(
                user.totp_secret, totp_code
            ):
                return None, None
        elif recovery_code:
            # Verify recovery code
            stmt = select(RecoveryCode).where(
                RecoveryCode.user_id == user.id,
                RecoveryCode.used_at == None
            )
            result = await db.execute(stmt)
            recovery_record = result.scalar_one_or_none()
            
            if not recovery_record or not verify_recovery_code(
                recovery_code, recovery_record.code_hash
            ):
                return None, None

            # Mark recovery code as used
            recovery_record.used_at = datetime.utcnow()
            await db.flush()
        else:
            return user, "2FA_REQUIRED"

    return user, None

async def get_current_user(
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    # Support both cookie and header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_role: str = payload.get("role")
        jti: str = payload.get("jti")
        tenant_id_str: str = payload.get("tenant_id")

        if not all([username, user_role, jti, tenant_id_str]):
            raise credentials_exception

        # Validate session token in DB
        stmt = select(SessionToken).where(SessionToken.jti == jti)
        result = await db.execute(stmt)
        session_record = result.scalar_one_or_none()
        
        if (
            not session_record
            or not session_record.is_valid
            or session_record.revoked_at
            or session_record.expires_at < datetime.utcnow()
        ):
            raise credentials_exception

        token_data = TokenData(
            username=username,
            role=user_role,
            tenant_id=uuid.UUID(tenant_id_str)
        )
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    return user

def has_role(required_roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in [role.value for role in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    return role_checker
