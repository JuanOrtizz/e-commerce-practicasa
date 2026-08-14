document.addEventListener('DOMContentLoaded', () => {
    const filtro = document.getElementById('filtro-consultas')
    const orden = document.getElementById('orden-consultas')
    const contador = document.getElementById('consultas-count')
    const mensaje = document.getElementById('no-consultas-message')
    const filas = Array.from(document.querySelectorAll('.consulta-item'))

    if (!filtro || !orden) return

    function cumpleFiltro(fila) {
        return filtro.value === 'todas' || fila.dataset.estado === filtro.value
    }

    function aplicar() {
        const visibles = filas.filter(fila => fila.isConnected && cumpleFiltro(fila))
        visibles.sort((a, b) => {
            const fechaA = a.dataset.fecha
            const fechaB = b.dataset.fecha
            return orden.value === 'antiguas' ? fechaA.localeCompare(fechaB) : fechaB.localeCompare(fechaA)
        })
        filas.forEach(fila => fila.classList.toggle('d-none', !visibles.includes(fila)))
        visibles.forEach(fila => fila.parentElement.appendChild(fila))
        if (contador) contador.textContent = visibles.length
        if (mensaje) mensaje.classList.toggle('d-none', visibles.length > 0)
    }

    filtro.addEventListener('change', aplicar)
    orden.addEventListener('change', aplicar)
    aplicar()
})
