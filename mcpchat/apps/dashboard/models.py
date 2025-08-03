from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
# Create your models here.
# models.py

class Dashboard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')
    name = models.CharField(max_length=255)
    datos_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name