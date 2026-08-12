document.addEventListener('DOMContentLoaded', () => {
    const escritorio = window.matchMedia('(min-width: 992px)')

    document.querySelectorAll('.fila-categorias').forEach((fila) => {
        const botones = [...document.querySelectorAll(`[data-fila="${fila.id}"]`)]
        if (!botones.length) return

        const paso = () => {
            const primera = fila.firstElementChild
            if (!primera) return 0
            const gap = parseFloat(getComputedStyle(fila).columnGap) || 0
            return primera.offsetWidth + gap
        }

        const maxScroll = () => fila.scrollWidth - fila.clientWidth

        const actualizarEstado = () => {
            const alInicio = fila.scrollLeft <= 1
            const alFinal = fila.scrollLeft >= maxScroll() - 1
            botones.forEach((boton) => {
                const direccion = Number(boton.dataset.direccion)
                boton.hidden = direccion < 0 ? alInicio : alFinal
            })
        }

        botones.forEach((boton) => {
            boton.addEventListener('click', () => {
                if (!escritorio.matches) return
                const indiceActual = Math.round(fila.scrollLeft / paso())
                const indiceDestino = indiceActual + (Number(boton.dataset.direccion) || 1)
                const destino = Math.max(0, Math.min(indiceDestino * paso(), maxScroll()))
                fila.scrollTo({ left: destino, behavior: 'smooth' })
            })
        })

        fila.addEventListener('scroll', actualizarEstado)

        window.addEventListener('resize', () => {
            if (escritorio.matches) {
                const indice = Math.round(fila.scrollLeft / paso())
                fila.scrollLeft = Math.max(0, Math.min(indice * paso(), maxScroll()))
            }
            actualizarEstado()
        })

        actualizarEstado()
    })
})
