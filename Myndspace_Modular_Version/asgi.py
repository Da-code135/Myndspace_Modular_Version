import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


from chat.routing import websocket_urlpatterns as chat_urlpatterns
from appointments.routing import websocket_urlpatterns as appointments_urlpatterns

# Combine the WebSocket URL patterns
all_websocket_urlpatterns = chat_urlpatterns + appointments_urlpatterns

# Define the ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})