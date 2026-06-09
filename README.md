# E-Commerce Practicasa

Plataforma de comercio electrónico desarrollada con Django 6, Django REST Framework y PostgreSQL.

## Tecnologías

| Categoría | Tecnologías |
|-----------|-------------|
| Backend | Django 6.0.6, Django REST Framework, SimpleJWT |
| Base de datos | PostgreSQL 15 |
| Frontend | Django Templates, Bootstrap 5, SweetAlert2 |
| Documentación API | drf-spectacular (Swagger UI + OpenAPI 3.0) |
| Autenticación | Django Auth (sesiones web) + JWT (API REST) |
| Infraestructura | Docker, Gunicorn, WhiteNoise |

## Estructura del Proyecto

```
e-commerce-practicasa/
├── project/
│   ├── project/               # Configuración principal (settings, urls, wsgi, asgi)
│   ├── manage.py
│   ├── requirements.txt
│   ├── static/                # Archivos estáticos globales (css, img, js)
│   ├── templates/             # Templates globales (base, header, footer)
│   └── {app}/                 # Apps Django
│       ├── api/v1/            # API versionada (DRF)
│       ├── services.py        # Lógica de negocio
│       ├── forms.py           # Formularios HTML
│       ├── static/{app}/      # Estáticos propios de la app
│       └── templates/{app}/   # Templates propios de la app
├── .agents/                   # Skills para agente de IA
├── .env                       # Variables de entorno (no versionar)
├── .env.example               # Plantilla de variables de entorno
├── Dockerfile
├── docker-compose.yml
├── AGENTS.md                  # Convenciones del proyecto
└── README.md
```

## Requisitos Previos

- Python 3.12.3
- Docker y Docker Compose (recomendado)
- PostgreSQL 15 (si no se usa Docker)

## Instalación y Ejecución

### Con Docker (recomendado)

```bash
cp .env.example .env
# Editar .env con los valores correspondientes
docker-compose up -d
```

### Sin Docker

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r project\requirements.txt

cd project
python manage.py migrate
python manage.py runserver
```

## Variables de Entorno

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | Modo debug (True/False) |
| `DATABASE_URL` | URL completa de conexión a la DB (opcional) |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de la base de datos |
| `DB_PASSWORD` | Contraseña de la base de datos |
| `DB_HOST` | Host de la base de datos |
| `DB_PORT` | Puerto de la base de datos |
| `POSTGRES_DB` | Nombre de la DB para el contenedor PostgreSQL |
| `POSTGRES_USER` | Usuario para el contenedor PostgreSQL |
| `POSTGRES_PASSWORD` | Contraseña para el contenedor PostgreSQL |

## Módulos del Proyecto

### App Base
Template base, header/footer, páginas institucionales (Index, Contacto, Sucursales) y formulario de contacto con envío de emails.

### Usuarios
Registro, inicio de sesión, validación de cuenta, recuperación de contraseña y panel de administración de usuarios.

### Productos
Catálogo de productos con CRUD completo, categorías, imágenes y lógica de promociones.

### Carrito de Compras
Carrito de compras con soporte para sesión anónima y usuario autenticado, con endpoints JSON para operaciones asíncronas.

### Checkout y Ventas
Procesamiento de órdenes de compra, integración con MercadoPago, webhooks y comparación contra base de datos.

## Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Superusuario
python manage.py createsuperuser

# Archivos estáticos
python manage.py collectstatic

# Servidor de desarrollo
python manage.py runserver
```

## Documentación de la API

La documentación de la API REST se genera automáticamente con drf-spectacular y estará disponible en:

- Swagger UI: `/api/docs/`
- OpenAPI Schema: `/api/schema/`
