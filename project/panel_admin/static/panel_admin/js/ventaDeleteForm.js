import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.btn-delete')
    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const ventaId = btn.getAttribute('data-id')
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert('¿Estás seguro que querés eliminar esta venta?', 'Eliminar', () => {
                btn.disabled = true
                deleteForm(ventaId, csrfToken, form)
            })
        })
    })
})

async function deleteForm(ventaId, csrfToken, form) {
    const btn = form.querySelector('.btn-delete')
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        })
        const data = await response.json()
        if (data.success) {
            const ventaTr = document.getElementById(`venta-${ventaId}`)
            if (ventaTr) {
                ventaTr.remove()
                const contador = document.getElementById('ventas-count')
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll('.venta-item')
                if (elementos.length === 0) {
                    const empty = document.getElementById('no-ventas-message')
                    if (empty) {
                        empty.classList.remove('d-none')
                    }
                }
                successAlert(data.message, 'La venta fue eliminada correctamente.')
            }
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
