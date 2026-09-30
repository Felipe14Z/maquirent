"""
arriendos/management/commands/cargar_datos.py
Comando: python manage.py cargar_datos
Crea datos de prueba: categorías, equipos, un Ejecutivo (admin) y un Cliente.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from arriendos.models import Carro, Categoria, Equipo, Marca, Perfil

DATOS = {
    'Movimiento de Tierra': [
        ('Excavadora', 'Excavadora hidráulica sobre orugas 20 ton.', 180000, 500000, 4, 'Caterpillar'),
        ('Retroexcavadora', 'Retroexcavadora 4x4 con pala frontal.', 150000, 400000, 3, 'JCB'),
    ],
    'Trabajo en Altura': [
        ('Andamios', 'Andamio multidireccional certificado, módulo 2 m.', 12000, 30000, 25, 'Layher'),
        ('Plataforma elevadora tipo tijera', 'Plataforma eléctrica de 10 m de altura.', 65000, 150000, 2, 'Genie'),
    ],
    'Energía y Respaldo': [
        ('Generadores', 'Generador diésel 30 kVA insonorizado.', 35000, 80000, 6, 'Cummins'),
        ('Torres de iluminación portátiles', 'Torre móvil con 4 focos LED.', 28000, 60000, 1, 'Atlas Copco'),
    ],
    'Obras Civiles y Hormigón': [
        ('Hormigoneras', 'Hormigonera de 350 litros con motor eléctrico.', 22000, 50000, 5, 'Imer'),
        ('Vibradores de inmersión', 'Vibrador de hormigón de alta frecuencia.', 9000, 20000, 8, 'Wacker Neuson'),
    ],
}


class Command(BaseCommand):
    help = 'Carga datos de prueba de MaquiRent'

    def handle(self, *args, **kwargs):
        for cat_nombre, equipos in DATOS.items():
            cat, _ = Categoria.objects.get_or_create(nombre=cat_nombre)
            for nombre, desc, tarifa, garantia, stock, marca in equipos:
                mar, _ = Marca.objects.get_or_create(nombre=marca)
                Equipo.objects.update_or_create(nombre=nombre, defaults={
                    'categoria': cat, 'marca': mar, 'descripcion': desc, 'tarifa_diaria': tarifa,
                    'garantia': garantia, 'stock': stock, 'stock_minimo': 2})

        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_user('admin', 'admin@maquirent.cl', 'admin12345', is_staff=True)
            Perfil.objects.create(usuario=u, rol='ADMIN', empresa='MaquiRent')
        if not User.objects.filter(username='cliente').exists():
            u = User.objects.create_user('cliente', 'cliente@constructora.cl', 'cliente12345')
            Perfil.objects.create(usuario=u, rol='CLIENTE', empresa='Constructora Demo SpA')
            Carro.objects.create(usuario=u)

        self.stdout.write(self.style.SUCCESS(
            'Datos cargados. admin/admin12345  |  cliente/cliente12345'))
