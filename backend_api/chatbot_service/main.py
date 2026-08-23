from backend_api.shared.service_factory import create_phantom_service

from .api import router as chatbot_router


app = create_phantom_service(
    name="Legacy Chatbot Service",
    description="Retired ungoverned chatbot advisory boundary; no conversational security surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)
app.include_router(chatbot_router)
