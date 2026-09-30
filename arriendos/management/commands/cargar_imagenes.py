"""
arriendos/management/commands/cargar_imagenes.py
Comando: python manage.py cargar_imagenes
Asigna las fotos de la carpeta 'imagenes_equipos/' (en la raíz del proyecto) a cada equipo,
comparando el nombre del archivo con el nombre del equipo. Ejemplos de nombres de archivo:
  excavadora.jpg, retroexcavadora.png, andamios.jpg, plataforma.jpg,
  generadores.jpg, torres.jpg, hormigoneras.jpg, vibradores.jpg
Opción --forzar: reemplaza también las imágenes que ya estaban asignadas.
"""
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from arriendos.models import Equipo

EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp'}


def normalizar(texto):
    """Minúsculas, sin tildes y con guion bajo en vez de espacios."""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')


class Command(BaseCommand):
    help = 'Carga las imágenes de la carpeta imagenes_equipos/ en los equipos'

    def add_arguments(self, parser):
        parser.add_argument('--forzar', action='store_true', help='Reemplaza imágenes existentes')

    def handle(self, *args, **opciones):
        carpeta = Path(settings.BASE_DIR) / 'imagenes_equipos'
        if not carpeta.exists():
            carpeta.mkdir()
            self.stdout.write(self.style.WARNING(
                'Creé la carpeta imagenes_equipos/. Copia ahí las fotos y ejecuta el comando de nuevo.'))
            return

        archivos = {normalizar(f.stem): f for f in carpeta.iterdir()
                    if f.suffix.lower() in EXTENSIONES}
        for equipo in Equipo.objects.all():
            if equipo.imagen and not opciones['forzar']:
                self.stdout.write(f'- {equipo.nombre}: ya tiene imagen (omitido)')
                continue
            nombre = normalizar(equipo.nombre)
            # Coincide con el nombre completo o con la primera palabra (ej. "plataforma")
            archivo = archivos.get(nombre) or archivos.get(nombre.split('_')[0])
            if not archivo:
                self.stdout.write(self.style.WARNING(f'- {equipo.nombre}: no encontré imagen'))
                continue
            with archivo.open('rb') as f:
                equipo.imagen.save(archivo.name, File(f), save=True)
            self.stdout.write(self.style.SUCCESS(f'- {equipo.nombre}: cargada ({archivo.name})'))
