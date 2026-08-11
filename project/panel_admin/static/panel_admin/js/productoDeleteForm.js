import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.btn-delete')

    // Evento para evitar que se mande el form
    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const productoId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar este producto?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(productoId, csrfToken, form)
            })
        })
    })
})

// funcion async para utilizar await y manejar asincronia
async function deleteForm(productoId, csrfToken, form) {
    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        const data = await response.json()
        if (data.success) {
            const productoTr = document.getElementById(`producto-${productoId}`)
            if (productoTr) {
                productoTr.remove()
                const contador = document.getElementById("productos-count")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".producto-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-productos-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "El producto fue eliminado correctamente.")
            }
        } else {
            const errors = data.errors
            if (typeof errors === "string") {
                errorAlert(data.errors)
            }
        }
    } catch(error) {
        errorAlert("Ocurrió un error inesperado. Intentá más tarde.")
    }
}
