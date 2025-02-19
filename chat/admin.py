from django.contrib import admin
from .models import ChatRoom, ChatMessage

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'client', 'created_at')
    list_filter = ('created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'timestamp', 'read', 'delivered')
    list_filter = ('timestamp', 'read', 'delivered')