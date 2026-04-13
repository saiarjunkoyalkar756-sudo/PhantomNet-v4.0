from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from typing import Optional
import os
import pyotp
import uuid # For JTI generation
import secrets # For recovery codes
from loguru import logger
from uuid import UUID # Import UUID

# Default tenant ID for new users (until multi-tenant registration is fully implemented)
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

from shared.database import User, SessionLocal, SessionToken, PasswordResetToken, RecoveryCode # Import RecoveryCode
from shared.schemas import (
    UserCreate, UserInDB, Token, TokenData,
    PasswordResetRequest, PasswordResetConfirm, RecoveryCodeResponse, TwoFACode, TwoFAChallenge, MFARequiredResponse, LoginRequest
)
from .auth_methods import (
    generate_totp_secret, verify_totp_code, authenticate_user,
    get_current_user, get_password_hash, create_access_token, get_user,
    UserRole, has_role, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_recovery_code, hash_recovery_code, verify_recovery_code, RECOVERY_CODE_COUNT, calculate_anomaly_score
)
from shared.database import get_db # Import get_db from shared.database

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/register", response_model=UserInDB)
async def register_user(
    user: UserCreate, db: Session = Depends(lambda: get_db("operational")), request: Request = None
):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        tenant_id=DEFAULT_TENANT_ID # Assign default tenant ID
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"User {db_user.username} (ID: {db_user.id}) registered successfully.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jwt_data = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "role": db_user.role,
        "twofa_enabled": db_user.totp_secret is not None,
        "twofa_enforced": db_user.twofa_enforced,
        "tenant_id": str(db_user.tenant_id) # Include tenant ID in JWT
    }
    access_token = create_access_token(
        db,
        user_id=db_user.id,
        data=jwt_data,
        expires_delta=access_token_expires,
        request=request,
    )
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "user": {"username": db_user.username, "role": db_user.role}})
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, expires=access_token_expires.total_seconds()
    )
    return response

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(lambda: get_db("operational")),
    x_device_fingerprint: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
    x_2fa_code: Optional[str] = Header(None, alias="X-2FA-Code"),
    x_recovery_code: Optional[str] = Header(None, alias="X-Recovery-Code"),
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    user = get_user(db, form_data.username)
    if user:
        anomaly_score = calculate_anomaly_score(
            db, user.id, ip_address, x_device_fingerprint, None, None
        )

        if anomaly_score > 0.5:
            logger.warning(
                f"Anomaly detected for user {user.username} (score: {anomaly_score})"
            )

    user, auth_status = authenticate_user(
        db,
        form_data.username,
        form_data.password,
        totp_code=x_2fa_code,
        recovery_code=x_recovery_code,
    )

    if auth_status == "2FA_REQUIRED":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA required",
            headers={"WWW-Authenticate": "Bearer", "X-2FA-Required": "true"},
        )
    if not user:
        logger.warning(f"Failed login attempt for user {form_data.username}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User {user.username} (ID: {user.id}) logged in successfully.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jwt_data = {
        "sub": user.username,
        "role": user.role,
        "twofa_enabled": user.totp_secret is not None,
        "twofa_enforced": user.twofa_enforced,
        "tenant_id": str(user.tenant_id) # Include tenant ID in JWT
    }
    access_token = create_access_token(
        db,
        user_id=user.id,
        data=jwt_data,
        expires_delta=access_token_expires,
        request=request,
        device_fingerprint=x_device_fingerprint,
        anomaly_score=anomaly_score,
    )
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "user": {"username": user.username, "role": user.role}})
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, expires=access_token_expires.total_seconds()
    )
    return response

@router.get("/users/me/", response_model=UserInDB)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/request-password-reset")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(lambda: get_db("operational")),
):
    user = get_user(db, username=reset_request.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_db = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user.id)
        .first()
    )
    if token_db:
        db.delete(token_db)
        db.commit()

    token = create_access_token(
        db,
        user_id=user.id,
        data={"sub": user.username},
        expires_delta=timedelta(hours=1),
        request=request,
    )
    new_token_db = PasswordResetToken(user_id=user.id, token=token)
    db.add(new_token_db)
    db.commit()

    logger.info(f"Password reset email sent to {user.username}.")
    return {"message": "Password reset email sent"}

@router.post("/confirm-password-reset")
async def confirm_password_reset(
    confirm_request: PasswordResetConfirm, db: Session = Depends(lambda: get_db("operational"))
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )
    try:
        payload = jwt.decode(confirm_request.token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception

    token_db = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token == confirm_request.token,
        )
        .first()
    )
    if token_db is None or token_db.expires_at < datetime.utcnow():
        raise credentials_exception

    user.hashed_password = get_password_hash(confirm_request.new_password)
    db.delete(token_db)
    db.commit()

    logger.info(f"Password reset successfully.")
    return {"message": "Password has been reset successfully"}

@router.post("/enable-2fa")
async def enable_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(lambda: get_db("operational"))):
    if current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    secret = generate_totp_secret()
    current_user.totp_secret = secret
    db.commit()

    logger.info(f"User {current_user.username} (ID: {current_user.id}) enabled 2FA.")

    return {"secret": secret, "message": "2FA enabled. Please verify with a TOTP code."}

@router.post("/verify-2fa")
async def verify_2fa(
    twofa_code: TwoFACode, current_user: User = Depends(get_current_user), db: Session = Depends(lambda: get_db("operational"))
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    if not verify_totp_code(current_user.totp_secret, twofa_code.code):
        logger.warning(f"User {current_user.username} (ID: {current_user.id}) failed 2FA verification.")
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    recovery_codes = [generate_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
    for code in recovery_codes:
        hashed_code = hash_recovery_code(code)
        db_recovery_code = RecoveryCode(user_id=current_user.id, code_hash=hashed_code)
        db.add(db_recovery_code)
    
    current_user.twofa_enforced = True
    db.commit()
    db.refresh(current_user)

    logger.info(f"User {current_user.username} (ID: {current_user.id}) successfully verified 2FA.")

    return RecoveryCodeResponse(message="2FA verified successfully. Save your recovery codes.", recovery_codes=recovery_codes)

@router.post("/disable-2fa")
async def disable_2fa(
    twofa_code: TwoFACode, current_user: User = Depends(get_current_user), db: Session = Depends(lambda: get_db("operational"))
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    if not verify_totp_code(current_user.totp_secret, twofa_code.code):
        logger.warning(f"User {current_user.username} (ID: {current_user.id}) failed to disable 2FA.")
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    current_user.totp_secret = None
    current_user.twofa_enforced = False
    db.query(RecoveryCode).filter(RecoveryCode.user_id == current_user.id).delete()
    db.commit()

    logger.info(f"User {current_user.username} (ID: {current_user.id}) disabled 2FA.")

    return {"message": "2FA disabled successfully."}

@router.get("/recovery-codes", response_model=RecoveryCodeResponse)
async def get_recovery_codes(current_user: User = Depends(get_current_user), db: Session = Depends(lambda: get_db("operational"))):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled, no recovery codes available.")
    
    recovery_codes_db = db.query(RecoveryCode).filter(
        RecoveryCode.user_id == current_user.id,
        RecoveryCode.used_at == None
    ).all()

    if not recovery_codes_db:
        recovery_codes = [generate_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
        for code in recovery_codes:
            hashed_code = hash_recovery_code(code)
            db_recovery_code = RecoveryCode(user_id=current_user.id, code_hash=hashed_code)
            db.add(db_recovery_code)
        db.commit()
        logger.info(f"User {current_user.username} (ID: {current_user.id}) generated new recovery codes.")
        return RecoveryCodeResponse(message="New recovery codes generated. Save them securely.", recovery_codes=recovery_codes)
    else:
        raise HTTPException(status_code=400, detail="Recovery codes already exist and should have been saved during 2FA setup. For security, existing codes cannot be retrieved. You can disable and re-enable 2FA to generate new ones.")

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(lambda: get_db("operational"))):
    token = response.cookies.get("access_token")

    if not token:
        auth_header = response.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti: str = payload.get("jti")
            if jti:
                session_record = db.query(SessionToken).filter(SessionToken.jti == jti).first()
                if session_record:
                    session_record.is_valid = False
                    session_record.revoked_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"User {current_user.username} (ID: {current_user.id}) logged out successfully, session {jti} invalidated.")
        except JWTError:
            logger.warning(f"Invalid JWT during logout attempt for user {current_user.username}. Token: {token}")

    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
