import json

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


def _build_workspace_message(request) -> LLMMessage | None:
    workspace = request.session.get("workspace_context", {})
    resume_text = workspace.get("resume_text", "").strip()
    career_track = workspace.get("career_track") or {}
    if not resume_text and not career_track:
        return None

    context_payload = {
        "document_name": workspace.get("document_name", ""),
        "target_role": workspace.get("target_role_title", ""),
        "career_track": career_track,
    }
    context_json = json.dumps(context_payload, ensure_ascii=False, indent=2)
    content = (
        "Ты работаешь внутри MONGOOSE AI Workspace. Пользователь ранее загрузил резюме, "
        "и платформа уже выполнила профессиональный анализ. Используй приведённые ниже данные "
        "как общий контекст текущей сессии. Отвечай только на основании резюме, результатов анализа "
        "и сообщений диалога. Не утверждай факты, которых в этих данных нет. При запросах об ИБ "
        "сопоставляй опыт кандидата с требованиями позиции и явно разделяй сильные стороны, пробелы, "
        "риски и следующие шаги.\n\n"
        f"СТРУКТУРИРОВАННЫЙ АНАЛИЗ WORKSPACE:\n{context_json}\n\n"
        f"ТЕКСТ ЗАГРУЖЕННОГО РЕЗЮМЕ:\n{resume_text}"
    )
    return LLMMessage(role="system", content=content)


@api_view(["POST"])
def create_conversation(request):
    if not request.session.session_key:
        request.session.create()
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

    history = []
    workspace_message = _build_workspace_message(request)
    if workspace_message:
        history.append(workspace_message)
    history.extend(
        LLMMessage(role=item.role, content=item.content)
        for item in conversation.messages.order_by("sequence_number")
    )

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
        "workspace_loaded": workspace_message is not None,
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
