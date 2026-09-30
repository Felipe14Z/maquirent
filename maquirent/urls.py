"""
maquirent/urls.py
Rutas raíz del proyecto.
 - /api/...  -> API REST (arriendos/api_urls.py)
 - /         -> páginas HTML (arriendos/urls.py)
 - handler404 -> página de error 404 controlada
"""
from django.conf import settings
from django.urls import path, include, re_path
from django.views.static import serve
from arriendos import paginas

urlpatterns = [
    path('api/', include('arriendos.api_urls')),
    path('', include('arriendos.urls')),
    # Sirve las imágenes subidas (/media/equipos/foto.jpg)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    # Ruta comodín (SIEMPRE al final): cualquier URL que no exista muestra nuestra página 404
    re_path(r'^.*$', paginas.no_encontrada),
]

# Página "esta página no existe" (se activa con DEBUG=False)
handler404 = 'arriendos.paginas.error_404'
