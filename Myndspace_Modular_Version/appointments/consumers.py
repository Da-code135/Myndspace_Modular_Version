import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Appointment
from users.models import User

logger = logging.getLogger(__name__)

class VideoCallConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.appointment = None
        self.peer_connections = {} # Track active peer connections

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

        # Notify group about new user *and* existing users to the new user
        await self.send_user_list()  # Send the current user list to the new user

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

        # Remove peer connection if exists
        if self.user.id in self.peer_connections:
            del self.peer_connections[self.user.id]

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
        await self.send_user_list()

    async def user_leave(self, event):
        await self.send_user_list()

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
        # This function is not working as intended.
        # It returns channel names which are not what you want.
        # This function returns connected users but not the User ID's
        return list(self.channel_layer.groups.get(self.room_group_name, {}).keys())

    async def send_user_list(self):
        user_ids = await self.get_connected_user_ids()
        users = await self.get_user_details(user_ids)  # Fetch username for each user ID

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update.user.list',
                'users': users,
            }
        )

    async def update_user_list(self, event):
        # Send user list to the specific recipient
        await self.send(text_data=json.dumps({
            'type': 'user.list',
            'users': event['users']
        }))

    @database_sync_to_async
    def get_connected_user_ids(self):
        group = self.channel_layer.groups.get(self.room_group_name, {})
        channel_names = list(group.keys())
        user_ids = set()

        for channel_name in channel_names:
             # Extract user ID from the scope associated with the channel name
            scope = self.channel_layer.scope_for_channel(channel_name)
            # Check if scope is not None and contains the 'user' key
            if scope and scope.get('user'):
                 user = scope.get('user')
                # Check if the user is authenticated and has an ID
                 if user and user.is_authenticated:
                   user_ids.add(str(user.id))

        return list(user_ids)

    @database_sync_to_async
    def get_user_details(self, user_ids):
        users = []
        for user_id in user_ids:
            user = User.objects.get(id=user_id) # use .get
            users.append({'user_id': str(user.id), 'username': user.username}) # Append username to list for transmission
        return users