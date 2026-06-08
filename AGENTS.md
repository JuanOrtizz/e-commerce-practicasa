# AGENTS.md - Proyecto Django con DRF

## Stack
- **Backend**: Django + Django REST Framework
- **API Auth**: JWT (SimpleJWT)
- **Web Auth**: Django Auth con sesiones
- **Documentación API**: drf-spectacular (Swagger UI + OpenAPI 3.0)
- **Frontend**: Django Templates (Jinja2) + Bootstrap 5 + SweetAlert2 + CSS y JS personalizado
- **DB**: PostgreSQL
- **Infra**: Docker + WhiteNoise

## Estructura base del proyecto
```
project/
├── project/              # Config principal (settings, urls, wsgi)
├── app_name/             # App Django
│   ├── api/v{N}/         # API versionada
│   ├── services.py       # Capa de lógica de negocio
│   ├── forms.py          # Formularios HTML
│   ├── static/app_name/  # Estáticos propios
│   └── templates/app_name/
├── static/               # Estáticos globales (css, img, js)
└── templates/            # Templates globales (base, header, footer)
```

## Reglas del agente
1. **Pedir Confirmación**: Antes de crear o modificar archivos, siempre pedir confirmación explicando qué se va a hacer
2. **Leer antes de crear/modificar**: Siempre leer archivos y skills existentes para entender contexto y patrones
3. **Seguir patrones existentes**: No inventar nuevas convenciones. Usar misma estructura, imports y estilo
4. **Revisar dependencias**: Antes de agregar nuevo paquete, verificar si existe en requirements.txt
5. **Usar librerías existentes**: SweetAlert2, Bootstrap 5, Material Symbols, drf-spectacular, simplejwt
6. **No agregar comentarios**: El código debe ser auto-explicativo
7. **Modificar solo lo solicitado**: No cambiar archivos no mencionados explícitamente
8. **Validar sintaxis**: Verificar consistencia antes de finalizar
9. **Conventional commits**: Luego de cada cambio indicar nomenclatura y mensaje para commits. feat:, fix:, docs:, refactor:, chore:
10. **CSRF**: Siempre en forms POST (`{% csrf_token %}`) y fetch (`X-CSRFToken` header)
11. **JS Modules**: ES6 Modules (`type="module"`) con import/export
12. **API versionada**: `api/v{N}/` dentro de cada app. Solo si es necesario, si no contiene DRF, no crear carpeta api.
13. **Auth dual**: Django Auth para HTML, JWT para API
14. **Service Layer**: Lógica de negocio en services.py, no en views