from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope["user"]

        if not await self.verify_room_access():
            logger.warning(f"User {self.user.id} unauthorized to access room {self.room_id}")
            await self.close(code=4003)
            return

        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        self.ping_task = asyncio.create_task(self.send_pings())

        # Defer database operations slightly
        await asyncio.sleep(0)
        await self.send_existing_messages()

        await asyncio.sleep(0)
        await self.mark_messages_read()

    async def disconnect(self, close_code):
        logger.info(f"User {self.user.id} disconnected from room {self.room_id} with code {close_code}")
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
            message_type = data.get('type')  # Use .get to avoid KeyError

            if message_type == 'read_receipt':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.read_receipt',
                        'message_id': data['message_id'],
                        'reader': self.user.username
                    }
                )

            elif message_type == 'ping':
                await self.send(json.dumps({'type': 'pong'}))
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received from user {self.user.id}")
        except Exception as e:
            logger.error(f"Error processing message from user {self.user.id}: {e}", exc_info=True)

    async def handle_message(self, data):
        message = data['message'].strip()
        if not message:
            logger.warning(f"Empty message received from user {self.user.id}")
            return

        db_message = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.user.username,
                'timestamp': db_message.timestamp.isoformat(),
                'message_id': db_message.id
            }
        )

    async def handle_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_typing',
                'typing': data['typing'],
                'sender': self.user.username
            }
        )

    async def handle_read_receipt(self, data):
        await self.mark_message_read(data['message_id'])
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_read_receipt',
                'message_id': data['message_id'],
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
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info(f"Ping task cancelled for user {self.user.id}")
        except Exception as e:
            logger.error(f"Ping error for user {self.user.id}: {e}", exc_info=True)

    @database_sync_to_async
    def verify_room_access(self):
        return ChatRoom.objects.filter(
            id=self.room_id,
            doctor=self.user
        ) | ChatRoom.objects.filter(
            id=self.room_id,
            client=self.user
        ).exists()

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
                    .order_by('timestamp')[:50])


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