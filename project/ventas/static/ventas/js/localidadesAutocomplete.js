const MAX_RESULTADOS = 50

let indicePromise = null

function normalizar(texto) {
    return texto
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
}

function cargarIndice(url) {
    if (!indicePromise) {
        indicePromise = fetch(url)
            .then((respuesta) => {
                if (!respuesta.ok) {
                    throw new Error('No se pudieron cargar las localidades')
                }
                return respuesta.json()
            })
            .then((datos) => {
                const provincias = (datos.provincias || []).map((nombre) => ({
                    nombre,
                    normalizado: normalizar(nombre),
                }))
                const localidades = []
                for (const [provincia, nombres] of Object.entries(datos.localidades || {})) {
                    for (const nombre of nombres) {
                        localidades.push({
                            nombre,
                            provincia,
                            normalizado: normalizar(nombre),
                        })
                    }
                }
                return { provincias, localidades }
            })
            .catch(() => null)
    }
    return indicePromise
}

function filtrarProvincias(indice, consulta) {
    const busqueda = normalizar(consulta)
    if (!busqueda) {
        return indice.provincias
            .slice()
            .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
            .slice(0, MAX_RESULTADOS)
            .map((provincia) => ({ nombre: provincia.nombre, valor: provincia.nombre }))
    }
    return indice.provincias
        .filter((provincia) => provincia.normalizado.includes(busqueda))
        .sort((a, b) => Number(b.normalizado.startsWith(busqueda)) - Number(a.normalizado.startsWith(busqueda)))
        .slice(0, MAX_RESULTADOS)
        .map((provincia) => ({ nombre: provincia.nombre, valor: provincia.nombre }))
}

export async function esLocalidadValida(provincia, ciudad) {
    const form = document.getElementById('form')
    const url = form?.dataset.localidadesUrl
    if (!url) {
        return true
    }
    const indice = await cargarIndice(url)
    if (!indice) {
        return true
    }
    const provinciaNombre = provinciaConocida(indice, provincia)
    if (!provinciaNombre) {
        return false
    }
    return indice.localidades.some(
        (localidad) => localidad.provincia === provinciaNombre && localidad.nombre === ciudad
    )
}

export async function esProvinciaValida(provincia) {
    const form = document.getElementById('form')
    const url = form?.dataset.localidadesUrl
    if (!url) {
        return true
    }
    const indice = await cargarIndice(url)
    if (!indice) {
        return true
    }
    return indice.provincias.some((item) => item.nombre === provincia)
}

function provinciaConocida(indice, valor) {
    const busqueda = normalizar(valor)
    if (!busqueda) {
        return null
    }
    return indice.provincias.find((provincia) => provincia.normalizado === busqueda)?.nombre || null
}

function filtrarCiudades(indice, provinciaValor, consulta) {
    const provincia = provinciaConocida(indice, provinciaValor)
    if (!provincia) {
        return []
    }
    const busqueda = normalizar(consulta)
    const localidades = indice.localidades.filter(
        (localidad) => localidad.provincia === provincia
    )
    if (!busqueda) {
        return localidades
            .slice()
            .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
            .slice(0, MAX_RESULTADOS)
            .map((localidad) => ({ nombre: localidad.nombre, valor: localidad.nombre }))
    }
    return localidades
        .filter((localidad) => localidad.normalizado.includes(busqueda))
        .sort((a, b) => Number(b.normalizado.startsWith(busqueda)) - Number(a.normalizado.startsWith(busqueda)))
        .slice(0, MAX_RESULTADOS)
        .map((localidad) => ({ nombre: localidad.nombre, valor: localidad.nombre }))
}

function crearCombobox(input, obtenerOpciones) {
    const contenedor = input.closest('.form-floating') || input.parentElement
    const idLista = `${input.id}-lista`
    contenedor.classList.add('localidad-combobox')
    const chevron = document.createElement('span')
    chevron.className = 'material-symbols-outlined localidad-chevron'
    chevron.textContent = 'expand_more'
    chevron.setAttribute('aria-hidden', 'true')
    contenedor.appendChild(chevron)
    const lista = document.createElement('div')
    lista.id = idLista
    lista.className = 'localidad-dropdown d-none'
    lista.setAttribute('role', 'listbox')
    contenedor.appendChild(lista)

    input.setAttribute('role', 'combobox')
    input.setAttribute('aria-autocomplete', 'list')
    input.setAttribute('aria-expanded', 'false')
    input.setAttribute('aria-controls', idLista)

    let opciones = []
    let activo = -1
    let suprimirEntrada = false

    function cerrar() {
        lista.classList.add('d-none')
        contenedor.classList.remove('localidad-abierto')
        lista.replaceChildren()
        input.setAttribute('aria-expanded', 'false')
        input.removeAttribute('aria-activedescendant')
        opciones = []
        activo = -1
    }

    function resaltar() {
        const items = lista.querySelectorAll('[role="option"]')
        items.forEach((item, indice) => {
            const seleccionado = indice === activo
            item.classList.toggle('localidad-opcion-activa', seleccionado)
            item.setAttribute('aria-selected', String(seleccionado))
        })
        if (activo >= 0 && items[activo]) {
            input.setAttribute('aria-activedescendant', items[activo].id)
            items[activo].scrollIntoView({ block: 'nearest' })
        } else {
            input.removeAttribute('aria-activedescendant')
        }
    }

    function seleccionar(indice) {
        const opcion = opciones[indice]
        if (!opcion) {
            return
        }
        suprimirEntrada = true
        input.value = opcion.valor
        input.dispatchEvent(new Event('input', { bubbles: true }))
        input.dispatchEvent(new Event('change', { bubbles: true }))
        suprimirEntrada = false
        cerrar()
    }

    function renderizar() {
        lista.replaceChildren()
        activo = -1
        if (!opciones.length) {
            cerrar()
            return
        }
        opciones.forEach((opcion, indice) => {
            const item = document.createElement('div')
            item.id = `${idLista}-${indice}`
            item.className = 'localidad-opcion'
            item.setAttribute('role', 'option')
            item.setAttribute('aria-selected', 'false')

            const nombre = document.createElement('span')
            nombre.className = 'localidad-opcion-nombre'
            nombre.textContent = opcion.nombre
            item.appendChild(nombre)

            item.addEventListener('mousedown', (evento) => {
                evento.preventDefault()
            })
            item.addEventListener('click', () => {
                seleccionar(indice)
            })

            lista.appendChild(item)
        })
        lista.classList.remove('d-none')
        contenedor.classList.add('localidad-abierto')
        input.setAttribute('aria-expanded', 'true')
    }

    function buscar(consulta = input.value) {
        opciones = obtenerOpciones(consulta)
        renderizar()
    }

    input.addEventListener('input', () => {
        if (suprimirEntrada) {
            return
        }
        buscar()
    })

    input.addEventListener('focus', () => {
        buscar()
    })

    chevron.addEventListener('mousedown', (evento) => {
        evento.preventDefault()
    })

    chevron.addEventListener('click', () => {
        const abierto = !lista.classList.contains('d-none')
        input.focus()
        if (abierto) {
            cerrar()
            return
        }
        buscar('')
    })

    input.addEventListener('blur', () => {
        setTimeout(() => {
            if (document.activeElement !== input) {
                cerrar()
            }
        }, 150)
    })

    input.addEventListener('keydown', (evento) => {
        if (evento.key === 'ArrowDown') {
            evento.preventDefault()
            if (lista.classList.contains('d-none')) {
                buscar()
                activo = opciones.length ? 0 : -1
                resaltar()
                return
            }
            activo = Math.min(activo + 1, opciones.length - 1)
            resaltar()
        } else if (evento.key === 'ArrowUp') {
            if (lista.classList.contains('d-none')) {
                return
            }
            evento.preventDefault()
            activo = Math.max(activo - 1, 0)
            resaltar()
        } else if (evento.key === 'Enter') {
            if (activo >= 0 && opciones[activo]) {
                evento.preventDefault()
                seleccionar(activo)
            }
        } else if (evento.key === 'Escape') {
            if (!lista.classList.contains('d-none')) {
                evento.preventDefault()
                cerrar()
            }
        } else if (evento.key === 'Tab') {
            cerrar()
        }
    })

    document.addEventListener('click', (evento) => {
        if (!contenedor.contains(evento.target)) {
            cerrar()
        }
    })

    return {
        cerrar,
        refrescar() {
            if (!lista.classList.contains('d-none')) {
                buscar()
            }
        },
    }
}

function inicializar() {
    const form = document.getElementById('form')
    const provinciaInput = document.querySelector('[data-autocompletar="provincia"]')
    const ciudadInput = document.querySelector('[data-autocompletar="ciudad"]')
    const url = form?.dataset.localidadesUrl

    if (!form || !provinciaInput || !ciudadInput || !url) {
        return
    }

    cargarIndice(url).then((indice) => {
        if (!indice) {
            return
        }

        crearCombobox(provinciaInput, (consulta) => filtrarProvincias(indice, consulta))
        const ciudad = crearCombobox(ciudadInput, (consulta) => filtrarCiudades(indice, provinciaInput.value, consulta))

        provinciaInput.addEventListener('input', () => ciudad.refrescar())
        provinciaInput.addEventListener('change', () => {
            ciudadInput.value = ''
            ciudad.refrescar()
        })
    })
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar)
} else {
    inicializar()
}
