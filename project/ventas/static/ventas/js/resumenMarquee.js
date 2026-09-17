const nombreDesborda = (nombre, track) => {
    const previo = nombre.style.whiteSpace
    nombre.style.whiteSpace = 'nowrap'
    const anchoTexto = track.getBoundingClientRect().width
    const anchoVisible = nombre.getBoundingClientRect().width
    nombre.style.whiteSpace = previo
    return anchoTexto > anchoVisible + 1
}

const activarMarquee = (nombre) => {
    const track = nombre.querySelector('.ventas-resumen-item-nombre-track')
    if (!track) {
        return
    }
    if (nombreDesborda(nombre, track)) {
        nombre.classList.add('ventas-resumen-item-nombre--marquee')
        if (!track.dataset.clonado) {
            const clon = track.children[0].cloneNode(true)
            clon.setAttribute('aria-hidden', 'true')
            track.appendChild(clon)
            track.dataset.clonado = 'true'
        }
    } else {
        nombre.classList.remove('ventas-resumen-item-nombre--marquee')
        delete track.dataset.clonado
        track.querySelectorAll('[aria-hidden="true"]').forEach((nodo) => nodo.remove())
    }
}

const inicializarMarquee = () => {
    document.querySelectorAll('.ventas-resumen-item-nombre').forEach(activarMarquee)
}

document.addEventListener('DOMContentLoaded', inicializarMarquee)
window.addEventListener('load', inicializarMarquee)
window.addEventListener('resize', inicializarMarquee)