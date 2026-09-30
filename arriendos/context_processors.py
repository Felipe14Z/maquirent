"""
arriendos/context_processors.py
Inyecta los datos del alumno (settings.ALUMNO) en TODAS las plantillas
para que el footer siempre muestre Nombre, Sección y Año.
"""
from django.conf import settings


def alumno(request):
    return {'ALUMNO': settings.ALUMNO}
