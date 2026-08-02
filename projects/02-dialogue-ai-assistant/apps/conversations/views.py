from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


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
