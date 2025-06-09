from .models import Configuraciones

def configuraciones(request):
    return {'config': Configuraciones.load()}