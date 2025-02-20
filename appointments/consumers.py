
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Appointment

logger = logging.getLogger(__name__)

class VideoCallConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.appointment = None

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_{self.room_id}'
        self.user = self.scope["user"]

        # Validate appointment access
        self.appointment = await self.get_appointment()
        if not await self.validate_participant():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Notify group about new user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.join',
                'user_id': str(self.user.id),
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        # Notify group about user leaving
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.leave',
                'user_id': str(self.user.id),
                'username': self.user.username
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Handle different WebRTC signal types
            if message_type in ['offer', 'answer', 'candidate']:
                await self.handle_webrtc_signal(data)
            elif message_type == 'chat':
                await self.handle_chat_message(data)
            elif message_type == 'keepalive':
                await self.send(text_data=json.dumps({'type': 'pong'}))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def handle_webrtc_signal(self, data):
        # Forward WebRTC signals to target user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc.signal',
                'sender_id': str(self.user.id),
                'recipient_id': data.get('target'),
                'payload': data
            }
        )

    async def handle_chat_message(self, data):
        # Broadcast chat messages to all participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'sender': self.user.username,
                'message': data.get('message'),
                'timestamp': data.get('timestamp')
            }
        )

    async def webrtc_signal(self, event):
        # Send WebRTC signals to specific recipient
        if str(self.user.id) == event['recipient_id']:
            await self.send(text_data=json.dumps({
                'type': event['payload']['type'],
                'sender': event['sender_id'],
                **event['payload']
            }))

    async def user_join(self, event):
        # Send user list updates to all participants
        users = await self.get_room_users()
        await self.send(text_data=json.dumps({
            'type': 'user.join',
            'user_id': event['user_id'],
            'username': event['username'],
            'users': users
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user.leave',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'sender': event['sender'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_appointment(self):
        try:
            return Appointment.objects.get(room_id=self.room_id)
        except Appointment.DoesNotExist:
            return None

    @database_sync_to_async
    def validate_participant(self):
        if isinstance(self.user, AnonymousUser):
            return False
        return self.user in [self.appointment.doctor, self.appointment.client]

    @database_sync_to_async
    def get_room_users(self):
        return list(self.channel_layer.groups.get(self.room_group_name, {}).keys())