from asgiref.sync import async_to_sync
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.analysis.models import UserAnalysis
from apps.analysis.services import analyze_conversation
from apps.reports.services import generate_pdf_report
from mongoose_core.ports.llm import LLMMessage
from mongoose_core.providers.factory import build_llm_provider
from mongoose_core.services.dialogue import DialogueService

from .models import Conversation, Message
from .serializers import ConversationSerializer, DialogueRequestSerializer, MessageSerializer


@api_view(["POST"])
def create_conversation(request):
    conversation = Conversation.objects.create(
        status=Conversation.Status.ACTIVE,
        session_key=request.session.session_key or "",
    )
    return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def conversation_detail(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    return Response(ConversationSerializer(conversation).data)


@api_view(["POST"])
@transaction.atomic
def add_message(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    if conversation.status != Conversation.Status.ACTIVE:
        return Response({"detail": "Messages can only be added to an active conversation."}, status=status.HTTP_409_CONFLICT)
    serializer = MessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    message = serializer.save(conversation=conversation, sequence_number=conversation.messages.count() + 1)
    return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def chat(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    if conversation.status != Conversation.Status.ACTIVE:
        return Response({"detail": "The conversation is not active."}, status=status.HTTP_409_CONFLICT)

    request_serializer = DialogueRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    user_text = request_serializer.validated_data["message"]
    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=user_text,
        sequence_number=conversation.messages.count() + 1,
    )
    history = [LLMMessage(role=item.role, content=item.content) for item in conversation.messages.order_by("sequence_number")]

    try:
        result = async_to_sync(DialogueService(build_llm_provider()).reply)(history)
    except (ValueError, RuntimeError) as exc:
        return Response({"detail": str(exc), "user_message": MessageSerializer(user_message).data}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response({"detail": "The AI provider is temporarily unavailable.", "user_message": MessageSerializer(user_message).data}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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


@api_view(["POST"])
def complete_conversation(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    if conversation.status == Conversation.Status.COMPLETED and hasattr(conversation, "report"):
        analysis_profile = getattr(conversation.analysis, "prompt_version", "career_strategist") if hasattr(conversation, "analysis") else "career_strategist"
        return Response({
            "public_id": conversation.public_id,
            "status": conversation.status,
            "analysis_profile": analysis_profile,
            "download_url": f"/api/v1/conversations/{conversation.public_id}/report/",
        })
    if not conversation.messages.exists():
        return Response({"detail": "Диалог пуст. Сначала добавьте сообщения."}, status=status.HTTP_400_BAD_REQUEST)

    profile_key = request.data.get("analysis_profile", "career_strategist")
    conversation.status = Conversation.Status.ANALYZING
    conversation.save(update_fields=["status", "updated_at"])
    try:
        result, model_name, profile = analyze_conversation(conversation, profile_key)
        structured_data = result.profile.model_dump()
        structured_data.update({
            "disclaimer": result.disclaimer,
            "analysis_profile": profile.key,
            "analysis_profile_title": profile.title,
        })
        analysis, _ = UserAnalysis.objects.update_or_create(
            conversation=conversation,
            defaults={
                "structured_data": structured_data,
                "summary": result.summary,
                "recommendations": [item.model_dump() for item in result.recommendations],
                "confidence": result.confidence,
                "missing_information": result.missing_information,
                "model_name": model_name,
                "prompt_version": profile.key,
            },
        )
        generate_pdf_report(conversation, analysis)
        conversation.status = Conversation.Status.COMPLETED
        conversation.completed_at = timezone.now()
        conversation.save(update_fields=["status", "completed_at", "updated_at"])
    except ValueError as exc:
        conversation.status = Conversation.Status.ACTIVE
        conversation.save(update_fields=["status", "updated_at"])
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        conversation.status = Conversation.Status.FAILED
        conversation.save(update_fields=["status", "updated_at"])
        return Response({"detail": f"Не удалось сформировать анализ и PDF: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        "public_id": conversation.public_id,
        "status": conversation.status,
        "analysis_profile": profile.key,
        "analysis_profile_title": profile.title,
        "summary": analysis.summary,
        "download_url": f"/api/v1/conversations/{conversation.public_id}/report/",
    })


def download_report(request, public_id):
    conversation = get_object_or_404(Conversation, public_id=public_id)
    report = get_object_or_404(conversation.__class__.objects.select_related("report"), public_id=public_id).report
    return FileResponse(
        report.file.open("rb"),
        as_attachment=True,
        filename=f"mongoose-dialogue-{conversation.public_id}.pdf",
        content_type="application/pdf",
    )
