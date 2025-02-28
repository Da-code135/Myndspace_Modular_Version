import json
import logging
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.utils.html import escape  # For XSS protection
from django.core.cache import cache  # For caching
from .models import ChatRoom, ChatMessage

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.user = None
        self.room_group_name = None
        self.access_verified = False # flag to track verification

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope["user"]
        self.room_group_name = f'chat_{self.room_id}'

        # Verify room access and cache the result
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

        # Defer database operations slightly
        await asyncio.sleep(0)
        await self.send_existing_messages()

        await asyncio.sleep(0)
        await self.mark_messages_read()

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
        if not self.access_verified:
            logger.warning(f"Unverified user {self.user.id} attempted to send a message")
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')  # Use .get to avoid KeyError

            if message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'ping':
                await self.send(json.dumps({'type': 'pong'}))
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'message':
                await self.handle_message(data)
            else:
                logger.warning(f"Unknown message type: {message_type} from user {self.user.id}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received from user {self.user.id}")
        except Exception as e:
            logger.error(f"Error processing message from user {self.user.id}: {e}", exc_info=True)

    async def handle_message(self, data):
        message = data.get('message', '').strip() # Use .get and provide a default
        if not message:
            logger.warning(f"Empty message received from user {self.user.id}")
            return

        # Sanitize the message to prevent XSS
        sanitized_message = escape(message)

        db_message = await self.save_message(sanitized_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': sanitized_message,
                'sender': self.user.username,
                'timestamp': db_message.timestamp.isoformat(),
                'message_id': db_message.id
            }
        )

    async def handle_typing(self, data):
        typing = data.get('typing', False) # Use .get and provide a default
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
            'message': event['message'],
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
                await asyncio.sleep(settings.PING_INTERVAL)  # Use setting for interval
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

        cache.set(cache_key, access, settings.CHAT_ROOM_ACCESS_CACHE_TIMEOUT) # Use setting for timeout
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
                    .order_by('timestamp')[:settings.CHAT_MESSAGE_PAGE_SIZE]) # Use setting for page size

    @database_sync_to_async
    async def send_existing_messages(self):
        messages = await self.get_messages()
        for message in messages:
            await self.send(json.dumps({
                'type': 'message',
                'message': message.message,
                'sender': message.sender.username,
                'timestamp': message.timestamp.isoformat(),
                'message_id': message.id
            }))

    @database_sync_to_async
    def mark_messages_read(self):
        ChatMessage.objects.filter(
            room_id=self.room_id,
            read=False
        ).exclude(sender=self.user).update(read=True)

    @database_sync_to_async
    def mark_message_read(self, message_id):
        ChatMessage.objects.filter(id=message_id).update(read=True)