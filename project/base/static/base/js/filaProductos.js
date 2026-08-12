document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-flecha-fila').forEach((boton) => {
        boton.addEventListener('click', () => {
            const fila = document.getElementById(boton.dataset.fila)
            if (!fila) return
            const direccion = Number(boton.dataset.direccion) || 1
            const anchoCard = fila.firstElementChild ? fila.firstElementChild.offsetWidth : 280
            fila.scrollBy({ left: direccion * anchoCard, behavior: 'smooth' })
        })
    })
})
