import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.color-delete-btn')

    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const colorId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar este color?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(colorId, csrfToken, form)
            })
        })
    })
})

async function deleteForm(colorId, csrfToken, form) {
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
            const colorTr = document.getElementById(`item-color-${colorId}`)
            if (colorTr) {
                colorTr.remove()
                const contador = document.getElementById("count-colores")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".color-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-colores-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "El color fue eliminado correctamente.")
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
