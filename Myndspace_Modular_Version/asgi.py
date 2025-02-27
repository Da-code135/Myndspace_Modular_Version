"""
ASGI config for Myndspace_Modular_Version project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from dotenv import load_dotenv
import django
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Myndspace_Modular_Version.settings')

# Configure Django settings *before* accessing them
django.setup()

from chat.routing import websocket_urlpatterns as chat_urlpatterns
from appointments.routing import websocket_urlpatterns as appointments_urlpatterns

# Combine the WebSocket URL patterns
all_websocket_urlpatterns = chat_urlpatterns + appointments_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})