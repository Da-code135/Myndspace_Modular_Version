import os
from channels import routing
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



django_asgi_app = get_asgi_application()

import chat.routing 

# Define the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
                chat.routing.websocket_urlpatterns  # Use ONLY chat routes
        )
    ),
})

logger.info("ASGI application configured successfully")
