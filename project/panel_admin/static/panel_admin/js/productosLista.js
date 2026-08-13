document.addEventListener('DOMContentLoaded', () => {
    const buscador = document.getElementById('buscador-productos')
    const filtro = document.getElementById('filtro-productos')
    const orden = document.getElementById('orden-productos')
    const contador = document.getElementById('productos-count')
    const mensaje = document.getElementById('no-productos-message')
    const filas = Array.from(document.querySelectorAll('.producto-item'))

    if (!buscador || !filtro || !orden) return

    function nombreProducto(fila) {
        const celda = fila.querySelector('td.fw-bold')
        return celda ? celda.textContent.trim() : ''
    }

    function esActivo(fila) {
        return fila.querySelector('.badge-estado-activo') !== null
    }

    function cumpleBusqueda(fila) {
        return nombreProducto(fila).toLowerCase().includes(buscador.value.trim().toLowerCase())
    }

    function cumpleFiltro(fila) {
        switch (filtro.value) {
            case 'sin-stock':
                return fila.querySelector('.badge-stock-sin') !== null
            case 'bajo-stock':
                return fila.querySelector('.badge-stock-bajo') !== null
            case 'activos':
                return esActivo(fila)
            case 'inactivos':
                return !esActivo(fila)
            default:
                return true
        }
    }

    function aplicar() {
        let visibles = filas.filter(fila => fila.isConnected && cumpleBusqueda(fila) && cumpleFiltro(fila))
        if (orden.value === 'az' || orden.value === 'za') {
            visibles.sort((a, b) => {
                const nombreA = nombreProducto(a)
                const nombreB = nombreProducto(b)
                return orden.value === 'az' ? nombreA.localeCompare(nombreB, 'es') : nombreB.localeCompare(nombreA, 'es')
            })
        }
        filas.forEach(fila => fila.classList.toggle('d-none', !visibles.includes(fila)))
        visibles.forEach(fila => fila.parentElement.appendChild(fila))
        if (contador) contador.textContent = visibles.length
        if (mensaje) mensaje.classList.toggle('d-none', visibles.length > 0)
    }

    buscador.addEventListener('input', aplicar)
    filtro.addEventListener('change', aplicar)
    orden.addEventListener('change', aplicar)
    aplicar()
})
