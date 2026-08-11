// funcion para validar el formulario
export function validateForm(formData){
    let isValid = true // al comienzo siempre va a ser valido

    // capturo el formulario para limpiar los errores anteriores
    const form = document.getElementById("form")
    form.querySelectorAll(".is-invalid").forEach(el => {
        clearErrorText(el)
    })

    const obligatorios = ["subcategoria", "nombre", "descripcion", "sku", "precio", "precio_transferencia", "stock"]
    const opcionales = ["peso", "promocion"]

    // recorre cada input del formulario y realiza las validaciones con sus metodos
    for(let [llave, valor] of formData.entries()){
        if(!obligatorios.includes(llave) && !opcionales.includes(llave)){
            continue    // ignora checkboxes, formset de imágenes
        }

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
            if(opcionales.includes(llave)) continue
            textErrorInput(input, llave === "subcategoria" ? "Seleccioná una subcategoría" : "El campo está vacío")
            isValid = false
        }
        else if (llave === "nombre"){
            if(!validarInputNombre(input, valor)) isValid = false
        }
        else if (llave === "descripcion"){
            if(!validarInputDescripcion(input, valor)) isValid = false
        }
        else if (llave === "sku"){
            if(!validarInputSku(input, valor)) isValid = false
        }
        else if (llave === "precio"){
            if(!validarInputPrecio(input, valor)) isValid = false
        }
        else if (llave === "precio_transferencia"){
            if(!validarInputPrecioTransferencia(input, valor)) isValid = false
        }
        else if (llave === "stock"){
            if(!validarInputStock(input, valor)) isValid = false
        }
        else if (llave === "peso"){
            if(!validarInputPeso(input, valor)) isValid = false
        }
    }
    return isValid
}

// Validaciones propias para cada campo
// validar input nombre producto
function validarInputNombre(input, valor){
    if(valor.length < 2 || valor.length > 200){
        textErrorInput(input, "Nombre: de 2 a 200 caracteres")
        return false
    }
    return true
}

function validarInputDescripcion(input, valor){
    if(valor.length < 2 || valor.length > 1000){
        textErrorInput(input, "Descripción: de 2 a 1000 caracteres")
        return false
    }
    return true
}

function validarInputSku(input, valor){
    if(valor.length < 2 || valor.length > 50){
        textErrorInput(input, "Sku: de 2 a 50 caracteres")
        return false
    }
    return true
}

function validarInputPrecio(input, valor){
    if(parseFloat(valor) <= 0){
        textErrorInput(input, "El precio de transferencia debe ser mayor a 0")
        return false
    }
    else if(parseFloat(valor) > 99999999.99){
        textErrorInput(input, "El precio no puede ser mayor a 99999999.99")
        return false
    }
    return true
}

function validarInputPrecioTransferencia(input, valor){
    const precioInput = document.getElementById("id_precio")
    if(parseFloat(valor) <= 0){
        textErrorInput(input, "El precio de transferencia debe ser mayor a 0")
        return false
    }
    else if(parseFloat(valor) > 99999999.99){
        textErrorInput(input, "El precio de transferencia no puede ser mayor a 99999999.99")
        return false
    }
    else if(parseFloat(valor) > parseFloat(precioInput.value)){
        textErrorInput(input, "El precio de transferencia no puede ser mayor al precio normal")
        return false
    }
    return true
}

function validarInputStock(input, valor){
    if(parseInt(valor) < 0){
        textErrorInput(input, "El stock no puede ser negativo")
        return false
    }
    return true
}

function validarInputPeso(input, valor){
    if(parseFloat(valor) <= 0){
        textErrorInput(input, "El peso debe ser mayor a 0")
        return false
    }
    else if(parseFloat(valor) > 9999.99){
        textErrorInput(input, "El peso no puede ser mayor a 9999.99")
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