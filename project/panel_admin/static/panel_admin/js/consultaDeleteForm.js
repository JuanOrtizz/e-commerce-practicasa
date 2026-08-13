import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.btn-delete')

    // Evento para evitar que se mande el form
    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const consultaId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar esta consulta?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(consultaId, csrfToken, form)
            })
        })
    })
})

// funcion async para utilizar await y manejar asincronia
async function deleteForm(consultaId, csrfToken, form) {
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
            const consultaTr = document.getElementById(`consulta-${consultaId}`)
            if (consultaTr) {
                consultaTr.remove()
                const contador = document.getElementById("consultas-count")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".consulta-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-consultas-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "La consulta fue eliminada correctamente.")
            }
        } else {
            const errors = data.errors
            if (typeof errors === "string") {
                errorAlert(data.errors)
            }
        }
    } catch(error) {
        errorAlert("Ocurrió un error inesperado. Intentá más tarde.")
    } finally {
        btn.disabled = false
    }
}
