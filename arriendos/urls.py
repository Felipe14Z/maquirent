"""
arriendos/urls.py
Rutas de las PÁGINAS HTML (landing, catálogo, carro, contratos, panel admin, login, registro).
Cada página carga sus datos consumiendo la API con JavaScript (fetch + JWT).
"""
from django.urls import path
from django.views.generic import TemplateView

T = TemplateView.as_view

urlpatterns = [
    path('', T(template_name='arriendos/landing.html'), name='inicio'),
    path('catalogo/', T(template_name='arriendos/catalogo.html'), name='catalogo'),
    path('carro/', T(template_name='arriendos/carro.html'), name='carro'),
    path('mis-contratos/', T(template_name='arriendos/contratos.html'), name='mis_contratos'),
    path('panel/', T(template_name='arriendos/panel.html'), name='panel'),
    path('login/', T(template_name='arriendos/login.html'), name='login'),
    path('registro/', T(template_name='arriendos/registro.html'), name='registro'),
]
