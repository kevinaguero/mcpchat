from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.dashboard_view, name='dashboard_view'),
    path('/<int:id>', views.dashboard_detalle, name='dashboard_detalle'),
]