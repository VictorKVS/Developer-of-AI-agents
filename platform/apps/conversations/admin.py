from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "sequence_number", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("public_id", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("public_id",)
    inlines = (MessageInline,)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "sequence_number", "created_at")
    list_filter = ("role",)
    search_fields = ("content",)
