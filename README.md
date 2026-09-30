# MaquiRent - Arriendo de Maquinaria de Construcción

EVA-2 Desarrollo Backend (Caso 6). Django REST Framework + MySQL + JWT.

Alumno: TU NOMBRE COMPLETO | Sección: TU SECCIÓN | Año: 2026

## Instalación
1. Encender MySQL (XAMPP) y crear la base de datos `maquirent` (utf8mb4_unicode_ci).
2. Crear y activar el entorno virtual:
   python -m venv venv
   venv\Scripts\activate
3. Instalar dependencias:
   pip install -r requirements.txt
4. Crear tablas y cargar datos de prueba:
   python manage.py migrate
   python manage.py cargar_datos
   python manage.py cargar_imagenes
5. Ejecutar:
   python manage.py runserver

## Usuarios de prueba
- Administrador: admin / admin12345
- Cliente: cliente / cliente12345

## Rutas principales
- Sitio: http://127.0.0.1:8000/
- Documentación API (Swagger): http://127.0.0.1:8000/api/docs/

## Importar más productos
python manage.py importar_productos productos_nuevos.csv