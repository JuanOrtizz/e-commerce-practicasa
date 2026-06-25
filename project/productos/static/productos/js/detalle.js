const DEFAULT_IMG = '/static/productos/img/logo_default_practicasa.webp'

document.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG' && e.target.closest('#producto-imagenes')) {
        e.target.src = DEFAULT_IMG
    }
}, true)

document.getElementById('producto-imagenes').addEventListener('mouseover', (e) => {
    const thumbnail = e.target.closest('.img-thumbnail')
    if (thumbnail) {
        document.getElementById('imagenPrincipal').src = thumbnail.src
    }
})
