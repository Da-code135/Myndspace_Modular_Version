import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns  # Import WebSocket routes

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Myndspace_Modular_Version.settings')

# Define the ASGI application
application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's ASGI application
    "http": get_asgi_application(),

    # WebSocket requests are handled by Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Use the WebSocket routes from chat/routing.py
        )
    ),
})
