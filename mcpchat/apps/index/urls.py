from django.urls import path

from apps.index import views
app_name = 'index'
urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('recuperar_contraseña', views.recuperar_contraseña, name='recuperar_contraseña'),
]