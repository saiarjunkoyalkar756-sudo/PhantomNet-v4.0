# backend_api/iam_service/api.py
import os
import uuid
import secrets
import pyotp
import jwt
from datetime import timedelta, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend_api.shared.database import (
    get_db, 
    User, 
    SessionToken, 
    PasswordResetToken, 
    RecoveryCode
)
from backend_api.shared.schemas import (
    UserCreate, 
    UserInDB, 
    Token, 
    TokenData,
    PasswordResetRequest, 
    PasswordResetConfirm, 
    RecoveryCodeResponse, 
    TwoFACode, 
    TwoFAChallenge, 
    MFARequiredResponse, 
    LoginRequest
)
from .auth_methods import (
    generate_totp_secret, 
    verify_totp_code, 
    authenticate_user,
    get_current_user, 
    get_password_hash, 
    create_access_token, 
    get_user,
    UserRole, 
    has_role, 
    SECRET_KEY, 
    ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_recovery_code, 
    hash_recovery_code, 
    verify_recovery_code, 
    RECOVERY_CODE_COUNT, 
    calculate_anomaly_score
)
from backend_api.core.logging import logger as pn_logger
from backend_api.core.response import success_response, error_response

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Default tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

@router.post("/register")
async def register_user(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db), 
    request: Request = None
):
    """Registers a new user and returns an access token."""
    existing_user = await get_user(db, username=user_data.username)
    if existing_user:
        return error_response(code="ALREADY_EXISTS", message="Username already registered", status_code=400)
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role or "user",
        tenant_id=DEFAULT_TENANT_ID
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    pn_logger.info(f"User {new_user.username} registered successfully.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_data = {
        "sub": str(new_user.id),
        "username": new_user.username,
        "role": new_user.role,
        "twofa_enabled": False,
        "twofa_enforced": False,
        "tenant_id": str(new_user.tenant_id)
    }
    
    access_token = await create_access_token(
        db,
        user_id=new_user.id,
        data=jwt_data,
        expires_delta=access_token_expires,
        request=request,
    )
    
    return success_response(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": new_user.username, "role": new_user.role}
    })

@router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    x_device_fingerprint: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
    x_2fa_code: Optional[str] = Header(None, alias="X-2FA-Code"),
    x_recovery_code: Optional[str] = Header(None, alias="X-Recovery-Code"),
):
    """Authenticates a user and returns an access token."""
    ip_address = request.client.host if request.client else "unknown"
    
    user = await get_user(db, form_data.username)
    anomaly_score = 0.0
    if user:
        anomaly_score = await calculate_anomaly_score(
            db, user.id, ip_address, x_device_fingerprint, None, None
        )
        if anomaly_score > 0.5:
            pn_logger.warning(f"Anomaly detected for user {user.username} (score: {anomaly_score})")

    user, auth_status = await authenticate_user(
        db,
        form_data.username,
        form_data.password,
        totp_code=x_2fa_code,
        recovery_code=x_recovery_code,
    )

    if auth_status == "2FA_REQUIRED":
        return error_response(
            code="2FA_REQUIRED", 
            message="2FA required", 
            status_code=401,
            headers={"WWW-Authenticate": "Bearer", "X-2FA-Required": "true"}
        )
    
    if not user:
        pn_logger.warning(f"Failed login attempt for user {form_data.username}.")
        return error_response(code="UNAUTHORIZED", message="Incorrect username or password", status_code=401)

    pn_logger.info(f"User {user.username} logged in successfully.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_data = {
        "sub": user.username,
        "role": user.role,
        "twofa_enabled": user.totp_secret is not None,
        "twofa_enforced": user.twofa_enforced,
        "tenant_id": str(user.tenant_id)
    }
    
    access_token = await create_access_token(
        db,
        user_id=user.id,
        data=jwt_data,
        expires_delta=access_token_expires,
        request=request,
        device_fingerprint=x_device_fingerprint,
        anomaly_score=anomaly_score,
    )
    
    return success_response(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user.username, "role": user.role}
    })

@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Returns the current authenticated user's profile."""
    return success_response(data={
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "tenant_id": str(current_user.tenant_id)
    })

@router.post("/request-password-reset")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generates a password reset token and 'sends' an email."""
    user = await get_user(db, username=reset_request.username)
    if not user:
        return error_response(code="NOT_FOUND", message="User not found", status_code=404)

    # Clean old tokens
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    
    token = await create_access_token(
        db,
        user_id=user.id,
        data={"sub": user.username, "type": "password_reset"},
        expires_delta=timedelta(hours=1),
        request=request,
    )
    
    new_token_db = PasswordResetToken(user_id=user.id, token=token)
    db.add(new_token_db)
    await db.commit()

    pn_logger.info(f"Password reset token generated for {user.username}.")
    return success_response(message="Password reset email sent (simulated).", data={"token": token})

@router.post("/confirm-password-reset")
async def confirm_password_reset(
    confirm_request: PasswordResetConfirm, 
    db: AsyncSession = Depends(get_db)
):
    """Uses a reset token to update the user's password."""
    try:
        payload = jwt.decode(confirm_request.token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise Exception("Invalid payload")
    except Exception:
        return error_response(code="INVALID_TOKEN", message="Invalid or expired token", status_code=401)

    user = await get_user(db, username=username)
    if not user:
        return error_response(code="INVALID_TOKEN", message="Invalid or expired token", status_code=401)

    stmt = select(PasswordResetToken).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.token == confirm_request.token
    )
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()
    
    if not token_obj or token_obj.expires_at < datetime.utcnow():
        return error_response(code="INVALID_TOKEN", message="Invalid or expired token", status_code=401)

    user.hashed_password = get_password_hash(confirm_request.new_password)
    await db.delete(token_obj)
    await db.commit()

    pn_logger.info("Password reset successfully via token.")
    return success_response(message="Password has been reset successfully")

@router.post("/enable-2fa")
async def enable_2fa(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Enables 2FA by generating a TOTP secret."""
    if current_user.totp_secret:
        return error_response(code="ALREADY_ENABLED", message="2FA is already enabled.", status_code=400)

    secret = generate_totp_secret()
    current_user.totp_secret = secret
    await db.commit()

    pn_logger.info(f"User {current_user.username} generated 2FA secret.")
    return success_response(data={"secret": secret}, message="2FA secret generated. Please verify.")

@router.post("/verify-2fa")
async def verify_2fa(
    twofa_code: TwoFACode, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Verifies a TOTP code and enforcements 2FA, returning recovery codes."""
    if not current_user.totp_secret:
        return error_response(code="NOT_ENABLED", message="2FA is not enabled.", status_code=400)

    if not verify_totp_code(current_user.totp_secret, twofa_code.code):
        pn_logger.warning(f"User {current_user.username} failed 2FA verification.")
        return error_response(code="INVALID_CODE", message="Invalid 2FA code.", status_code=401)

    # Generate recovery codes
    recovery_codes = [generate_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
    for code in recovery_codes:
        hashed_code = hash_recovery_code(code)
        db_recovery_code = RecoveryCode(user_id=current_user.id, code_hash=hashed_code)
        db.add(db_recovery_code)
    
    current_user.twofa_enforced = True
    await db.commit()

    pn_logger.info(f"User {current_user.username} verified 2FA and received recovery codes.")
    return success_response(data={"recovery_codes": recovery_codes}, message="2FA verified successfully.")

@router.post("/disable-2fa")
async def disable_2fa(
    twofa_code: TwoFACode, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Disables 2FA given a valid code."""
    if not current_user.totp_secret:
        return error_response(code="NOT_ENABLED", message="2FA is not enabled.", status_code=400)

    if not verify_totp_code(current_user.totp_secret, twofa_code.code):
        pn_logger.warning(f"User {current_user.username} failed to disable 2FA.")
        return error_response(code="INVALID_CODE", message="Invalid 2FA code.", status_code=401)

    current_user.totp_secret = None
    current_user.twofa_enforced = False
    
    await db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == current_user.id))
    await db.commit()

    pn_logger.info(f"User {current_user.username} disabled 2FA.")
    return success_response(message="2FA disabled successfully.")

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Invalidates the current session token."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                stmt = select(SessionToken).where(SessionToken.jti == jti)
                result = await db.execute(stmt)
                session_record = result.scalar_one_or_none()
                if session_record:
                    session_record.is_valid = False
                    session_record.revoked_at = datetime.utcnow()
                    await db.commit()
                    pn_logger.info(f"User {current_user.username} logged out, session {jti} invalidated.")
        except Exception:
            pass

    return success_response(message="Logged out successfully")
