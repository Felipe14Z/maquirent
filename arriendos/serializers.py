"""
arriendos/serializers.py
Convierten modelos <-> JSON y validan datos de entrada.
Incluye el serializer del token JWT con el claim de rol.
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (Marca, Categoria, Equipo, Carro, ItemCarro, Contrato,
                     DetalleContrato, Perfil, obtener_rol)


class TokenConRolSerializer(TokenObtainPairSerializer):
    """Agrega 'rol' y 'username' al payload del JWT y a la respuesta del login."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = obtener_rol(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['rol'] = obtener_rol(self.user)
        data['username'] = self.user.username
        return data


class RegistroSerializer(serializers.ModelSerializer):
    """Registro público: crea usuario CLIENTE, su Perfil y su Carro."""
    password = serializers.CharField(write_only=True, min_length=6)
    empresa = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'empresa']

    def create(self, validated_data):
        empresa = validated_data.pop('empresa', '')
        user = User.objects.create_user(**validated_data)
        Perfil.objects.create(usuario=user, rol='CLIENTE', empresa=empresa)
        Carro.objects.create(usuario=user)
        return user


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'descripcion']


class CambiarClaveSerializer(serializers.Serializer):
    """Datos para cambiar contraseña."""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


class LogoutSerializer(serializers.Serializer):
    """Refresh token que se invalida (blacklist) al cerrar sesión."""
    refresh = serializers.CharField()


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'rol', 'empresa', 'date_joined']

    def get_rol(self, obj):
        return obtener_rol(obj)

    def get_empresa(self, obj):
        p = getattr(obj, 'perfil', None)
        return p.empresa if p else ''


class EquipoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    marca_nombre = serializers.SerializerMethodField()
    stock_bajo = serializers.BooleanField(read_only=True)

    def get_marca_nombre(self, obj):
        return obj.marca.nombre if obj.marca else ''

    class Meta:
        model = Equipo
        fields = ['id', 'nombre', 'descripcion', 'categoria', 'categoria_nombre',
                  'marca', 'marca_nombre',
                  'tarifa_diaria', 'garantia', 'stock', 'stock_minimo', 'stock_bajo', 'imagen']

    def validate_tarifa_diaria(self, value):
        if value <= 0:
            raise serializers.ValidationError('La tarifa debe ser mayor a 0.')
        return value


class ItemCarroSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    tarifa_diaria = serializers.IntegerField(source='equipo.tarifa_diaria', read_only=True)
    garantia = serializers.IntegerField(source='equipo.garantia', read_only=True)
    dias = serializers.IntegerField(read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = ItemCarro
        fields = ['id', 'equipo', 'equipo_nombre', 'cantidad', 'fecha_inicio', 'fecha_fin',
                  'tarifa_diaria', 'garantia', 'dias', 'subtotal']

    def validate(self, data):
        if data['fecha_fin'] < data['fecha_inicio']:
            raise serializers.ValidationError('La fecha de fin no puede ser anterior al inicio.')
        if data['cantidad'] < 1:
            raise serializers.ValidationError('La cantidad debe ser al menos 1.')
        return data


class CarroSerializer(serializers.ModelSerializer):
    items = ItemCarroSerializer(many=True, read_only=True)
    total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Carro
        fields = ['id', 'items', 'total']


class DetalleContratoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)

    class Meta:
        model = DetalleContrato
        fields = ['id', 'equipo', 'equipo_nombre', 'cantidad', 'fecha_inicio', 'fecha_fin',
                  'dias', 'tarifa_diaria', 'garantia', 'subtotal']


class ContratoSerializer(serializers.ModelSerializer):
    detalles = DetalleContratoSerializer(many=True, read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Contrato
        fields = ['id', 'usuario_nombre', 'estado', 'total', 'creado', 'detalles']


class EstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Contrato.ESTADOS)
