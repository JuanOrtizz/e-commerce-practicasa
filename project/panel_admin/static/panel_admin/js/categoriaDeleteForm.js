import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.categoria-delete-btn')

    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const categoriaId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar esta categoría?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(categoriaId, csrfToken, form)
            })
        })
    })
})

async function deleteForm(categoriaId, csrfToken, form) {
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
            const categoriaTr = document.getElementById(`item-categoria-${categoriaId}`)
            if (categoriaTr) {
                categoriaTr.remove()
                const contador = document.getElementById("count-categorias")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".categoria-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-categorias-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "La categoría fue eliminada correctamente.")
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
