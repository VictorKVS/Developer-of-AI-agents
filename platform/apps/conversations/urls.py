from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_conversation, name="conversation-create"),
    path("<uuid:public_id>/", views.conversation_detail, name="conversation-detail"),
    path("<uuid:public_id>/chat/", views.chat, name="conversation-chat"),
]
