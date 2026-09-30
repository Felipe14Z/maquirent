"""
arriendos/management/commands/importar_productos.py
Comando: python manage.py importar_productos productos_nuevos.csv
Importa muchos equipos de una sola vez desde un archivo CSV.
Columnas: categoria, marca, nombre, descripcion, tarifa_diaria, garantia, stock, stock_minimo, imagen
 - Si el equipo (por nombre) ya existe, se actualiza; si no, se crea.
 - La categoría y la marca se crean si no existen.
 - 'imagen' es opcional: nombre de un archivo dentro de la carpeta imagenes_equipos/.
Acepta CSV separado por comas o por punto y coma (como lo guarda Excel en español).
"""
import csv
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from arriendos.models import Categoria, Equipo, Marca


class Command(BaseCommand):
    help = 'Importa equipos desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta del CSV (ej: productos_nuevos.csv)')

    def handle(self, *args, **opciones):
        ruta = Path(opciones['archivo'])
        if not ruta.is_absolute():
            ruta = Path(settings.BASE_DIR) / ruta
        if not ruta.exists():
            raise CommandError(f'No existe el archivo: {ruta}')

        carpeta_img = Path(settings.BASE_DIR) / 'imagenes_equipos'
        creados = actualizados = 0

        with ruta.open(encoding='utf-8-sig', newline='') as f:
            primera = f.readline()
            f.seek(0)
            delimitador = ';' if primera.count(';') > primera.count(',') else ','
            for n, fila in enumerate(csv.DictReader(f, delimiter=delimitador), start=2):
                try:
                    cat, _ = Categoria.objects.get_or_create(nombre=fila['categoria'].strip())
                    marca = None
                    if fila.get('marca', '').strip():
                        marca, _ = Marca.objects.get_or_create(nombre=fila['marca'].strip())
                    equipo, nuevo = Equipo.objects.update_or_create(
                        nombre=fila['nombre'].strip(),
                        defaults={
                            'categoria': cat, 'marca': marca,
                            'descripcion': fila.get('descripcion', '').strip(),
                            'tarifa_diaria': int(fila['tarifa_diaria']),
                            'garantia': int(fila['garantia']),
                            'stock': int(fila['stock']),
                            'stock_minimo': int(fila.get('stock_minimo') or 2),
                        })
                    archivo_img = (fila.get('imagen') or '').strip()
                    if archivo_img and (carpeta_img / archivo_img).exists():
                        with (carpeta_img / archivo_img).open('rb') as img:
                            equipo.imagen.save(archivo_img, File(img), save=True)
                    creados += nuevo
                    actualizados += not nuevo
                except (KeyError, ValueError) as e:
                    self.stdout.write(self.style.ERROR(f'Fila {n} con error ({e}): {fila}'))

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {creados} equipos creados, {actualizados} actualizados.'))
