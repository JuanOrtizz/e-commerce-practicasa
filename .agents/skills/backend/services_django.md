# Services Django - Reglas para el agente

## Cuándo crear
- Para encapsular lógica de negocio separada de las vistas
- Para operaciones CRUD con validaciones adicionales
- Archivo: `services.py` dentro de cada app

## Reglas

### 1. Estructura de funciones
- Funciones independientes (no clases)
- Cada función recibe datos ya validados (cleaned_data del form)
- Nombrar con prefijo de acción: `crear_entidad()`, `obtener_entidad()`, `actualizar_entidad()`, `eliminar_entidad()`

### 2. Sanitización de datos
- `.strip().title()` para nombres
- `.strip()` para teléfonos
- `.lower()` para emails
- Strings vacíos → None: `if valor == '': valor = None`
- Usar `__iexact` en filtros para búsqueda case-insensitive

### 3. Verificación de duplicados
- Antes de crear: `if Modelo.objects.filter(campo=valor).exists(): raise ValueError("mensaje")`
- En update: siempre agregar `.exclude(id=objeto.id)` para no detectar el mismo registro

### 4. Manejo de errores
- `ValueError` para errores de negocio (duplicados, no encontrado)
- Capturar `Modelo.DoesNotExist` y convertir a `ValueError`
- No usar Http404 en services (es capa de lógica, no de presentación)

### 5. Retorno
- Función crear → retorna el objeto creado
- Función actualizar → retorna el objeto actualizado
- Función obtener → retorna el objeto o lanza ValueError
- Función listar → retorna queryset (sin evaluar)
- Función eliminar → no retorna nada, lanza ValueError si no existe

## Ejemplo genérico

```python
from .models import Entidad

def crear_entidad(data):
    nombre = data.get('nombre').strip().title()
    campo_opcional = data.get('campo_opcional')
    
    if campo_opcional == '':
        campo_opcional = None
    
    if campo_opcional is not None:
        if Entidad.objects.filter(nombre__iexact=nombre, campo_opcional=campo_opcional).exists():
            raise ValueError(f'Ya existe una entidad con nombre {nombre}')
    
    entidad = Entidad(
        nombre=nombre,
        campo_opcional=campo_opcional,
    )
    entidad.save()
    return entidad


def obtener_entidad(pk):
    try:
        return Entidad.objects.get(id=pk)
    except Entidad.DoesNotExist:
        raise ValueError("Entidad no encontrada")


def listar_entidades():
    return Entidad.objects.all()


def actualizar_entidad(entidad, data):
    nombre = data.get('nombre').strip().title()
    campo_opcional = data.get('campo_opcional')
    
    if campo_opcional == '':
        campo_opcional = None
    
    if campo_opcional is not None:
        if Entidad.objects.filter(nombre__iexact=nombre, campo_opcional=campo_opcional).exclude(id=entidad.id).exists():
            raise ValueError(f'Ya existe una entidad con nombre {nombre}')
    
    entidad.nombre = nombre
    entidad.save()
    return entidad


def eliminar_entidad(pk):
    try:
        Entidad.objects.get(id=pk).delete()
    except Entidad.DoesNotExist:
        raise ValueError("Entidad no encontrada")
```
