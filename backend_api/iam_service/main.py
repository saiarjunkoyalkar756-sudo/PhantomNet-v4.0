from backend_api.shared.service_factory import create_phantom_service
from .api import router as iam_router

app = create_phantom_service(
    name="IAM Service",
    description="Service for Identity and Access Management.",
    version="1.0.0"
)

app.include_router(iam_router)
