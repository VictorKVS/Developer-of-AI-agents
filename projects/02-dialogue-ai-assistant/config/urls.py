from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "dialogue-ai-assistant"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/conversations/", include("apps.conversations.urls")),
    path("", include("apps.web.urls")),
]
