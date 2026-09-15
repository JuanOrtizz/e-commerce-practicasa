import {validateForm, textErrorInput} from './validacionesCheckout.js'
import {errorAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', ()=>{
    const form = document.getElementById("form")
    if (!form) {
        return
    }
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value

    form.addEventListener('submit', (e) =>{
        e.preventDefault()
        const formData = new FormData(form)
        if(validateForm(formData)){
            postForm(formData, csrfToken, form)
        }
    })
})

async function postForm(formData, csrfToken, form){
    const btnSubmit = document.getElementById("btn-submit")
    const text = document.getElementById("btn-text")
    const textBtnInicial = text.textContent
    const spinner = document.getElementById("btn-spinner")
    btnSubmit.disabled = true
    text.textContent = ""
    spinner.classList.remove("d-none")

    try
    {
        const response = await fetch("",{
            method:"POST",
            body: formData,
            headers:{
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        const data = await response.json()
        if(data.success){
            if (data.redirect) {
                window.location.href = data.redirect
            } else {
                form.reset()
            }
        }else{
            const errors = data.errors
            if (errors.__all__) {
                const nonFieldDiv = document.getElementById("non-field-errors")
                if (nonFieldDiv) {
                    nonFieldDiv.textContent = errors.__all__[0]
                    nonFieldDiv.classList.remove("d-none")
                }
            }
            else{
                for (let field in errors) {
                    const msj = errors[field][0]
                    const input = document.getElementById(`id_${field}`)
                    if (input) {
                        textErrorInput(input, msj)
                    }
                }
            }
        }
    }catch(error){
        console.log(error)
        errorAlert("Ocurrió un error inesperado. Intentá más tarde.")
    }
    finally {
        btnSubmit.disabled = false
        text.textContent = textBtnInicial
        spinner.classList.add("d-none")
    }
}