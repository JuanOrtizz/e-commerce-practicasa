const DEFAULT_IMG = '/static/productos/img/logo_default_practicasa.webp'

document.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG' && e.target.closest('.card')) {
        e.target.src = DEFAULT_IMG
    }
}, true)

const form = document.getElementById('form-filtros')
const precioMin = form.querySelector('[name=precio_min]')
const precioMax = form.querySelector('[name=precio_max]')

precioMin.addEventListener('input', () => {
    if (precioMin.value < 0) precioMin.value = 0
})

precioMax.addEventListener('input', () => {
    if (precioMax.value < 0) precioMax.value = 0
})

form.querySelector('.btn-enviar.btn-sm').addEventListener('click', () => {
    form.submit()
})
