// funcion para validar el formulario
export function validateForm(formData){
    let isValid = true // al comienzo siempre va a ser valido

    // capturo el formulario para limpiar los errores anteriores
    const form = document.getElementById("form")
    form.querySelectorAll(".is-invalid").forEach(el => {
        clearErrorText(el)
    })

    // recorre cada input del formulario y realiza las validaciones con sus metodos
    for(let [llave, valor] of formData.entries()){
        const input = document.getElementById(`id_${llave}`)
        if (!input) {
            continue
        }

        if (!input.dataset.listener){
            input.addEventListener('focus', ()=>{
                clearErrorText(input)
            })
            input.dataset.listener = "true"
        }

        valor = valor.trim()
        if(!valor){
            textErrorInput(input, "El campo está vacío")
            isValid = false
        }
        else if (llave === "nombre"){
            if(!validarInputNombre(input, valor)) isValid = false
        }
        else if (llave === "email"){
            if(!validarInputEmail(input, valor)) isValid = false
        }
        else if (llave === "telefono"){
            if(!validarInputTelefono(input, valor)) isValid = false
        }
        else if (llave === "mensaje"){
            if(!validarInputMensaje(input, valor)) isValid = false
        }
    }
    return isValid
}

// Validaciones propias para cada campo
// validar input nombre
function validarInputNombre(input, valor){
   const patron = /^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$/
    if(valor.length >= 2 && valor.length <= 100){
        if (!patron.test(valor)){
            textErrorInput(input, "El nombre no es válido")
            return false
        }
    }else{
        textErrorInput(input, "Nombre: de 2 a 100 caracteres")
        return false
    }
    return true
}

// Validar input email
function validarInputEmail(input, valor){
    const patron = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/ // verifica si es un email valido
    if(valor.length >= 6 && valor.length <= 254){
        if (!patron.test(valor)){
            textErrorInput(input, "El email no es válido")
            return false
        }
    }else{
        textErrorInput(input, "Email: de 6 a 254 caracteres")
        return false
    }
    return true
}

//validar input telefono
function validarInputTelefono(input, valor){
    const patron = /^\+?[0-9\s-]{6,25}$/ // verifica si es un celular valido
    if(valor.length >= 6 && valor.length <= 25){
        if (!patron.test(valor)){
            textErrorInput(input, "El celular no es válido")
            return false
        }
    }else{
        textErrorInput(input, "Celular: de 6 a 25 caracteres")
        return false
    }
    return true
}

// validar input mensaje
function validarInputMensaje(input, valor){
    if(valor.length < 2 || valor.length > 1000){
        textErrorInput(input, "Mensaje: de 2 a 1000 caracteres")
        return false
    }
    return true
}

export function textErrorInput(input, msj){
    const errorText = document.getElementById(input.name + "-error")
    input.classList.add("is-invalid")
    if ( errorText ){
        errorText.textContent = msj
        errorText.classList.add("fw-bold")
    }
}

export function clearErrorText(input){
    const errorText = document.getElementById(input.name + "-error")
    input.classList.remove("is-invalid")
    if ( errorText ){
        errorText.textContent = ""
    }
}