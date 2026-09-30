"""
arriendos/paginas.py
Vistas que devuelven páginas HTML.
Aquí vive el manejador del error 404 controlado.
"""
from django.shortcuts import render


def error_404(request, exception):
    """Muestra la plantilla 404.html con código de estado 404."""
    return render(request, '404.html', status=404)


def no_encontrada(request, *args, **kwargs):
    """Se usa como ruta comodín: cualquier URL inexistente muestra 404.html (incluso con DEBUG=True)."""
    return render(request, '404.html', status=404)
