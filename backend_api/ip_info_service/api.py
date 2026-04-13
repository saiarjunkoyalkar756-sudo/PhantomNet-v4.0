from fastapi import APIRouter, Depends, HTTPException
import httpx
from loguru import logger

from iam_service.auth_methods import get_current_user, User, UserRole, has_role

router = APIRouter()

@router.get(
    "/ip-info/{ip_address}",
    dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))],
)
async def get_ip_info(ip_address: str, current_user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://ip-api.com/json/{ip_address}")
        if response.status_code == 200:
            logger.info(
                f"User ID: {current_user.id} fetched IP info for IP: {ip_address}."
            )  # Redact username
            return response.json()
        else:
            logger.error(
                f"User ID: {current_user.id} failed to fetch IP info for IP: {ip_address}: Status {response.status_code}"
            )  # Redact username
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch IP info: {response.text}",
            )
