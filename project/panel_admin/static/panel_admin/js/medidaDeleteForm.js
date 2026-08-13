import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.medida-delete-btn')

    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const medidaId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar esta medida?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(medidaId, csrfToken, form)
            })
        })
    })
})

async function deleteForm(medidaId, csrfToken, form) {
    const btn = form.querySelector('.btn-delete')
    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        const data = await response.json()
        if (data.success) {
            const medidaTr = document.getElementById(`item-medida-${medidaId}`)
            if (medidaTr) {
                medidaTr.remove()
                const contador = document.getElementById("count-medidas")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".medida-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-medidas-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "La medida fue eliminada correctamente.")
            }
        } else if (data.message) {
            errorAlert(data.message)
        }
    } catch(error) {
        errorAlert("Ocurrió un error inesperado. Intentá más tarde.")
    } finally {
        btn.disabled = false
    }
}
