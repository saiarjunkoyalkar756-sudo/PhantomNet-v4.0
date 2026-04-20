from backend_api.shared.service_factory import create_phantom_service
from .api import router as agent_command_router

app = create_phantom_service(
    name="Agent Command Service",
    description="Service for sending commands to agents.",
    version="1.0.0"
)

app.include_router(agent_command_router)
