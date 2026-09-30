"""
arriendos/api_urls.py
Rutas de la API REST y de la documentación Swagger (/api/docs/).
"""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('maquinarias', views.EquipoViewSet, basename='maquinaria')
router.register('categorias', views.CategoriaViewSet, basename='categoria')
router.register('marcas', views.MarcaViewSet, basename='marca')

urlpatterns = [
    path('auth/login/', views.LoginView.as_view()),
    path('auth/refresh/', views.RefreshView.as_view()),
    path('auth/register/', views.RegistroView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/me/', views.MeView.as_view()),
    path('auth/change-password/', views.CambiarClaveView.as_view()),
    path('carro-arriendo/', views.CarroView.as_view()),
    path('carro-arriendo/<int:item_id>/', views.CarroItemView.as_view()),
    path('contratos/', views.ContratosAdminView.as_view()),
    path('contratos/checkout/', views.CheckoutView.as_view()),
    path('contratos/<int:pk>/pagar/', views.PagarView.as_view()),
    path('contratos/<int:pk>/estado/', views.ContratoEstadoView.as_view()),
    path('mis-contratos/', views.MisContratosView.as_view()),
    path('alertas-stock/', views.AlertasStockView.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('usuarios/', views.UsuariosView.as_view()),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema')),
] + router.urls
