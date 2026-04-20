from backend_api.shared.service_factory import create_phantom_service
from .api import router as config_router

app = create_phantom_service(
    name="Config Service",
    description="Service for managing agent configuration.",
    version="1.0.0"
)

app.include_router(config_router)
