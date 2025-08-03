from django.urls import path
from apps.chat import views

app_name = 'chat'
urlpatterns = [
    path('', views.chat_view, name='chat_view'),
    path('/create/', views.chat_create, name='chat_create'),
    path('/edit/<int:id>', views.chat_edit, name='chat_edit'),
    path('/delete/<int:id>', views.chat_delete, name='chat_delete'),
    path('/message/', views.chat_message, name='chat_message'),
    path('/conversations/', views.chat_conversations, name='chat_conversations'),
    path('/<int:id>', views.chat_detalle, name='chat_detalle'),
    path('/chat_dark/', views.chat_dark, name='chat_dark'),
]