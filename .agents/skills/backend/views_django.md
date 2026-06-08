# Views Django - Reglas para el agente

## Cuándo crear
- Por cada página de las apps web
- Cada vista maneja GET (renderizar) y POST (procesar)

## Reglas

### 1. Decoradores
- `@login_required` en las vistas que necesiten autenticación
- Importar: `from django.contrib.auth.decorators import login_required`

### 2. GET (mostrar formulario/página)
- Crear instancia del form: `form = MiForm()`
- Para edición: `form = MiForm(initial={'campo': objeto.campo, ...})`
- Renderizar: `return render(request, 'app/template.html', {'form': form, 'pk': objeto.id})`

### 3. POST (procesar datos)
- Validar: `form = MiForm(request.POST)` → `if form.is_valid():`
- Llamar service: `crear_entidad(form.cleaned_data)`
- Éxito: `return JsonResponse({'success': True, 'message': 'mensaje'})`
- Error de negocio: `except ValueError as e: return JsonResponse({'success': False, 'errors': str(e)})`
- Error de validación: `return JsonResponse({'success': False, 'errors': form.errors})`

### 4. Filtros por GET params
- Capturar: `request.GET.get('param', '')`
- Pasar filtros al template para mantener estado

### 5. Parámetros en URL
- Recibir: `def vista(request, pk):`
- Pasar `pk` al template para rutas POST/acciones

### 6. Template context
- Pasar: `form`, `titulo_form`, `pk` si es edición
- Titulo según el modo: crear vs modificar

## Ejemplo genérico

```python
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from .forms import MiForm
from .services import crear_entidad, obtener_entidad, actualizar_entidad


@login_required
def crear(request):
    if request.method == 'POST':
        form = MiForm(request.POST)
        if form.is_valid():
            try:
                crear_entidad(form.cleaned_data)
                return JsonResponse({'success': True, 'message': 'Creado con éxito'})
            except ValueError as e:
                return JsonResponse({'success': False, 'errors': str(e)})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = MiForm()
    return render(request, 'app/crear.html', {'form': form, 'titulo': 'Crear'})


@login_required
def editar(request, pk):
    entidad = obtener_entidad(pk)
    if request.method == 'POST':
        form = MiForm(request.POST)
        if form.is_valid():
            try:
                actualizar_entidad(entidad, form.cleaned_data)
                return JsonResponse({'success': True, 'message': 'Modificado con éxito'})
            except ValueError as e:
                return JsonResponse({'success': False, 'errors': str(e)})
    else:
        form = MiForm(initial={
            'nombre': entidad.nombre,
            'telefono': entidad.telefono,
        })
    return render(request, 'app/editar.html', {'form': form, 'pk': pk, 'titulo': 'Modificar'})


@login_required
def eliminar(request, pk):
    if request.method == 'POST':
        try:
            eliminar_entidad(pk)
            return JsonResponse({'success': True, 'message': 'Eliminado con éxito'})
        except ValueError as e:
            return JsonResponse({'success': False, 'errors': str(e)})
```
