"""
arriendos/permissions.py
Permisos personalizados por ROL. El rol se lee del claim 'rol' dentro del token JWT
(request.auth); si no existe, se consulta al usuario.
"""
from rest_framework.permissions import BasePermission
from .models import obtener_rol


def _rol(request):
    token = request.auth
    if token is not None and hasattr(token, 'get') and token.get('rol'):
        return token.get('rol')
    return obtener_rol(request.user)


class EsEjecutivo(BasePermission):
    """Solo Ejecutivo de Arriendos (ADMIN): gestión de inventario y estados."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _rol(request) == 'ADMIN')


class EsCliente(BasePermission):
    """Solo Empresa Constructora (CLIENTE): carro y contratos propios."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _rol(request) == 'CLIENTE')
