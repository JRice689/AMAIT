from django.urls import path
from src.views import chat, login, logout

urlpatterns = [
    path('', chat.as_view, name='chat'),
    path('', login.as_view, name='login'),
    path('', logout.as_view, name='logout')
    
]