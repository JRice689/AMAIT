from django.urls import path
from src.views import chat

urlpatterns = [
    path('', chat.as_view, name='chat')
]