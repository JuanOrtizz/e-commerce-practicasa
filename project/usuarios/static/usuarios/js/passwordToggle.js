const ETIQUETA_MOSTRAR = 'Mostrar contraseña'
const ETIQUETA_OCULTAR = 'Ocultar contraseña'

document.addEventListener('click', (evento) => {
    const boton = evento.target.closest('[data-password-toggle]')
    if (!boton) return

    const input = document.getElementById(boton.getAttribute('aria-controls'))
    if (!input) return

    const mostrar = input.type === 'password'
    input.type = mostrar ? 'text' : 'password'
    boton.setAttribute('aria-pressed', String(mostrar))
    boton.setAttribute('aria-label', mostrar ? ETIQUETA_OCULTAR : ETIQUETA_MOSTRAR)
})
