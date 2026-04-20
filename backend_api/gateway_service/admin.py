# backend_api/gateway_service/admin.py
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel

from backend_api.shared.database import (
    get_db,
    User,
    BlacklistedIP,
)
from backend_api.shared.schemas import UserInDB
from backend_api.iam_service.auth_methods import has_role, UserRole
from backend_api.core.response import success_response, error_response
from backend_api.core.logging import logger as pn_logger

router = APIRouter(prefix="/admin", tags=["Admin"])

class BlacklistRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = None

@router.post("/blacklist/add")
async def add_to_blacklist(
    blacklist_request: BlacklistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_role([UserRole.ADMIN])),
):
    stmt = select(BlacklistedIP).where(BlacklistedIP.ip_address == blacklist_request.ip_address)
    result = await db.execute(stmt)
    existing_ip = result.scalar_one_or_none()
    
    if existing_ip:
        return error_response(
            code="ALREADY_EXISTS",
            message="IP address already blacklisted",
            status_code=400
        )

    new_blacklisted_ip = BlacklistedIP(
        ip_address=blacklist_request.ip_address, 
        reason=blacklist_request.reason
    )
    db.add(new_blacklisted_ip)
    await db.commit()
    
    pn_logger.info(f"IP {blacklist_request.ip_address} blacklisted by {current_user.username}")
    
    return success_response(
        data={"message": f"IP address {blacklist_request.ip_address} has been blacklisted"}
    )

@router.post("/blacklist/remove")
async def remove_from_blacklist(
    blacklist_request: BlacklistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_role([UserRole.ADMIN])),
):
    stmt = select(BlacklistedIP).where(BlacklistedIP.ip_address == blacklist_request.ip_address)
    result = await db.execute(stmt)
    blacklisted_ip = result.scalar_one_or_none()
    
    if not blacklisted_ip:
        return error_response(
            code="NOT_FOUND",
            message="IP address not found in blacklist",
            status_code=404
        )

    await db.delete(blacklisted_ip)
    await db.commit()
    
    pn_logger.info(f"IP {blacklist_request.ip_address} removed from blacklist by {current_user.username}")
    
    return success_response(
        data={"message": f"IP address {blacklist_request.ip_address} has been removed from the blacklist"}
    )

@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_role([UserRole.ADMIN])),
    search: Optional[str] = Query(None, description="Search by username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    stmt = select(User)
    if search:
        stmt = stmt.where(User.username.ilike(f"%{search}%"))
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # Standardize output manually as we want the envelope
    user_list = [UserInDB.model_validate(u).model_dump() for u in users]
    
    return success_response(data=user_list)
