from django.urls import path
from apps.chat import views

app_name = 'chat'
urlpatterns = [
    path('', views.chat_view, name='chats'),
    path('/message/', views.chat_message, name='chat_message'),
]