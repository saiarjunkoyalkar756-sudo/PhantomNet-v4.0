from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from ..auth import get_current_user, User, UserRole, has_role
from features.ai_autonomy_levels.autonomy_manager import AutonomyManager

router = APIRouter()

# Instantiate AutonomyManager within the router file
autonomy_manager = AutonomyManager()

class AutonomyLevelRequest(BaseModel):
    level: str = Field(..., description="The desired autonomy level (A1-A5).")

@router.post("/autonomy", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def set_autonomy_level(
    request: AutonomyLevelRequest, current_user: User = Depends(get_current_user)
):
    """
    Sets the global AI autonomy level for PhantomNet.
    Requires Admin privileges.
    """
    result = autonomy_manager.set_autonomy_level(request.level)
    if result["status"] == "success":
        # In a real app, you might use logger here, but for now print
        print(
            f"User {current_user.username} set autonomy level to {result['new_level']}"
        )
        return result
    else:
        print(
            f"User {current_user.username} failed to set autonomy level with value: {request.level}"
        )
        raise HTTPException(status_code=400, detail=result["message"])