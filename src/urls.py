from django.urls import path
from src.views import chat, login

urlpatterns = [
    path('', chat.as_view, name='chat'),
    path('', login.as_view, name='login')
    
]