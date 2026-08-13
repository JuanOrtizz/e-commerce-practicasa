import {successAlert, errorAlert, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const btnsDelete = document.querySelectorAll('.subcategoria-delete-btn')

    btnsDelete.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault()
            const subcategoriaId = btn.getAttribute("data-id")
            const form = btn.closest('form')
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            confirmAlert("¿Estás seguro que querés eliminar esta subcategoría?", "Eliminar", () => {
                btn.disabled = true
                deleteForm(subcategoriaId, csrfToken, form)
            })
        })
    })
})

async function deleteForm(subcategoriaId, csrfToken, form) {
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
            const subcategoriaTr = document.getElementById(`item-subcategoria-${subcategoriaId}`)
            if (subcategoriaTr) {
                subcategoriaTr.remove()
                const contador = document.getElementById("count-subcategorias")
                if (contador) {
                    contador.textContent = parseInt(contador.textContent) - 1
                }
                const elementos = document.querySelectorAll(".subcategoria-item")
                if (elementos.length === 0) {
                    const empty = document.getElementById("no-subcategorias-message")
                    if (empty) {
                        empty.classList.remove("d-none")
                    }
                }
                successAlert(data.message, "La subcategoría fue eliminada correctamente.")
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
