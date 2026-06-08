# Models Django - Reglas para el agente

## Cuándo crear
- Por cada entidad de negocio que requiera persistencia en BD

## Reglas

### 1. Nombrado
- Clase en español y plural: `Productos`, `Clientes`, `Pedidos`
- Campos en snake_case: `fecha_creacion`, `nombre_completo`
- db_table en snake_case: `nombre_tabla`

### 2. Tipos de campo
- `CharField` siempre con `max_length`
- `db_index=True` en campos frecuentemente buscados (nombre, email, fecha)
- `auto_now_add=True` en fechas de creación automáticas
- `null=True, blank=True` para campos opcionales
- `TimeField(null=True, blank=True)` para horas opcionales
- `EmailField(unique=True, db_index=True)` para emails únicos
- No omitir `max_length` en CharField (bug: Django asume varchar(1))

### 3. Restricciones
- `UniqueConstraint` dentro de `Meta.constraints`
- Siempre con `name='unique_descripcion'`
- Para combinaciones de campos: `fields=['campo1', 'campo2']`

### 4. Meta
- `db_table = 'nombre_tabla'` en snake_case
- `constraints = [...]` para restricciones de unicidad

### 5. Admin
- Registrar con `@admin.register(Modelo)`
- Clase hereda de `admin.ModelAdmin`
- `list_display` con campos a mostrar en el panel

### 6. Errores comunes
- Olvidar `null=True, blank=True` en campos opcionales → error de BD
- CharField sin max_length → varchar(1) en PostgreSQL

## Ejemplo genérico

```python
from django.db import models

class Clientes(models.Model):
    nombre = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    telefono = models.CharField(max_length=25)
    fecha_creacion = models.DateField(auto_now_add=True, db_index=True)
    campo_opcional = models.CharField(max_length=50, null=True, blank=True)
    hora_evento = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'clientes'
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'telefono'],
                name='unique_cliente_telefono'
            )
        ]

# admin.py
from django.contrib import admin
from .models import Clientes

@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'email', 'telefono', 'fecha_creacion']
```
