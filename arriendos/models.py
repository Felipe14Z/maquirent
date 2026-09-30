"""
arriendos/models.py
Modelos de datos de MaquiRent (PostgreSQL).

Relaciones:
  User 1-1 Perfil        -> rol del usuario (CHOICES)
  User 1-1 Carro         -> carro persistente en BD
  Carro 1-N ItemCarro    -> equipos agregados con fechas
  Categoria 1-N Equipo   -> catálogo de maquinaria
  Marca 1-N Equipo       -> marca del equipo
  User 1-N Contrato      -> historial de contratos (órdenes)
  Contrato 1-N DetalleContrato -> líneas con precios congelados
"""
from django.contrib.auth.models import User
from django.db import models


class Perfil(models.Model):
    """Extiende al usuario con un rol. Usa CHOICES explícito."""
    ROLES = [
        ('CLIENTE', 'Empresa Constructora'),
        ('ADMIN', 'Ejecutivo de Arriendos'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=10, choices=ROLES, default='CLIENTE')
    empresa = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'{self.usuario.username} ({self.rol})'


def obtener_rol(user):
    """Devuelve 'ADMIN' o 'CLIENTE'. Se usa para el claim 'rol' del JWT."""
    if user.is_staff:
        return 'ADMIN'
    perfil = getattr(user, 'perfil', None)
    return perfil.rol if perfil else 'CLIENTE'


class Categoria(models.Model):
    """Categoría de maquinaria (Movimiento de Tierra, Trabajo en Altura, etc.)."""
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    """Marca del fabricante (Caterpillar, JCB, Genie, etc.)."""
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    """Maquinaria arrendable con tarifa diaria, garantía fija y stock de flota."""
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='equipos')
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, null=True, blank=True,
                              related_name='equipos')
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    tarifa_diaria = models.PositiveIntegerField()
    garantia = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    # Umbral de alerta: si stock <= stock_minimo se considera "por agotarse"
    stock_minimo = models.PositiveIntegerField(default=2)
    # Foto del equipo (se guarda en la carpeta media/equipos/)
    imagen = models.ImageField(upload_to='equipos/', null=True, blank=True)

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def __str__(self):
        return self.nombre


class Carro(models.Model):
    """Carro de arriendo: relación 1 a 1 con el usuario, persistente en BD."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carro')
    actualizado = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(i.subtotal for i in self.items.all())


class ItemCarro(models.Model):
    """Un equipo dentro del carro con su periodo de arriendo."""
    carro = models.ForeignKey(Carro, on_delete=models.CASCADE, related_name='items')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        # Impide agregar el mismo equipo dos veces al mismo carro
        unique_together = ('carro', 'equipo')

    @property
    def dias(self):
        return max((self.fecha_fin - self.fecha_inicio).days, 1)

    @property
    def subtotal(self):
        """(tarifa diaria x días + garantía) x cantidad."""
        return (self.equipo.tarifa_diaria * self.dias + self.equipo.garantia) * self.cantidad


class Contrato(models.Model):
    """Orden histórica generada en el checkout. Estados con CHOICES."""
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ENTREGADO', 'Entregado'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contratos')
    estado = models.CharField(max_length=12, choices=ESTADOS, default='PENDIENTE')
    total = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']


class DetalleContrato(models.Model):
    """Línea del contrato. Guarda tarifa y garantía CONGELADAS al momento del checkout."""
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='detalles')
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveIntegerField()
    tarifa_diaria = models.PositiveIntegerField()
    garantia = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField()
