# chat/routing.py
from django.urls import re_path
from . import minimal_consumer  # Changed import

websocket_urlpatterns = [
    re_path(r'^ws/test/$', minimal_consumer.MinimalConsumer.as_asgi()),  # Changed regex and consumer
]