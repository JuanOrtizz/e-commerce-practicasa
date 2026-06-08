# Archivos Static Django MVT - Reglas para el agente

## Cuándo crear
- Para organizar archivos CSS, JS, imágenes del proyecto

## Reglas

### 1. Estructura global (static/)
```
static/
├── css/
│   └── globalStyles.css      # Estilos globales (colores, layout base)
├── img/
│   └── logo.webp             # Imágenes globales (favicon, logo)
└── js/
    └── global.js             # JS global (puede estar vacío si no se usa)
```

### 2. Estructura por app (app/static/app/)
```
app/static/app/
├── css/
│   ├── estilos.css           # Estilos específicos de la app
│   └── adicional.css         # (opcional, puede estar vacío)
└── js/
    ├── alerts.js             # Alertas SweetAlert2
    ├── validaciones.js        # Validaciones client-side
    ├── crear.js               # Lógica de formulario crear
    ├── editar.js              # Lógica de formulario editar
    └── eliminar.js            # Lógica de eliminación
```

### 3. Solo apps con archivos propios
- Crear carpeta `static/app/` solo si la app tiene archivos propios
- Apps sin estáticos no necesitan la carpeta

### 4. Configuración en settings.py (NO TOCAR)
```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # solo global
```

### 5. Referencia en templates
```html
{% load static %}

<!-- Globales -->
<link rel="stylesheet" href="{% static 'css/globalStyles.css' %}">
<link rel="icon" href="{% static 'img/favicon.webp' %}">

<!-- Por app -->
<link rel="stylesheet" href="{% static 'app/css/estilos.css' %}">
<script type="module" src="{% static 'app/js/crear.js' %}"></script>
```

### 6. Reglas adicionales
- `type="module"` en scripts JS tipo módulo
- CDNs (SweetAlert2, Bootstrap) se cargan directamente, no via static
- Google Fonts vía link tag o @import
- WhiteNoise comprime y cachea en producción (STATICFILES_STORAGE)

### 7. Errores comunes
- Olvidar `{% load static %}` antes de `{% static %}`
- Rutas incorrectas: la ruta en `{% static %}` es relativa a la carpeta `static/`
- STATICFILES_DIRS debe apuntar solo a la carpeta global (las de app se detectan automáticamente)
```
