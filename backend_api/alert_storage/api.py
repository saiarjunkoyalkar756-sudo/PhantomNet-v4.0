from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from shared.database import Alert, get_db
from uuid import UUID # Import UUID
from iam_service.auth_methods import get_current_user, has_role, UserRole
from shared.database import User # Import User model to type hint current_user

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)

@router.get("/", response_model=List[Alert])
def get_alerts(
    *,
    session: Session = Depends(get_db),
    current_user: User = Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])), # RBAC applied
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    agent_id: str = None
):
    """
    Retrieve alerts from the database.
    """
    try:
        # Start with a base statement that filters by the current user's tenant_id
        statement = select(Alert).where(Alert.tenant_id == current_user.tenant_id)

        if agent_id:
            statement = statement.where(Alert.agent_id == agent_id)
        
        statement = statement.offset(offset).limit(limit)
        
        alerts = session.exec(statement).all()
        return alerts
    except Exception as e:
        # In a real app, you'd log the error
        raise HTTPException(status_code=500, detail="Internal Server Error")
