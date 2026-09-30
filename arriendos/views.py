"""
arriendos/views.py
Endpoints de la API REST.
Matriz de permisos:
  PÚBLICO : GET catálogo (maquinarias, categorías, marcas)
  CLIENTE : carro, checkout, pagar, mis-contratos
  ADMIN   : CRUD catálogo, cambio de estado, alertas, dashboard, usuarios
  AUTH    : login, refresh, register, logout, me, change-password
"""
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import F
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .filters import EquipoFilter
from .models import (Carro, Categoria, Contrato, Equipo, ItemCarro, Marca, obtener_rol)
from .permissions import EsCliente, EsEjecutivo
from .serializers import (CambiarClaveSerializer, CarroSerializer, CategoriaSerializer,
                          ContratoSerializer, EquipoSerializer, EstadoSerializer,
                          ItemCarroSerializer, LogoutSerializer, MarcaSerializer,
                          RegistroSerializer, TokenConRolSerializer, UsuarioSerializer)
from .services import cambiar_estado, crear_contrato_desde_carro


def _crud(singular, plural):
    """Frases de Swagger para un CRUD completo (lectura pública, escritura solo Admin)."""
    return {
        'list': f'Listar {plural}',
        'create': f'Crear {singular} (solo Admin)',
        'retrieve': f'Detalle de {singular}',
        'update': f'Actualizar {singular} (solo Admin)',
        'partial_update': f'Actualizar parcialmente {singular} (solo Admin)',
        'destroy': f'Eliminar {singular} (solo Admin)',
    }


# ---------------- Autenticación ----------------
class LoginView(TokenObtainPairView):
    """Login JWT: devuelve access, refresh, rol y username."""
    serializer_class = TokenConRolSerializer
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'post': 'Iniciar sesión (obtener tokens JWT)'}


class RegistroView(generics.CreateAPIView):
    """Registrar un nuevo cliente (empresa constructora)."""
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'post': 'Registrar un nuevo cliente'}


class LogoutView(APIView):
    """Cerrar sesión: invalida el refresh token (blacklist). El carro NO se pierde."""
    permission_classes = [IsAuthenticated]
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'post': 'Cerrar sesión (logout)'}

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        ser = LogoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            RefreshToken(ser.validated_data['refresh']).blacklist()
        except Exception:
            return Response({'detail': 'Token inválido.'}, status=400)
        return Response(status=205)


class MeView(APIView):
    """Perfil del usuario autenticado."""
    permission_classes = [IsAuthenticated]
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'get': 'Obtener perfil del usuario autenticado'}

    @extend_schema(responses=UsuarioSerializer)
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class CambiarClaveView(APIView):
    """Cambiar contraseña (PUT o PATCH)."""
    permission_classes = [IsAuthenticated]
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'put': 'Cambiar contraseña', 'patch': 'Cambiar contraseña'}

    @extend_schema(request=CambiarClaveSerializer, responses={200: None})
    def put(self, request):
        ser = CambiarClaveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not request.user.check_password(ser.validated_data['old_password']):
            return Response({'detail': 'La contraseña actual es incorrecta.'}, status=400)
        request.user.set_password(ser.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Contraseña actualizada.'})

    @extend_schema(request=CambiarClaveSerializer, responses={200: None})
    def patch(self, request):
        return self.put(request)


class RefreshView(TokenRefreshView):
    """Renueva el access token usando el refresh token."""
    swagger_tag = 'Autenticación'
    swagger_resumenes = {'post': 'Renovar access token'}


# ---------------- Catálogo (lectura pública, escritura ADMIN) ----------------
class LecturaPublicaEscrituraAdmin:
    """Mixin: list/retrieve públicos; crear, editar y eliminar solo ADMIN."""
    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [EsEjecutivo()]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({'detail': 'No se puede eliminar: tiene registros asociados.'},
                            status=status.HTTP_400_BAD_REQUEST)


class CategoriaViewSet(LecturaPublicaEscrituraAdmin, viewsets.ModelViewSet):
    """CRUD de categorías."""
    queryset = Categoria.objects.all().order_by('nombre')
    serializer_class = CategoriaSerializer
    swagger_tag = 'Catálogo - Categorías'
    swagger_resumenes = _crud('categoría', 'categorías')


class MarcaViewSet(LecturaPublicaEscrituraAdmin, viewsets.ModelViewSet):
    """CRUD de marcas."""
    queryset = Marca.objects.all().order_by('nombre')
    serializer_class = MarcaSerializer
    swagger_tag = 'Catálogo - Marcas'
    swagger_resumenes = _crud('marca', 'marcas')


class EquipoViewSet(LecturaPublicaEscrituraAdmin, viewsets.ModelViewSet):
    """CRUD de maquinaria con filtros (categoría, marca, tarifa, stock bajo) y búsqueda."""
    queryset = Equipo.objects.select_related('categoria', 'marca').all().order_by('categoria', 'nombre')
    serializer_class = EquipoSerializer
    filterset_class = EquipoFilter
    search_fields = ['nombre', 'descripcion', 'marca__nombre']
    ordering_fields = ['tarifa_diaria', 'stock', 'nombre']
    swagger_tag = 'Catálogo - Maquinarias'
    swagger_resumenes = _crud('maquinaria', 'maquinarias (con filtros)')


# ---------------- Administración ----------------
class AlertasStockView(APIView):
    """Equipos cuyo stock <= stock_minimo (por agotarse). Solo ADMIN."""
    permission_classes = [EsEjecutivo]
    swagger_tag = 'Administración'
    swagger_resumenes = {'get': 'Equipos con stock por agotarse (solo Admin)'}

    @extend_schema(responses=EquipoSerializer(many=True))
    def get(self, request):
        equipos = Equipo.objects.filter(stock__lte=F('stock_minimo')).order_by('stock')
        return Response(EquipoSerializer(equipos, many=True).data)


class DashboardView(APIView):
    """Totales y estado del sistema para el dashboard del ADMIN."""
    permission_classes = [EsEjecutivo]
    swagger_tag = 'Administración'
    swagger_resumenes = {'get': 'Totales y estado del sistema (solo Admin)'}

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        try:
            with connection.cursor() as c:
                c.execute('SELECT 1')
            db_ok = True
        except Exception:
            db_ok = False
        return Response({
            'equipos': Equipo.objects.count(),
            'categorias': Categoria.objects.count(),
            'marcas': Marca.objects.count(),
            'contratos': Contrato.objects.count(),
            'pendientes': Contrato.objects.filter(estado='PENDIENTE').count(),
            'alertas': Equipo.objects.filter(stock__lte=F('stock_minimo')).count(),
            'motor': connection.vendor, 'db_ok': db_ok, 'api': True, 'jwt': True,
        })


class UsuariosView(generics.ListAPIView):
    """Listado de usuarios registrados (solo ADMIN)."""
    serializer_class = UsuarioSerializer
    permission_classes = [EsEjecutivo]
    queryset = User.objects.select_related('perfil').order_by('id')
    swagger_tag = 'Administración'
    swagger_resumenes = {'get': 'Listar usuarios (solo Admin)'}


# ---------------- Carro persistente ----------------
class CarroView(APIView):
    """GET ver carro | POST agregar equipo | DELETE vaciar. Solo CLIENTE."""
    permission_classes = [EsCliente]
    swagger_tag = 'Carro de Arriendo'
    swagger_resumenes = {'get': 'Ver mi carro', 'post': 'Agregar equipo al carro', 'delete': 'Vaciar el carro'}

    def _carro(self, request):
        carro, _ = Carro.objects.get_or_create(usuario=request.user)
        return carro

    @extend_schema(responses=CarroSerializer)
    def get(self, request):
        return Response(CarroSerializer(self._carro(request)).data)

    @extend_schema(request=ItemCarroSerializer, responses=CarroSerializer)
    def post(self, request):
        carro = self._carro(request)
        ser = ItemCarroSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if ItemCarro.objects.filter(carro=carro, equipo=ser.validated_data['equipo']).exists():
            return Response({'detail': 'Este equipo ya está en tu carro.'}, status=400)
        ser.save(carro=carro)
        return Response(CarroSerializer(carro).data, status=201)

    @extend_schema(responses={204: None})
    def delete(self, request):
        self._carro(request).items.all().delete()
        return Response(status=204)


class CarroItemView(APIView):
    """PATCH /api/carro-arriendo/<id>/ modifica cantidad o fechas | DELETE quita el ítem."""
    permission_classes = [EsCliente]
    swagger_tag = 'Carro de Arriendo'
    swagger_resumenes = {'patch': 'Modificar cantidad o fechas de un ítem', 'delete': 'Quitar un ítem del carro'}

    @extend_schema(request=ItemCarroSerializer, responses=CarroSerializer)
    def patch(self, request, item_id):
        item = get_object_or_404(ItemCarro, pk=item_id, carro__usuario=request.user)
        # Parte de los valores actuales y sobrescribe solo los campos enviados
        datos = {'equipo': item.equipo_id, 'cantidad': item.cantidad,
                 'fecha_inicio': item.fecha_inicio, 'fecha_fin': item.fecha_fin}
        for campo in ('cantidad', 'fecha_inicio', 'fecha_fin'):
            if campo in request.data:
                datos[campo] = request.data[campo]
        ser = ItemCarroSerializer(item, data=datos)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(CarroSerializer(item.carro).data)

    @extend_schema(responses={204: None})
    def delete(self, request, item_id):
        item = get_object_or_404(ItemCarro, pk=item_id, carro__usuario=request.user)
        item.delete()
        return Response(status=204)


# ---------------- Contratos ----------------
class CheckoutView(APIView):
    """POST: convierte el carro en un Contrato PENDIENTE (no descuenta stock)."""
    permission_classes = [EsCliente]
    swagger_tag = 'Contratos'
    swagger_resumenes = {'post': 'Confirmar contrato (checkout)'}

    @extend_schema(request=None, responses=ContratoSerializer)
    def post(self, request):
        contrato = crear_contrato_desde_carro(request.user)
        return Response(ContratoSerializer(contrato).data, status=201)


class PagarView(APIView):
    """POST: registra el pago -> PAGADO y descuenta stock de forma atómica."""
    permission_classes = [EsCliente]
    swagger_tag = 'Contratos'
    swagger_resumenes = {'post': 'Registrar pago (descuenta stock)'}

    @extend_schema(request=None, responses=ContratoSerializer)
    def post(self, request, pk):
        try:
            contrato = cambiar_estado(pk, 'PAGADO', usuario=request.user)
        except Contrato.DoesNotExist:
            raise Http404
        return Response(ContratoSerializer(contrato).data)


class MisContratosView(generics.ListAPIView):
    """Contratos del cliente autenticado."""
    serializer_class = ContratoSerializer
    permission_classes = [EsCliente]
    swagger_tag = 'Contratos'
    swagger_resumenes = {'get': 'Listar mis contratos'}

    def get_queryset(self):
        return Contrato.objects.filter(usuario=self.request.user).prefetch_related('detalles__equipo')


class ContratosAdminView(generics.ListAPIView):
    """Todos los contratos (solo ADMIN)."""
    serializer_class = ContratoSerializer
    permission_classes = [EsEjecutivo]
    queryset = Contrato.objects.prefetch_related('detalles__equipo').select_related('usuario')
    swagger_tag = 'Contratos'
    swagger_resumenes = {'get': 'Listar todos los contratos (solo Admin)'}


class ContratoEstadoView(APIView):
    """PATCH: el ADMIN cambia el estado (ENTREGADO, COMPLETADO, CANCELADO...)."""
    permission_classes = [EsEjecutivo]
    swagger_tag = 'Contratos'
    swagger_resumenes = {'patch': 'Cambiar estado del contrato (solo Admin)'}

    @extend_schema(request=EstadoSerializer, responses=ContratoSerializer)
    def patch(self, request, pk):
        ser = EstadoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            contrato = cambiar_estado(pk, ser.validated_data['estado'])
        except Contrato.DoesNotExist:
            raise Http404
        return Response(ContratoSerializer(contrato).data)
