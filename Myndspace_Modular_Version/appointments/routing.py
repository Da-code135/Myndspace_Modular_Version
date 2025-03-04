from django.urls import re_path
from . import consumers

video_websocket_urlpatterns = [
    re_path(r'ws/video/(?P<room_id>[0-9a-f-]+)/$', consumers.VideoCallConsumer.as_asgi()),
]