import {validateForm, textErrorInput} from './validacionesContacto.js'
import {successAlert, errorAlert} from './alertas.js'

document.addEventListener('DOMContentLoaded', ()=>{
    // capturo el formulario y el token
    const form = document.getElementById("form")
    const csrfToken = document.querySelector('[name = csrfmiddlewaretoken]').value

    // Evento para evitar que se mande el form
    form.addEventListener('submit', (e) =>{
        // evita recargar la pagina al mandar el formulario
        e.preventDefault()
        // captura los datos del formulario
        const formData = new FormData(form)
        // valida los campos del formulario, si son validos, hace el post del formulario
        if(validateForm(formData)){
            postForm(formData, csrfToken, form)
        }
    })
})

// funcion async para utilizar await y manejar asincronia
async function postForm(formData, csrfToken, form){
    const btnSubmit = document.getElementById("btn-submit") // Obtiene el botón de submit
    const text = document.getElementById("btn-text")
    const spinner = document.getElementById("btn-spinner")
    btnSubmit.disabled = true // Deshabilita el botón de submit para evitar múltiples envíos
    text.textContent = ""
    spinner.classList.remove("d-none")

    // hago fetch del formulario
    try
    {
        const response = await fetch("/contacto/",{
            method:"POST",
            body: formData,
            headers:{
                "X-CSRFToken": csrfToken
            }
        })
        const data = await response.json()
        if(data.success){
            // vacio el formulario
            form.reset()
            successAlert("¡Recibimos tu consulta!", "Quedate atento a tu email o teléfono porque nos pondremos en contacto lo antes posible")
        }else{
            const errors = data.errors //capturo los errores
            //Si los errores son string (provenientes de la vista)
            if (typeof errors === "string") {
                errorAlert(data.errors)//Muestro una alerta
            }
            else{ // Sino (errores en formulario), muestro mediante un for estos errores provenientes de forms.py
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
        text.textContent = "Registrar Sesión"
        spinner.classList.add("d-none")
    }
}