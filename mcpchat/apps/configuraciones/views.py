from django.shortcuts import render

# Create your views here.

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt  # Si no usás el token CSRF (no recomendado en producción)
def guardar_modo_oscuro(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        request.user.dark_mode = data.get('dark_mode', False)
        request.user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)
