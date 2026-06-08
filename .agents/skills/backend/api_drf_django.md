# API DRF - Reglas para el agente

## Cuándo crear
- Para endpoints REST personalizados (no CRUD estándar)
- Para cada nueva versión de la API

## Reglas

### 1. Versionado
- Estructura de carpetas: `app/api/v{N}/`
- Cada nivel con `__init__.py`
- Inclusión desde app/urls.py: `path('api/v1/', include('app.api.v1.urls'))`
- Contenido de `api/v1/`: `views.py`, `serializers.py`, `urls.py`

### 2. GenericViewSet con acciones personalizadas
- Heredar de `viewsets.GenericViewSet`
- Atributos: `serializer_class`, `throttle_classes`, `throttle_scope`
- `@action(detail=False, methods=['post'])` para acciones sobre la colección
- `@action(detail=False, methods=['get'], url_path='nombre')` para rutas custom
- `@action(detail=True, methods=['post'])` para acciones sobre un elemento específico

### 3. Permisos dinámicos
- Sobrescribir `get_permissions(self)`
- Según `self.action`: retornar `[permissions.AllowAny()]` o `[permissions.IsAuthenticated()]`

### 4. Throttles personalizados
- Crear clases en `project/throttles.py` heredando de `AnonRateThrottle`
- Asignar `scope` único que coincida con `DEFAULT_THROTTLE_RATES` en settings
- Asignar en ViewSet: `throttle_classes = [ScopedRateThrottle, MiThrottle]`

### 5. Documentación con drf-spectacular
En settings:
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Proyecto',
    'DESCRIPTION': 'Documentación de la API',
    'VERSION': '1.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```
En project/urls.py:
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

### 6. ViewSet con @action
- `@extend_schema(summary="...", description="...")` antes del decorador `@action`
- El método recibe `self, request` (y `pk` si detail=True)
- Retornar `Response(data, status=status.HTTP_201_CREATED)` o `Response(data)`

### 7. Serializer para acciones custom
- Validaciones idénticas al form HTML
- Método `create()` con `User.objects.create_user()` si es modelo User
- `extra_kwargs` para campos write_only (password)

## Ejemplo genérico

```python
# app/api/v1/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import MiSerializer

class MiViewSet(viewsets.GenericViewSet):
    serializer_class = MiSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'crear':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(summary="Crear elemento")
    @action(detail=False, methods=['post'])
    def crear(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Obtener perfil actual")
    @action(detail=False, methods=['get'], url_path='perfil')
    def perfil(self, request):
        return Response(self.get_serializer(request.user).data)


# app/api/v1/serializers.py
from rest_framework import serializers

class MiSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiModelo
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}
```
