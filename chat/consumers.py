import json
import logging
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.utils.html import escape
from django.core.cache import cache
from .models import ChatRoom, ChatMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.user = None
        self.room_group_name = None
        self.access_verified = False

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope["user"]
        self.room_group_name = f'chat_{self.room_id}'

        self.ping_task = asyncio.create_task(self.send_pings())

        if not await self.verify_room_access():
            logger.warning(f"Unauthorized user {self.user.id} tried to access room {self.room_id}")
            await self.close(code=4003)
            return

        self.access_verified = True

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'ping_task'):
            self.ping_task.cancel()
            try:
                await self.ping_task
            except asyncio.CancelledError:
                pass

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'ping':
                await self.send(json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type} from user {self.user.id}")

        except json.JSONDecodeError as e:
               logger.error(f"Invalid JSON received from user {self.user.id}: {e}", exc_info=True)
               await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid JSON'}))  # Send error to client
        except Exception as e:
                logger.error(f"Error processing message from user {self.user.id}: {e}", exc_info=True)
                await self.send(text_data=json.dumps({'type': 'error', 'message': 'Server error'}))  # Send error to client

    async def handle_message(self, data):
        message = data.get('message', '').strip()
        if not message:
            logger.warning(f"Empty message received from user {self.user.id}")
            return

        sanitized_message = escape(message)

        db_message = await self.save_message(sanitized_message)

        message_html = await self.render_message(db_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_html': message_html,
                'sender': self.user.username,
                'timestamp': db_message.timestamp.isoformat(),
                'message_id': db_message.id
            }
        )

    async def handle_typing(self, data):
        typing = data.get('typing', False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_typing',
                'typing': typing,
                'sender': self.user.username
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        if not message_id:
            logger.warning(f"Read receipt received without message_id from user {self.user.id}")
            return
        await self.mark_message_read(message_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_read_receipt',
                'message_id': message_id,
                'reader': self.user.username
            }
        )

    async def chat_message(self, event):

        await self.send(json.dumps({
            'type': 'message',
            'message': event['message_html'],  # changed from event[message]
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def chat_typing(self, event):
        await self.send(json.dumps({
            'type': 'typing',
            'typing': event['typing'],
            'sender': event['sender']
        }))

    async def chat_read_receipt(self, event):
        await self.send(json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'reader': event['reader']
        }))

    async def send_pings(self):
        try:
            while True:
                await self.send(json.dumps({'type': 'ping'}))
                await asyncio.sleep(settings.PING_INTERVAL)
        except asyncio.CancelledError:
            logger.info(f"Ping task cancelled for user {self.user.id}")
        except Exception as e:
            logger.error(f"Ping error for user {self.user.id}: {e}", exc_info=True)

    @database_sync_to_async
    def verify_room_access(self):
         # Cache key based on user and room
        cache_key = f"chat_room_access:{self.user.id}:{self.room_id}"
        access = cache.get(cache_key)

        if access is not None:
            return access

        access = ChatRoom.objects.filter(
            id=self.room_id,
            doctor=self.user
        ).exists() or ChatRoom.objects.filter(
            id=self.room_id,
            client=self.user
        ).exists()

        cache.set(cache_key, access, settings.CHAT_ROOM_ACCESS_CACHE_TIMEOUT)
        return access

    @database_sync_to_async
    def save_message(self, message):
        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            message=message
        )
        message.delivered = True
        message.save()
        return message

    @database_sync_to_async
    def get_messages(self):
        return list(ChatMessage.objects.filter(room_id=self.room_id)
                    .select_related('sender')
                    .order_by('timestamp')[:settings.CHAT_MESSAGE_PAGE_SIZE])

    @database_sync_to_async
    def render_message(self, message):
        return render_to_string('chat/message.html', {'message': message, 'user': self.user})