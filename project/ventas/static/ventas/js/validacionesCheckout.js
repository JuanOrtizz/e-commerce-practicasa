export function validateForm(formData){
    let isValid = true

    const form = document.getElementById("form")
    form.querySelectorAll(".is-invalid").forEach(el => {
        clearErrorText(el)
    })

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
        if (llave === "notas"){
            continue
        }
        if(!valor){
            textErrorInput(input, "El campo está vacío")
            isValid = false
        }
        else if (llave === "email"){
            if(!validarInputEmail(input, valor)) isValid = false
        }
        else if (llave === "nombre"){
            if(!validarInputNombre(input, valor)) isValid = false
        }
        else if (llave === "telefono"){
            if(!validarInputTelefono(input, valor)) isValid = false
        }
        else if (llave === "provincia"){
            if(!validarInputProvincia(input, valor)) isValid = false
        }
        else if (llave === "ciudad"){
            if(!validarInputCiudad(input, valor)) isValid = false
        }
        else if (llave === "direccion"){
            if(!validarInputDireccion(input, valor)) isValid = false
        }
        else if (llave === "numero"){
            if(!validarInputNumero(input, valor)) isValid = false
        }
        else if (llave === "codigo_postal"){
            if(!validarInputCodigoPostal(input, valor)) isValid = false
        }
    }
    return isValid
}

function validarInputNombre(input, valor){
    const patron = /^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$/
    if(valor.length >= 2 && valor.length <= 150){
        if (!patron.test(valor)){
            textErrorInput(input, "El nombre no es válido")
            return false
        }
    }else{
        textErrorInput(input, "Nombre: de 2 a 150 caracteres")
        return false
    }
    return true
}

function validarInputEmail(input, valor){
    const patron = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/
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

function validarInputTelefono(input, valor){
    const patron = /^\+?[0-9\s-]{6,25}$/
    if(valor.length >= 6 && valor.length <= 25){
        if (!patron.test(valor)){
            textErrorInput(input, "El teléfono no es válido")
            return false
        }
    }else{
        textErrorInput(input, "Teléfono: de 6 a 25 caracteres")
        return false
    }
    return true
}

function validarInputProvincia(input, valor){
    const patron = /^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$/
    if(valor.length >= 2 && valor.length <= 100){
        if (!patron.test(valor)){
            textErrorInput(input, "La provincia no es válida (solo letras y espacios)")
            return false
        }
    }else{
        textErrorInput(input, "Provincia: de 2 a 100 caracteres")
        return false
    }
    return true
}

function validarInputCiudad(input, valor){
    const patron = /^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$/
    if(valor.length >= 2 && valor.length <= 100){
        if (!patron.test(valor)){
            textErrorInput(input, "La ciudad no es válida (solo letras y espacios)")
            return false
        }
    }else{
        textErrorInput(input, "Ciudad: de 2 a 100 caracteres")
        return false
    }
    return true
}

function validarInputDireccion(input, valor){
    const patron = /^[a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ .\-'º#]+$/
    if(valor.length >= 2 && valor.length <= 100){
        if (!patron.test(valor)){
            textErrorInput(input, "La dirección no es válida")
            return false
        }
    }else{
        textErrorInput(input, "Dirección: de 2 a 100 caracteres")
        return false
    }
    return true
}

function validarInputNumero(input, valor){
    const patron = /^\d+$/
    if(valor.length >= 1 && valor.length <= 6){
        if (!patron.test(valor)){
            textErrorInput(input, "El número no es válido (solo dígitos)")
            return false
        }
    }else{
        textErrorInput(input, "Número: de 1 a 6 dígitos")
        return false
    }
    return true
}

function validarInputCodigoPostal(input, valor){
    const patron = /^\d{4}$/
    if (!patron.test(valor)){
        textErrorInput(input, "El CP debe tener 4 dígitos")
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