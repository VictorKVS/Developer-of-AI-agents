from asgiref.sync import async_to_sync
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mongoose_core.llm import GigaChatProvider, LLMMessage
from .models import Conversation, Message
from .serializers import ChatRequestSerializer, ConversationSerializer, MessageSerializer


def build_provider() -> GigaChatProvider:
    if settings.LLM_PROVIDER != "gigachat":
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
    return GigaChatProvider(
        credentials=settings.GIGACHAT_CREDENTIALS,
        model=settings.GIGACHAT_MODEL,
        scope=settings.GIGACHAT_SCOPE,
        verify_ssl_certs=settings.GIGACHAT_VERIFY_SSL_CERTS,
        ca_bundle_file=settings.GIGACHAT_CA_BUNDLE_FILE,
    )


@api_view(["POST"])
def create_conversation(request):
    conversation = Conversation.objects.create()
    return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def conversation_detail(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    return Response(ConversationSerializer(conversation).data)


@api_view(["POST"])
def chat(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=serializer.validated_data["message"],
        sequence_number=conversation.messages.count() + 1,
    )
    history = [LLMMessage(role=item.role, content=item.content) for item in conversation.messages.all()]

    try:
        result = async_to_sync(build_provider().generate)(history)
    except (ValueError, RuntimeError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response({"detail": "LLM provider is temporarily unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=result.text,
        sequence_number=conversation.messages.count() + 1,
    )
    return Response({
        "conversation_id": conversation.public_id,
        "model": result.model,
        "user_message": MessageSerializer(user_message).data,
        "assistant_message": MessageSerializer(assistant_message).data,
    })
