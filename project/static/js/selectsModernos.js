const CLASE_ABIERTO = 'select-moderno-abierto'
const CLASE_ARRIBA = 'select-moderno-arriba'
const CLASE_ACTIVA = 'is-activa'
const CLASE_SELECCIONADA = 'is-seleccionada'

function inicializarSelects() {
    document.querySelectorAll('select').forEach(crearSelectModerno)
}

function crearSelectModerno(select) {
    if (select.dataset.selectModerno === 'listo') return
    if (select.closest('.select-moderno')) return
    if (select.multiple || select.size > 1) return

    const etiqueta = select.id
        ? document.querySelector(`label[for="${CSS.escape(select.id)}"]`)
        : null

    const contenedor = document.createElement('div')
    contenedor.className = 'select-moderno'
    if (select.classList.contains('w-auto')) contenedor.classList.add('select-moderno-auto')
    if (select.classList.contains('form-select-sm')) contenedor.classList.add('select-moderno-sm')

    select.parentNode.insertBefore(contenedor, select)
    contenedor.appendChild(select)

    select.dataset.selectModerno = 'listo'
    select.classList.add('select-moderno-nativo')
    select.tabIndex = -1
    select.setAttribute('aria-hidden', 'true')

    const boton = document.createElement('button')
    boton.type = 'button'
    boton.className = 'select-moderno-boton'
    boton.setAttribute('aria-haspopup', 'listbox')
    boton.setAttribute('aria-expanded', 'false')
    if (select.id) boton.id = `${select.id}-boton`

    const ariaLabel = select.getAttribute('aria-label') || etiqueta?.textContent.trim()
    if (ariaLabel) boton.setAttribute('aria-label', ariaLabel)

    const texto = document.createElement('span')
    texto.className = 'select-moderno-texto'

    const chevron = document.createElement('span')
    chevron.className = 'material-symbols-outlined select-moderno-chevron'
    chevron.setAttribute('aria-hidden', 'true')
    chevron.textContent = 'expand_more'

    boton.append(texto, chevron)

    const lista = document.createElement('div')
    lista.className = 'select-moderno-lista d-none'
    lista.setAttribute('role', 'listbox')
    if (select.id) {
        lista.id = `${select.id}-lista`
        boton.setAttribute('aria-controls', lista.id)
    }

    contenedor.append(boton, lista)

    let activo = -1
    let abierto = false

    function actualizarTexto() {
        const opcion = select.options[select.selectedIndex]
        texto.textContent = opcion ? opcion.label : ''
        boton.disabled = select.disabled
        boton.classList.toggle('is-disabled', select.disabled)
    }

    function crearItem(opcion, indice) {
        const item = document.createElement('button')
        item.type = 'button'
        item.className = 'select-moderno-opcion'
        item.setAttribute('role', 'option')
        item.setAttribute('aria-selected', String(indice === select.selectedIndex))
        item.tabIndex = -1
        item.dataset.indice = String(indice)
        item.textContent = opcion.label
        item.disabled = opcion.disabled
        if (select.id) item.id = `${lista.id}-${indice}`
        if (indice === select.selectedIndex) item.classList.add(CLASE_SELECCIONADA)
        item.addEventListener('mouseenter', () => marcarActivo(indice))
        item.addEventListener('click', () => seleccionar(indice))
        return item
    }

    function construirLista() {
        lista.replaceChildren()
        Array.from(select.options).forEach((opcion, indice) => {
            if (opcion.hidden) return
            lista.appendChild(crearItem(opcion, indice))
        })
    }

    function marcarActivo(indice) {
        activo = indice
        lista.querySelectorAll('.select-moderno-opcion').forEach(item => {
            item.classList.toggle(CLASE_ACTIVA, Number(item.dataset.indice) === indice)
        })
        const item = lista.querySelector(`[data-indice="${indice}"]`)
        if (!item) return
        if (item.id) boton.setAttribute('aria-activedescendant', item.id)
        item.scrollIntoView({ block: 'nearest' })
    }

    function moverActivo(direccion) {
        const total = select.options.length
        if (!total) return
        let indice = activo
        for (let paso = 0; paso < total; paso += 1) {
            indice = (indice + direccion + total) % total
            const opcion = select.options[indice]
            if (!opcion.disabled && !opcion.hidden) break
        }
        marcarActivo(indice)
    }

    function ajustarPosicion() {
        const rect = contenedor.getBoundingClientRect()
        const espacioAbajo = window.innerHeight - rect.bottom
        contenedor.classList.toggle(
            CLASE_ARRIBA,
            espacioAbajo < 220 && rect.top > espacioAbajo
        )
    }

    function abrir() {
        if (abierto || boton.disabled) return
        construirLista()
        if (!lista.children.length) return
        lista.classList.remove('d-none')
        contenedor.classList.add(CLASE_ABIERTO)
        boton.setAttribute('aria-expanded', 'true')
        abierto = true
        ajustarPosicion()
        marcarActivo(select.selectedIndex >= 0 ? select.selectedIndex : 0)
    }

    function cerrar() {
        if (!abierto) return
        lista.classList.add('d-none')
        contenedor.classList.remove(CLASE_ABIERTO, CLASE_ARRIBA)
        boton.setAttribute('aria-expanded', 'false')
        boton.removeAttribute('aria-activedescendant')
        activo = -1
        abierto = false
    }

    function seleccionar(indice) {
        const opcion = select.options[indice]
        if (!opcion || opcion.disabled) return
        select.selectedIndex = indice
        actualizarTexto()
        cerrar()
        boton.focus()
        select.dispatchEvent(new Event('input', { bubbles: true }))
        select.dispatchEvent(new Event('change', { bubbles: true }))
    }

    boton.addEventListener('click', () => {
        if (abierto) {
            cerrar()
        } else {
            abrir()
        }
    })

    boton.addEventListener('keydown', evento => {
        if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
            evento.preventDefault()
            if (!abierto) {
                abrir()
                return
            }
            moverActivo(evento.key === 'ArrowDown' ? 1 : -1)
        } else if (evento.key === 'Enter' || evento.key === ' ') {
            evento.preventDefault()
            if (abierto && activo >= 0) {
                seleccionar(activo)
            } else {
                abrir()
            }
        } else if (evento.key === 'Escape') {
            evento.preventDefault()
            cerrar()
        } else if (evento.key === 'Tab') {
            cerrar()
        }
    })

    etiqueta?.addEventListener('click', evento => {
        if (evento.target.closest('a, button')) return
        evento.preventDefault()
        if (abierto) {
            cerrar()
        } else {
            abrir()
            boton.focus()
        }
    })

    select.addEventListener('change', actualizarTexto)
    select.form?.addEventListener('reset', () => setTimeout(actualizarTexto, 0))

    new MutationObserver(actualizarTexto).observe(select, {
        attributes: true,
        attributeFilter: ['disabled'],
    })

    document.addEventListener('click', evento => {
        if (!abierto) return
        if (contenedor.contains(evento.target)) return
        if (etiqueta?.contains(evento.target)) return
        cerrar()
    })
    window.addEventListener('resize', () => cerrar())

    actualizarTexto()
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarSelects)
} else {
    inicializarSelects()
}
