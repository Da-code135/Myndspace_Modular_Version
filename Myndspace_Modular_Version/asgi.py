import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from dotenv import load_dotenv
import django
import logging
  # Import ONLY chat routes

logger = logging.getLogger(__name__)

# Load environment variables from .env file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Myndspace_Modular_Version.settings")
load_dotenv()

# Configure Django settings *before* accessing them
django.setup()

logger.info("Django settings loaded successfully")

from .routing import websocket_urlpatterns as chat_urlpatterns

# Define the ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_urlpatterns  # Use ONLY chat routes
        )
    ),
})

logger.info("ASGI application configured successfully")