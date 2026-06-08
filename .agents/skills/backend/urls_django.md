# URLs Django - Reglas para el agente

## Cuándo crear
- Para enrutar nuevas vistas HTML
- Para enrutar nuevas APIs versionadas

## Reglas

### 1. project/urls.py (raíz del proyecto)
- Incluir apps con `path('prefijo/', include('app.urls'))`
- Ruta vacía para app principal: `path('', include('app_principal.urls'))`
- Swagger al final: `path('api/schema/', ...)` y `path('api/docs/', ...)`

### 2. app/urls.py (cada app)
- Cada app tiene su propio urls.py
- Cada vista con `name='nombre'` para usar en templates con `{% url %}`
- Parámetros dinámicos: `<int:pk>` para IDs
- API versionada: `path('api/v1/', include('app.api.v1.urls'))`

### 3. api/v1/urls.py (API REST)
- Usar `DefaultRouter` para ViewSets
- `router.register(r'entidad', ViewSet, basename='entidad')`
- Vistas personalizadas (JWT, etc.): `path('accion/', View.as_view(), name='accion')`
- Sumar todo: `urlpatterns += router.urls`

### 4. Estructura de imports
```python
from django.urls import path, include
```

## Ejemplo genérico

```python
# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app1/', include('app1.urls')),
    path('', include('app2.urls')),
]

# app/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.listar, name='listar'),
    path('crear/', views.crear, name='crear'),
    path('editar/<int:pk>/', views.editar, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar, name='eliminar'),
    path('api/v1/', include('app.api.v1.urls')),
]

# app/api/v1/urls.py
from rest_framework.routers import DefaultRouter
from .views import EntidadViewSet

router = DefaultRouter()
router.register(r'entidad', EntidadViewSet, basename='entidad')

urlpatterns = router.urls
```
