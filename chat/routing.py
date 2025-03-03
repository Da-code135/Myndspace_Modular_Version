from django.urls import re_path
from chat import consumers as chat_consumers


chat_websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_id>[0-9a-f-]+)/$', chat_consumers.ChatConsumer.as_asgi()),
    # Add your other WebSocket URL patterns here (e.g., from appointments)
]
