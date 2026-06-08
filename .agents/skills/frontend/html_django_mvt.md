# HTML Django MVT - Reglas para el agente

## Cuándo crear
- Para cada página de la app usando Django Templates

## Reglas base del sistema de templates

### 1. Herencia y estructura
- Todos los templates extienden `base.html`
- `base.html` ubicado en `templates/` (global)
- `{% extends 'base.html' %}` al inicio

### 2. Bloques disponibles en base.html
| Bloque | Uso |
|--------|-----|
| `{% block title %}` | Título de la página |
| `{% block extra_css %}` | CSS específico de la página |
| `{% block content %}` | Contenido principal |
| `{% block extra_js %}` | JS específico de la página (al final del body) |

### 3. Inclusión de partials
- `{% include 'header.html' %}` — navbar/logout
- `{% include 'footer.html' %}` — footer
- Los partials se incluyen en base.html, no en cada template

### 4. Archivos estáticos
- `{% load static %}` al inicio del template
- `{% static 'ruta/archivo' %}` para referenciar archivos

### 5. URLs dinámicas
- `{% url 'nombre_ruta' %}` — sin parámetros
- `{% url 'editar' item.id %}` — con parámetros

### 6. CSRF
- `{% csrf_token %}` en TODOS los formularios POST

## Reglas de Bootstrap y diseño

### 7. Layout responsive
- `container-fluid` para ancho completo
- `row` + `col-12` para estructura de columnas
- `col-lg-6` o `col-md-6` para dividir en desktop
- `g-3` para espaciado entre columnas

### 8. Tabla (vista desktop)
- `d-none d-lg-block` para ocultar en mobile
- `table`, `table-responsive`, `rounded-3`, `shadow`, `align-middle`
- `table-group-divider` para separar thead

### 9. Cards (vista mobile)
- `d-block d-lg-none` para ocultar en desktop
- `card`, `card-body`, `shadow-sm`, `border-info`, `border-2`

### 10. Formularios
- `form-floating` para labels flotantes
- `form-control` en inputs de texto
- `form-select` en selects
- `has-validation` + `invalid-feedback` para errores de validación
- `is-invalid` para inputs con error
- `novalidate` en form tag para desactivar validación HTML5 nativa

### 11. Botones
| Clase Bootstrap | Uso |
|----------------|-----|
| `btn btn-success` | Crear/registrar |
| `btn btn-warning btn-sm` | Modificar/editar |
| `btn btn-danger btn-sm` | Eliminar |
| `btn btn-info` / `btn-primary` | Acciones varias |
| `fw-bold` | Texto en negrita |
| `w-100` | Ancho completo |

### 12. Alertas
- `alert alert-info` para mensajes informativos
- `alert alert-danger` para errores
- `text-center` para centrar texto

## Reglas de Jinja2 / Django Template Language

### 13. Condicionales y loops
- `{% if user.is_authenticated %}` — verificar sesión
- `{% for item in items %}` — iterar listas/querysets
- `{% empty %}` — dentro de for, para lista vacía

### 14. Variables
- `{{ item.campo }}` — acceder a atributos
- `{{ form.field.label }}`, `{{ form.field }}`, `{{ form.field.errors }}` — form fields
- `{{ valor|add:'texto' }}` — filter para concatenar
- `{{ valor|default:"texto" }}` — valor por defecto

## Ejemplo genérico

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Listado{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'app/css/estilos.css' %}">
{% endblock %}

{% block content %}
<div class="container-fluid p-3">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Listado de Elementos</h1>
        <a href="{% url 'crear' %}" class="btn btn-success">Agregar Nuevo</a>
    </div>

    <!-- Desktop: tabla -->
    <div class="d-none d-lg-block">
        <table class="table table-responsive rounded-3 shadow align-middle">
            <thead><tr><th>#</th><th>Nombre</th><th>Acciones</th></tr></thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>{{ item.id }}</td>
                    <td>{{ item.nombre }}</td>
                    <td>
                        <a href="{% url 'editar' item.id %}" class="btn btn-warning btn-sm">Editar</a>
                        <button class="btn btn-danger btn-sm btn-eliminar" data-id="{{ item.id }}">Eliminar</button>
                    </td>
                </tr>
                {% empty %}
                <tr><td colspan="3"><div class="alert alert-info text-center">No hay elementos</div></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Mobile: cards -->
    <div class="d-block d-lg-none">
        {% for item in items %}
        <div class="card shadow-sm border-info border-2 mb-3">
            <div class="card-body">
                <p><strong>{{ item.nombre }}</strong></p>
                <a href="{% url 'editar' item.id %}" class="btn btn-warning btn-sm">Editar</a>
                <button class="btn btn-danger btn-sm btn-eliminar" data-id="{{ item.id }}">Eliminar</button>
            </div>
        </div>
        {% empty %}
        <div class="alert alert-info text-center">No hay elementos</div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script type="module" src="{% static 'app/js/acciones.js' %}"></script>
{% endblock %}
```
