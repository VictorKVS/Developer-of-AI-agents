from asgiref.sync import async_to_sync
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider
from mongoose_core.services.dialogue import DialogueService

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    DialogueRequestSerializer,
    MessageSerializer,
)


@api_view(["POST"])
def create_conversation(request):
    conversation = Conversation.objects.create(
        status=Conversation.Status.ACTIVE,
        session_key=request.session.session_key or "",
    )
    return Response(
        ConversationSerializer(conversation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def conversation_detail(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    return Response(ConversationSerializer(conversation).data)


@api_view(["POST"])
@transaction.atomic
def add_message(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    if conversation.status != Conversation.Status.ACTIVE:
        return Response(
            {"detail": "Messages can only be added to an active conversation."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = MessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    next_sequence = conversation.messages.count() + 1
    message = serializer.save(
        conversation=conversation,
        sequence_number=next_sequence,
    )
    return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def chat(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    if conversation.status != Conversation.Status.ACTIVE:
        return Response(
            {"detail": "The conversation is not active."},
            status=status.HTTP_409_CONFLICT,
        )

    request_serializer = DialogueRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    user_text = request_serializer.validated_data["message"]

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=user_text,
        sequence_number=conversation.messages.count() + 1,
    )

    history = [
        LLMMessage(role=item.role, content=item.content)
        for item in conversation.messages.order_by("sequence_number")
    ]

    try:
        provider = build_llm_provider()
        result = async_to_sync(DialogueService(provider).reply)(history)
    except (ValueError, RuntimeError) as exc:
        return Response(
            {
                "detail": str(exc),
                "user_message": MessageSerializer(user_message).data,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception:
        return Response(
            {
                "detail": "The AI provider is temporarily unavailable.",
                "user_message": MessageSerializer(user_message).data,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=result.text,
        sequence_number=conversation.messages.count() + 1,
    )

    return Response(
        {
            "conversation_id": conversation.public_id,
            "model": result.model,
            "user_message": MessageSerializer(user_message).data,
            "assistant_message": MessageSerializer(assistant_message).data,
        }
    )


@api_view(["POST"])
def complete_conversation(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)

    if conversation.status in {
        Conversation.Status.ANALYZING,
        Conversation.Status.COMPLETED,
    }:
        return Response(ConversationSerializer(conversation).data)

    conversation.status = Conversation.Status.ANALYZING
    conversation.save(update_fields=["status", "updated_at"])

    return Response(
        {
            "public_id": conversation.public_id,
            "status": conversation.status,
            "detail": "Conversation accepted for analysis. AI and PDF services are implemented next.",
        },
        status=status.HTTP_202_ACCEPTED,
    )
