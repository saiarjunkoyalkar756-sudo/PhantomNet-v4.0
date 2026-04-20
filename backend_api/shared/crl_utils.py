# backend_api/shared/crl_utils.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import RevokedCertificate

async def is_certificate_revoked(db: AsyncSession, serial_number: str) -> bool:
    """
    Checks if a certificate serial number is in the revocation list.
    """
    stmt = select(RevokedCertificate).where(RevokedCertificate.serial_number == serial_number)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None

async def revoke_certificate(db: AsyncSession, serial_number: str, reason: str = "Unspecified"):
    """
    Adds a certificate serial number to the revocation list.
    """
    if not await is_certificate_revoked(db, serial_number):
        revoked_cert = RevokedCertificate(serial_number=serial_number, reason=reason)
        db.add(revoked_cert)
        await db.flush()
        return True
    return False
