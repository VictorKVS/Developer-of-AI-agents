import logging

from django.shortcuts import render

from .career_services import TARGET_ROLES, build_career_track, extract_resume_text


logger = logging.getLogger("apps.web")
WORKSPACE_RESUME_LIMIT = 24_000


def index(request):
    return render(request, "web/index.html")


def chat(request):
    workspace = request.session.get("workspace_context", {})
    return render(
        request,
        "web/chat.html",
        {
            "workspace_loaded": bool(workspace.get("resume_text")),
            "workspace_document_name": workspace.get("document_name", ""),
            "workspace_target_role": workspace.get("target_role_title", ""),
        },
    )


def _career_user_error(exc: Exception) -> str:
    text = str(exc)
    lowered = text.lower()

    if "чувствитель" in lowered or "без json-объекта" in lowered:
        return (
            "AI-провайдер не смог обработать этот вариант документа. "
            "Попробуйте нейтральную карьерную версию резюме или другой файл."
        )
    if "event loop" in lowered:
        return "Сервис анализа временно перезапускается. Повторите попытку через несколько секунд."
    if "пустой ответ" in lowered:
        return "AI-провайдер не вернул результат. Повторите попытку."
    if isinstance(exc, ValueError):
        return text[:280]
    return "Не удалось сформировать карьерный трек. Повторите попытку или выберите другой файл."


def career_track(request):
    context = {"target_roles": TARGET_ROLES}

    if request.method == "POST":
        uploaded_file = request.FILES.get("resume")
        target_role = request.POST.get("target_role", "")

        if not uploaded_file:
            context["error"] = "Выберите файл резюме."
            return render(request, "web/career_track.html", context)

        try:
            resume_text = extract_resume_text(uploaded_file)
            result, model_name = build_career_track(resume_text, target_role)
            result_data = result.model_dump()
            context["result"] = result
            context["model_name"] = model_name
            context["selected_role"] = target_role

            request.session["career_track_result"] = result_data
            request.session["workspace_context"] = {
                "document_name": uploaded_file.name,
                "resume_text": resume_text[:WORKSPACE_RESUME_LIMIT],
                "target_role": target_role,
                "target_role_title": TARGET_ROLES.get(target_role, target_role),
                "career_track": result_data,
                "model_name": model_name,
            }
            request.session.modified = True
        except Exception as exc:
            logger.exception(
                "Career track build failed file=%s role=%s",
                getattr(uploaded_file, "name", "unknown"),
                target_role,
            )
            context["error"] = _career_user_error(exc)

    return render(request, "web/career_track.html", context)
