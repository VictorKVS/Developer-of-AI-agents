from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="home"),
    path("chat/", views.chat, name="chat"),
    path("career/", views.career_track, name="career-track"),
    path("career/report/", views.download_career_report, name="career-report"),
]
