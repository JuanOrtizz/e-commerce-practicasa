const form = document.querySelector('form[role="search"]');
const input = form?.querySelector('input[name="search"]');

if (!form || !input) {
    const observer = new MutationObserver(() => {
        const f = document.querySelector('form[role="search"]')
        if (f) {
            observer.disconnect()
            inicializar(f)
        }
    })
    observer.observe(document.body, { childList: true, subtree: true })
} else {
    inicializar(form)
}

function inicializar(form) {
    const input = form.querySelector('input[name="search"]')
    const dropdown = document.createElement('div')
    dropdown.className = 'dropdown-search position-absolute top-100 start-0 w-100 bg-white border rounded-3 shadow-lg overflow-hidden z-3 d-none'
    const wrapper = form.querySelector('.position-relative');
    (wrapper || form).appendChild(dropdown)

    let timeoutId = null
    let selectedIndex = -1
    let resultados = []

    input.addEventListener('input', () => {
        clearTimeout(timeoutId)
        const q = input.value.trim()
        if (q.length < 2) {
            dropdown.classList.add('d-none')
            selectedIndex = -1
            return
        }
        timeoutId = setTimeout(() => fetchResultados(q), 300)
    })

    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            selectedIndex = Math.min(selectedIndex + 1, resultados.length - 1)
            resaltar()
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            selectedIndex = Math.max(selectedIndex - 1, -1)
            resaltar()
        } else if (e.key === 'Enter') {
            if (selectedIndex >= 0 && resultados[selectedIndex]) {
                e.preventDefault()
                const r = resultados[selectedIndex]
                window.location.href = `/productos/${r.url}/${r.url_subcategoria}/${r.slug}/`
            }
        } else if (e.key === 'Escape') {
            dropdown.classList.add('d-none')
            input.blur()
        }
    })

    document.addEventListener('click', (e) => {
        if (!form.contains(e.target)) {
            dropdown.classList.add('d-none')
        }
    })

    async function fetchResultados(q) {
        try {
            const res = await fetch(`/productos/search/json/?search=${encodeURIComponent(q)}`)
            resultados = await res.json()
            renderDropdown(resultados)
        } catch {
            dropdown.classList.add('d-none')
        }
    }

    function renderDropdown(items){
        dropdown.innerHTML = ''
        selectedIndex = -1

        if (items.length === 0) {
            dropdown.classList.add('d-none')
            return
        }

        const list = document.createElement('div')
        items.forEach((item, i) => {
            const a = document.createElement('a')
            a.href = `/productos/${item.url}/${item.url_subcategoria}/${item.slug}/`
            a.className = 'd-flex align-items-center gap-3 px-3 py-2 text-decoration-none text-dark dropdown-item-search border-bottom'
            a.style.cursor = 'pointer'

            const img = document.createElement('img')
            img.src = item.imagen_url || '/static/productos/img/logo_default_practicasa.webp'
            img.alt = item.nombre
            img.style.width = '45px'
            img.style.height = '45px'
            img.style.objectFit = 'cover'
            img.className = 'rounded'
            img.loading = 'lazy'

            const info = document.createElement('div')
            info.className = 'd-flex flex-column'
            info.innerHTML = `
                <span class="fw-semibold small">${item.nombre}</span>
                <span class="text-success fw-bold small">$${item.precio_transferencia}</span>
            `

            a.appendChild(img)
            a.appendChild(info)

            a.addEventListener('mouseenter', () => {
                selectedIndex = i
                resaltar()
            })

            a.addEventListener('click', () => {
                dropdown.classList.add('d-none')
            })

            list.appendChild(a)
        })

        dropdown.appendChild(list);
        dropdown.classList.remove('d-none')
    }

    function resaltar() {
        const items = dropdown.querySelectorAll('.dropdown-item-search')
        items.forEach((el, i) => {
            el.classList.toggle('bg-light', i === selectedIndex)
        })
        if (selectedIndex >= 0 && items[selectedIndex]) {
            items[selectedIndex].scrollIntoView({ block: 'nearest' })
        }
    }
}
