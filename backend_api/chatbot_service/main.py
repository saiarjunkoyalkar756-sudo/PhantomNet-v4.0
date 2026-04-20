from backend_api.shared.service_factory import create_phantom_service
from .api import router as chatbot_router

app = create_phantom_service(
    name="Chatbot Service",
    description="Backend service for the SOC Copilot chatbot interface, enabling natural language investigation and analysis.",
    version="1.0.0"
)
app.include_router(chatbot_router)
