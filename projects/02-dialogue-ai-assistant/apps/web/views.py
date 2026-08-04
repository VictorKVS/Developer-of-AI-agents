from django.shortcuts import render


def index(request):
    return render(request, "web/index.html")


def chat(request):
    return render(request, "web/chat.html")
