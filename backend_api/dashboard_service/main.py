from backend_api.shared.service_factory import create_phantom_service
from .api import router as dashboard_router

app = create_phantom_service(
    name="Dashboard Service",
    description="Backend service for the PhantomNet dashboard and analytics visualization.",
    version="1.0.0"
)
app.include_router(dashboard_router)
