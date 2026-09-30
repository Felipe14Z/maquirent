"""
arriendos/filters.py
Filtros django-filter para el catálogo de maquinaria.
Ejemplos: /api/maquinarias/?categoria=1&tarifa_min=10000&tarifa_max=50000&stock_bajo=true
"""
import django_filters
from django.db.models import F, Q
from .models import Equipo


class EquipoFilter(django_filters.FilterSet):
    tarifa_min = django_filters.NumberFilter(field_name='tarifa_diaria', lookup_expr='gte')
    tarifa_max = django_filters.NumberFilter(field_name='tarifa_diaria', lookup_expr='lte')
    stock_bajo = django_filters.BooleanFilter(method='filtrar_stock_bajo')

    class Meta:
        model = Equipo
        fields = ['categoria', 'marca']

    def filtrar_stock_bajo(self, queryset, name, value):
        bajo = Q(stock__lte=F('stock_minimo'))
        return queryset.filter(bajo) if value else queryset.exclude(bajo)
