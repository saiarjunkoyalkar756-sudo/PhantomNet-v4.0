from backend_api.shared.service_factory import create_phantom_service
from .api import router as ip_info_router

app = create_phantom_service(
    name="IP Info Service",
    description="Enriches events with geolocation and reputation data for IP addresses.",
    version="1.0.0"
)

app.include_router(ip_info_router)
