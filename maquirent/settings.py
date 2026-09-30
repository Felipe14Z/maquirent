"""
maquirent/settings.py
Configuración global del proyecto MaquiRent.
Aquí se define: base de datos MySQL, apps instaladas, JWT, filtros,
Swagger (drf-spectacular) y los datos del alumno que se muestran en el footer.
NO se usa django.contrib.admin (requisito de la reunión: 100% templates).
"""
from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------
# Seguridad básica
# ---------------------------------------------------------------
SECRET_KEY = os.getenv('SECRET_KEY', 'maquirent-clave-de-desarrollo-cambiar')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------
# DATOS DEL ALUMNO (aparecen en el footer de todas las páginas)
# >>> EDITA ESTOS TRES VALORES <<<
# ---------------------------------------------------------------
ALUMNO = {
    'nombre': 'Luis Felipe Zapata',
    'seccion': 'AP-N4-C2(E-F)/D',
    'anio': '2026',
}

# ---------------------------------------------------------------
# Aplicaciones instaladas (sin admin)
# ---------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'arriendos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'maquirent.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'arriendos.context_processors.alumno',
    ]},
}]

WSGI_APPLICATION = 'maquirent.wsgi.application'

# ---------------------------------------------------------------
# Base de datos: MySQL (motor nativo, NO SQLite)
# ---------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'maquirent'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

# Archivos subidos por el ADMIN (fotos de los equipos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------
# Django REST Framework: JWT + django-filter + Swagger
# ---------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'arriendos.schema.EsquemaConTags',
}

# Tokens: access dura 30 min, refresh dura 1 día
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Documentación Swagger/OpenAPI (visible en /api/docs/)
SPECTACULAR_SETTINGS = {
    'TITLE': 'API MaquiRent - Arriendo de Maquinaria de Construcción',
    'DESCRIPTION': """
## Descripción General
API REST para el arriendo de maquinaria de construcción desarrollada con Django REST Framework y MySQL.

## Características principales
- 🔐 Autenticación JWT con claims de rol (CLIENTE / ADMIN)
- 🛒 Carro de arriendo persistente (relación 1:1 con usuario)
- 📦 Control transaccional de stock con `select_for_update`
- 🔍 Filtros avanzados con `django-filter`
- 📚 Documentación OpenAPI automática

## Autenticación
1. Hacer login en `POST /api/auth/login/`
2. Copiar el `access` token
3. Hacer clic en **Authorize** y pegar `Bearer <access>`
4. Los endpoints protegidos ya estarán disponibles

## Roles y permisos
- **Público**: lectura de catálogo
- **Cliente**: gestión de carro, checkout y pago de sus contratos
- **Administrador**: gestión de catálogo, inventario y estados de contratos
""",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVERS': [{'url': 'http://127.0.0.1:8000', 'description': 'Servidor de desarrollo'}],
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
    'TAGS': [
        {'name': 'Autenticación', 'description': 'Registro, login, logout y perfil.'},
        {'name': 'Catálogo - Categorías', 'description': 'CRUD de categorías.'},
        {'name': 'Catálogo - Marcas', 'description': 'CRUD de marcas.'},
        {'name': 'Catálogo - Maquinarias', 'description': 'CRUD de maquinaria con filtros.'},
        {'name': 'Carro de Arriendo', 'description': 'Carro persistente del cliente.'},
        {'name': 'Contratos', 'description': 'Checkout, pago y estados.'},
        {'name': 'Administración', 'description': 'Dashboard, alertas de stock y usuarios.'},
    ],
}
