// funcion para generar alerta de exito
export function successAlertRedirect(text, href){
    Swal.fire({
        title: `${text}`,
        icon: "success",
        iconColor: '#12A116',
        showCancelButton: true,
        confirmButtonText: "Ir",
        confirmButtonColor: '#3366CC',
        cancelButtonText: "Cerrar",
        cancelButtonColor: '#FF0000',
        willOpen: () => {
            const title = document.querySelector('.swal2-title')
            title.style.fontSize = '1rem'
            title.style.fontFamily = '"Nunito Sans", sans-serif'
        },
        didOpen: () =>{ // agrego esto ya que sino recalcula con esta clase y sube el footer para evitar scroll
            document.body.classList.remove('swal2-height-auto')
            document.body.style.overflow = 'auto'
            document.body.style.paddingRight = '0'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = href
        }
    })
}

// funcion para generar alerta de error
export function errorAlert(text){
    Swal.fire({
        title: `${text}`,
        icon: "error",
        iconColor: '#FF0000',
        confirmButtonText: "Cerrar",
        confirmButtonColor: '#000000',
        willOpen: () => {
            const title = document.querySelector('.swal2-title')
            title.style.fontSize = '1rem'
            title.style.fontFamily = '"Nunito Sans", sans-serif'
        },
        didOpen: () =>{ // agrego esto ya que sino recalcula con esta clase y sube el footer para evitar scroll
            document.body.classList.remove('swal2-height-auto')
            document.body.style.overflow = 'auto'
            document.body.style.paddingRight = '0'
        }
    })
}

export function successAlert(title, text){
    Swal.fire({
        title: `${title}`,
        text: `${text}`,
        icon: "success",
        iconColor: '#12A116',
        confirmButtonText: "Cerrar",
        confirmButtonColor: '#000000',
        willOpen: () => {
            const title = document.querySelector('.swal2-title')
            title.style.fontSize = '1rem'
            title.style.fontFamily = '"Nunito Sans", sans-serif'
        },
        didOpen: () =>{ // agrego esto ya que sino recalcula con esta clase y sube el footer para evitar scroll
            document.body.classList.remove('swal2-height-auto')
            document.body.style.overflow = 'auto'
            document.body.style.paddingRight = '0'
        }
    })
}

export function confirmAlert(text, action, callback){ // funcion para generar alerta de confirmacion
    Swal.fire({
        title: `${text}`,
        text: "No podrás revertir esto",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: '#3366CC',
        cancelButtonText: "Cerrar",
        cancelButtonColor: '#FF0000',
        confirmButtonText: `Sí`,
        didOpen: () =>{ // agrego esto ya que sino recalcula con esta clase y sube el footer para evitar scroll
            document.body.classList.remove('swal2-height-auto')
            document.body.style.overflow = 'auto'
            document.body.style.paddingRight = '0'
        }
    }).then(async (result) => {
        if (result.isConfirmed) {
            await callback()
        }
    })
}