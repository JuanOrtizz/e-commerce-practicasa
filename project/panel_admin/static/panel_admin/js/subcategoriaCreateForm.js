import {textErrorInput, clearErrorText, scrollToFirstError} from './validacionesProducto.js'
import {successAlertRedirectOnClose, errorAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', ()=>{
    const form = document.getElementById("form")
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value

    form.querySelectorAll("input, select").forEach(input => {
        if (!input.dataset.listener){
            input.addEventListener('focus', ()=>{
                clearErrorText(input)
            })
            input.dataset.listener = "true"
        }
    })

    form.addEventListener('submit', (e) =>{
        e.preventDefault()
        const formData = new FormData(form)
        postForm(formData, csrfToken, form)
    })
})

async function postForm(formData, csrfToken, form){
    const btnSubmit = document.getElementById("btn-submit")
    const text = document.getElementById("btn-text")
    const spinner = document.getElementById("btn-spinner")
    btnSubmit.disabled = true
    text.textContent = ""
    spinner.classList.remove("d-none")

    try
    {
        const response = await fetch(form.action,{
            method:"POST",
            body: formData,
            headers:{
                "X-CSRFToken": csrfToken
            }
        })
        const data = await response.json()
        if(data.success){
            successAlertRedirectOnClose(data.message, data.redirect)
        }else{
            const errors = data.errors
            for (let field in errors) {
                const msj = errors[field][0]
                const input = document.getElementById(`id_${field}`)
                if (input) {
                    textErrorInput(input, msj)
                }
            }
            scrollToFirstError()
        }
    }catch(error){
        console.log(error)
        errorAlert("Ocurrió un error inesperado. Intentá más tarde.")
    }
    finally {
        btnSubmit.disabled = false
        text.textContent = "Crear subcategoría"
        spinner.classList.add("d-none")
    }
}
