"""
arriendos/services.py
Lógica de negocio transaccional (checkout, stock y cambios de estado).
Todo corre dentro de transaction.atomic: si algo falla, se revierte completo.

Reglas:
 - El stock NO se descuenta al agregar al carro.
 - El stock se descuenta SOLO al pasar a PAGADO (si no alcanza, se rechaza).
 - Si se CANCELA un contrato PAGADO, el stock se repone.
 - Al pasar a COMPLETADO (devolución del equipo) el stock se reincorpora.
"""
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from .models import Carro, Contrato, DetalleContrato, Equipo

# Transiciones permitidas entre estados
TRANSICIONES = {
    'PENDIENTE': ['PAGADO', 'CANCELADO'],
    'PAGADO': ['ENTREGADO', 'CANCELADO'],
    'ENTREGADO': ['COMPLETADO'],
    'COMPLETADO': [],
    'CANCELADO': [],
}


@transaction.atomic
def crear_contrato_desde_carro(usuario):
    """Checkout: convierte el carro en un Contrato PENDIENTE con precios congelados y vacía el carro."""
    carro, _ = Carro.objects.get_or_create(usuario=usuario)
    items = list(carro.items.select_related('equipo'))
    if not items:
        raise ValidationError({'detail': 'El carro está vacío.'})
    contrato = Contrato.objects.create(usuario=usuario, total=carro.total)
    for i in items:
        DetalleContrato.objects.create(
            contrato=contrato, equipo=i.equipo, cantidad=i.cantidad,
            fecha_inicio=i.fecha_inicio, fecha_fin=i.fecha_fin, dias=i.dias,
            tarifa_diaria=i.equipo.tarifa_diaria, garantia=i.equipo.garantia,
            subtotal=i.subtotal)
    carro.items.all().delete()
    return contrato


@transaction.atomic
def cambiar_estado(contrato_id, nuevo, usuario=None):
    """Cambia el estado de un contrato aplicando las reglas de stock."""
    filtro = {'pk': contrato_id}
    if usuario is not None:
        filtro['usuario'] = usuario
    contrato = Contrato.objects.select_for_update().get(**filtro)

    if nuevo not in TRANSICIONES[contrato.estado]:
        raise ValidationError({'detail': f'No se puede pasar de {contrato.estado} a {nuevo}.'})

    detalles = list(contrato.detalles.all())

    if nuevo == 'PAGADO':
        # Bloquea las filas de equipos y valida stock de TODOS antes de descontar
        for d in detalles:
            equipo = Equipo.objects.select_for_update().get(pk=d.equipo_id)
            if equipo.stock < d.cantidad:
                raise ValidationError(
                    {'detail': f'Stock insuficiente de {equipo.nombre}: quedan {equipo.stock}.'})
        for d in detalles:
            Equipo.objects.filter(pk=d.equipo_id).update(stock=F('stock') - d.cantidad)

    elif nuevo == 'CANCELADO' and contrato.estado == 'PAGADO':
        # Repone el stock que se había descontado al pagar
        for d in detalles:
            Equipo.objects.filter(pk=d.equipo_id).update(stock=F('stock') + d.cantidad)

    elif nuevo == 'COMPLETADO':
        # El equipo fue devuelto: vuelve a la flota disponible
        for d in detalles:
            Equipo.objects.filter(pk=d.equipo_id).update(stock=F('stock') + d.cantidad)

    contrato.estado = nuevo
    contrato.save()
    return contrato
