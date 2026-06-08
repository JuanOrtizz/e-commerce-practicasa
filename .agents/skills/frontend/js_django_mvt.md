# JS Django MVT - Reglas para el agente

## Cuándo crear
- Para interactividad del frontend: formularios, filtros, eliminación
- Para comunicación asíncrona con vistas Django

## Reglas

### 1. ES6 Modules
- `type="module"` en script tag
- `export function miFuncion() { }` para exportar
- `import { funcion } from './archivo.js'` para importar
- No usar variables globales ni window.* innecesariamente

### 2. CSRF en fetch
- Obtener token: `document.querySelector('[name=csrfmiddlewaretoken]').value`
- Enviar en header: `'X-CSRFToken': csrfToken`
- Siempre en peticiones POST

### 3. Estructura de fetch POST (JSON)
```javascript
async function postData(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}
```

### 4. Estructura de fetch POST (FormData)
```javascript
async function postForm(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
    });
    return await response.json();
}
```

### 5. Manejo de respuestas JsonResponse
```javascript
const data = await response.json();
if (data.success) {
    // mostrar éxito, resetear form, redirigir
} else if (typeof data.errors === 'string') {
    // error de negocio (mensaje simple)
    errorAlert(data.errors);
} else {
    // errores de validación por campo
    Object.entries(data.errors).forEach(([campo, errores]) => {
        textErrorInput(document.getElementById(`id_${campo}`), errores);
    });
}
```

### 6. SweetAlert2
- `successAlert(text)` — alerta de éxito con botón cerrar
- `successAlertRedirect(text)` — éxito con botón "Ir a Dashboard"
- `errorAlert(text)` — alerta de error
- `confirmAlert(text, action, callback)` — confirmación antes de eliminar

### 7. sessionStorage para mensajes entre páginas
```javascript
// En página origen
sessionStorage.setItem('msgSuccess', 'Operación exitosa');
window.location.href = '/';

// En página destino
const msg = sessionStorage.getItem('msgSuccess');
if (msg) { successAlert(msg); sessionStorage.removeItem('msgSuccess'); }
```

### 8. Submit de formularios (patrón)
```javascript
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    if (!validar(formData)) return;

    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.querySelector('.spinner').classList.remove('d-none');

    try {
        const data = await postForm(form.action, formData);
        if (data.success) {
            form.reset();
            successAlertRedirect(data.message);
        } else {
            errorAlert(data.errors || "Error");
        }
    } catch (error) {
        errorAlert("Error de conexión");
    } finally {
        btn.disabled = false;
        btn.querySelector('.spinner').classList.add('d-none');
    }
});
```

### 9. Validación client-side
- Validar antes del fetch para feedback instantáneo
- `textErrorInput(input, msj)` — agrega `is-invalid` y mensaje en `invalid-feedback`
- `clearErrorText(input)` — remueve `is-invalid`
- Iterar sobre `FormData.entries()` para validar campos

## Ejemplo genérico

```javascript
// app/static/app/js/alerts.js
import Swal from 'sweetalert2';

export function successAlert(text) {
    Swal.fire({ icon: 'success', text, confirmButtonColor: '#3366CC' });
    document.body.classList.remove('swal2-height-auto');
}

export function errorAlert(text) {
    Swal.fire({ icon: 'error', text, confirmButtonColor: '#000000' });
    document.body.classList.remove('swal2-height-auto');
}

export function confirmAlert(text, action, callback) {
    Swal.fire({
        text, icon: 'warning',
        showCancelButton: true,
        confirmButtonText: `Sí, ${action}`,
        confirmButtonColor: '#3366CC'
    }).then((result) => { if (result.isConfirmed) callback(); });
    document.body.classList.remove('swal2-height-auto');
}
```
