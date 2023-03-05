from django.urls import path
from src.views import chat, login, logout, home, reports, quiz, studyguides, feedback, help

urlpatterns = [
    path('', home.as_view, name='home'),
    path('', chat.as_view, name='chat'),
    path('', login.as_view, name='login'),
    path('', logout.as_view, name='logout'),
    path('', reports.as_view, name='reports'),
    path('', quiz.as_view, name='quiz'),
    path('', studyguides.as_view, name='studyguides'),
    path('', feedback.as_view, name='feedback'),
    path('', help.as_view, name='help'),
    path('get-chat-list/', chat.get_chat_list, name='get-chat-list')
       
    
    
]