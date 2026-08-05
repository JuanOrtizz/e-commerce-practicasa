import {successToast, errorToast, infoLoginAlertRedirect} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.agregar-carrito-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault()
            const formData = new FormData(form)
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value
            const action = form.getAttribute('action') || ''
            await postForm(formData, csrfToken, action, form)
        })
    })
})

async function postForm(formData, csrfToken, action, form){
    const btnSubmit = form.querySelector('button[type="submit"]')
    const text = btnSubmit.querySelector('.btn-text')
    const spinner = btnSubmit.querySelector('.btn-spinner')
    btnSubmit.disabled = true
    text.textContent = ""
    spinner.classList.remove("d-none")

    try {
        const response = await fetch(action, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        const data = await response.json()
        if (response.status === 401 || response.status === 403) {
            infoLoginAlertRedirect("Debés iniciar sesión para agregar productos al carrito", `/usuarios/login/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`)
        } else if(data.success){
            successToast(data.success.message)
        }else{
            if (typeof data.errors === "string") {
                errorToast(data.errors)
            }
        }
    }catch(error){
        console.log(error)
        errorToast("Ocurrió un error inesperado. Intentá más tarde.")
    }finally {
        btnSubmit.disabled = false
        text.textContent = "Agregar al Carrito"
        spinner.classList.add("d-none")
    }
}
