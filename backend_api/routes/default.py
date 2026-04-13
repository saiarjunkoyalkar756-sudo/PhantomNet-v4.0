from fastapi import APIRouter
from loguru import logger

router = APIRouter()

@router.get("/")
def home():
    logger.info("Root endpoint accessed.")  # Use logger
    return {"message": "PhantomNet API Running"}
