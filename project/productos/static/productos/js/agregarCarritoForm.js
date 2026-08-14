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

    window.gsap?.fromTo(btnSubmit, { scale: 0.96 }, { scale: 1, duration: 0.25, ease: "back.out(1.8)" })

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
            window.gsap?.fromTo(btnSubmit, { scale: 1 }, { scale: 1.08, duration: 0.15, ease: "power2.out", yoyo: true, repeat: 1 })
            actualizarStockRestante(data.success)
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

function actualizarStockRestante(success) {
    if (!success.producto_id || success.stock_restante === undefined) return
    document.querySelectorAll('.agregar-carrito-form').forEach(form => {
        const input = form.querySelector(`input[name="producto_id"][value="${success.producto_id}"]`)
        if (!input) return
        const card = form.closest('.card')
        const btn = form.querySelector('button[type="submit"]')
        if (success.stock_restante <= 0) {
            if (card) card.classList.add('card-disabled')
            if (btn && btn.textContent.trim() !== 'Sin stock') {
                const nuevoBtn = document.createElement('button')
                nuevoBtn.type = 'button'
                nuevoBtn.className = 'btn btn-secondary w-100 py-2'
                nuevoBtn.disabled = true
                nuevoBtn.textContent = 'Sin stock'
                form.replaceChild(nuevoBtn, btn)
            }
        } else {
            if (card) card.classList.remove('card-disabled')
        }
    })
}
