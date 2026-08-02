from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "sequence_number", "created_at"]
        read_only_fields = ["id", "sequence_number", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["public_id", "status", "created_at", "messages"]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)
