"""CCAIT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from src.views import chat, login, logout, reports, quiz, studyguides, feedback, help

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('src.urls')),
    path('', chat.as_view),
    path('chat/', chat.as_view),
    path('login/', login.as_view),
    path('logout/', logout.as_view),
    path('reports/', reports.as_view),
    path('quiz/', quiz.as_view),
    path('studyguides/', studyguides.as_view),
    path('feedback/', feedback.as_view),
    path('help/', help.as_view),
    path('get-chat-list/', chat.get_chat_list, name='get-chat-list')
]
