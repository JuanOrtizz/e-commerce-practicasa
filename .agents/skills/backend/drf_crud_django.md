# CRUD DRF - Reglas para el agente

## Cuándo crear
- Para endpoints REST CRUD completos sobre un modelo
- Usar ModelViewSet cuando se necesiten: list, create, retrieve, update, destroy

## Reglas

### 1. ViewSet
- Heredar de `viewsets.ModelViewSet`
- Atributos: `queryset`, `serializer_class`, `permission_classes`
- Decorar clase con `@extend_schema(tags=['nombre_grupo'])`
- Decorar cada acción con `@extend_schema(summary="...", description="...")`
- Configurar `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'` en settings

### 2. Serializer
- Heredar de `serializers.ModelSerializer`
- `fields` listando campos del modelo
- `read_only_fields` para campos auto-asignados (fechas, ids)
- `extra_kwargs` para write_only (contraseñas)
- Validaciones: `validate_<campo>()` — misma lógica que forms.py

### 3. Router
- `router.register(r'nombre', ViewSet, basename='nombre')`
- `urlpatterns = router.urls`
- No necesita `as_view()` ni nombres individuales

### 4. Permisos
- `permission_classes = [permissions.IsAuthenticated]` por defecto
- Importar: `from rest_framework import permissions`

## Ejemplo genérico

```python
# api/v1/views.py
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema
from ...models import Entidad
from .serializers import EntidadSerializer

@extend_schema(tags=['entidad'])
class EntidadViewSet(viewsets.ModelViewSet):
    queryset = Entidad.objects.all()
    serializer_class = EntidadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Listar entidades")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Crear entidad")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener entidad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar entidad")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar entidad")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# api/v1/serializers.py
from rest_framework import serializers
from ...models import Entidad

class EntidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entidad
        fields = ['id', 'nombre', 'telefono', 'fecha_creacion', 'campo_opcional']
        read_only_fields = ['fecha_creacion']

    def validate_nombre(self, value):
        value = value.strip().title()
        if len(value) < 2 or len(value) > 100:
            raise serializers.ValidationError("Longitud inválida")
        return value
```
