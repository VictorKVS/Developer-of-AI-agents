from django.shortcuts import render

from .career_services import TARGET_ROLES, build_career_track, extract_resume_text


def index(request):
    return render(request, "web/index.html")


def chat(request):
    return render(request, "web/chat.html")


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
            context["result"] = result
            context["model_name"] = model_name
            context["selected_role"] = target_role
            request.session["career_track_result"] = result.model_dump()
        except Exception as exc:
            context["error"] = f"Не удалось построить трек: {exc}"

    return render(request, "web/career_track.html", context)
