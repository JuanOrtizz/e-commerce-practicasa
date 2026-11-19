import { errorAlert, confirmAlert, successToast } from '/static/js/alertas.js'

const MENSAJES = {
    reembolsado: 'Se marcará como reembolsado. Hacelo después de devolver el pago en Mercado Pago.',
    aprobado: 'El pago volverá a figurar como aprobado.',
}

const FLASH_KEY = 'panel_pago_estado_flash'

document.addEventListener('DOMContentLoaded', () => {
    mostrarFlash()
    const forms = document.querySelectorAll('.pago-estado-form')
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault()
            const estado = form.dataset.estado
            confirmAlert(
                MENSAJES[estado] || '¿Confirmás el cambio de estado?',
                estado === 'reembolsado' ? 'Reembolsar' : 'Restaurar',
                () => enviarEstado(form)
            )
        })
    })
})

function mostrarFlash() {
    const mensaje = sessionStorage.getItem(FLASH_KEY)
    if (!mensaje) {
        return
    }
    sessionStorage.removeItem(FLASH_KEY)
    successToast(mensaje)
}

async function enviarEstado(form) {
    const btn = form.querySelector('button')
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
    btn.disabled = true
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-CSRFToken': csrfToken }
        })
        const data = await response.json()
        if (data.success) {
            sessionStorage.setItem(FLASH_KEY, data.message)
            window.location.reload()
        } else {
            errorAlert(data.message || 'Ocurrió un error.')
        }
    } catch (error) {
        console.log(error)
        errorAlert('Ocurrió un error inesperado.')
    } finally {
        btn.disabled = false
    }
}
