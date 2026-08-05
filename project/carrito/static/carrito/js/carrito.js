import {successToast, errorToast, confirmAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value

    document.querySelectorAll('.btn-aumentar').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('.carrito-qty-input')
            const max = parseInt(input.dataset.stock)
            const actual = parseInt(input.value)
            if (actual < max) {
                actualizarCantidad(input, actual + 1, csrfToken)
            }
        })
    })

    document.querySelectorAll('.btn-disminuir').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('.carrito-qty-input')
            const actual = parseInt(input.value)
            if (actual > 1) {
                actualizarCantidad(input, actual - 1, csrfToken)
            }
        })
    })

    document.querySelectorAll('.btn-eliminar-item').forEach(btn => {
        btn.addEventListener('click', () => {
            confirmAlert('¿Eliminar este producto?', 'eliminar', async () => {
                await eliminarItem(btn.dataset.itemId, csrfToken)
            })
        })
    })

    const btnVaciar = document.getElementById('btn-vaciar-carrito')
    if (btnVaciar) {
        btnVaciar.addEventListener('click', () => {
            confirmAlert('¿Vaciar carrito?', 'vaciar', async () => {
                await vaciarCarrito(csrfToken)
            })
        })
    }
})

async function redirigirSiNoAuth(response) {
    if (response.status === 401) {
        const {successAlertRedirect} = await import('/static/js/alertas.js')
        successAlertRedirect("Debés iniciar sesión", `/usuarios/login/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`)
        return true
    }
    return false
}

function mostrarCarga(card) {
    card.classList.add('is-loading')
    document.querySelectorAll('.carrito-qty-btn, .carrito-qty-input, .btn-eliminar-item').forEach(el => el.disabled = true)
    const btnVaciar = document.getElementById('btn-vaciar-carrito')
    if (btnVaciar) btnVaciar.disabled = true
    card.querySelectorAll('.carrito-qty-input').forEach(input => input.classList.add('d-none'))
    card.querySelectorAll('.carrito-qty-spinner').forEach(spinner => spinner.classList.remove('d-none'))
    const overlay = document.querySelector('.carrito-resumen-overlay')
    if (overlay) overlay.classList.remove('d-none')
}

function restaurarControles() {
    document.querySelectorAll('.carrito-item').forEach(card => {
        card.classList.remove('is-loading')
    })
    document.querySelectorAll('.carrito-qty-spinner').forEach(spinner => spinner.classList.add('d-none'))
    document.querySelectorAll('.carrito-qty-input').forEach(input => {
        input.classList.remove('d-none')
        input.disabled = false
    })
    document.querySelectorAll('.btn-eliminar-item').forEach(btn => btn.disabled = false)
    document.querySelectorAll('.carrito-item').forEach(card => {
        const input = card.querySelector('.carrito-qty-input')
        if (!input) return
        const qty = parseInt(input.value)
        const max = parseInt(input.dataset.stock)
        card.querySelectorAll('.btn-disminuir').forEach(btn => btn.disabled = qty <= 1)
        card.querySelectorAll('.btn-aumentar').forEach(btn => btn.disabled = qty >= max)
    })
    const btnVaciar = document.getElementById('btn-vaciar-carrito')
    if (btnVaciar) btnVaciar.disabled = false
    const overlay = document.querySelector('.carrito-resumen-overlay')
    if (overlay) overlay.classList.add('d-none')
}

function actualizarItem(card, item) {
    card.querySelectorAll('.carrito-qty-input').forEach(input => {
        input.value = item.cantidad
        input.dataset.stock = item.stock
        input.max = item.stock
    })
    card.querySelectorAll('.carrito-item-subtotal').forEach(el => {
        el.textContent = `$${item.subtotal}`
    })
    card.querySelectorAll('.carrito-item-subtotal-transferencia').forEach(el => {
        el.textContent = `$${item.subtotal_transferencia}`
    })
    const pagas = card.querySelector('.carrito-item-pagas')
    if (pagas) {
        const promo = pagas.dataset.promo
        const n = item.cantidad_paga
        pagas.textContent = `${promo} — Pagás ${n} unidad${n !== 1 ? 'es' : ''}`
    }
    const ahorroEl = card.querySelector('.carrito-item-ahorro-item')
    if (ahorroEl) {
        if (parseFloat(item.ahorro) > 0) {
            ahorroEl.textContent = ` | Ahorrás $${item.ahorro}`
            ahorroEl.classList.remove('d-none')
        } else {
            ahorroEl.classList.add('d-none')
        }
    }
}

function actualizarResumen(carrito) {
    const set = (sel, val) => {
        const el = document.querySelector(sel)
        if (el) el.textContent = `$${val}`
    }
    set('.carrito-resumen-subtotal', carrito.total)
    set('.carrito-resumen-subtotal-transferencia', carrito.total_transferencia)
    set('.carrito-resumen-total', carrito.total)
    set('.carrito-resumen-total-transferencia', carrito.total_transferencia)
    const ahorroRow = document.querySelector('.carrito-resumen-ahorro')?.closest('.d-flex')
    if (ahorroRow) {
        if (parseFloat(carrito.total_ahorro) > 0) {
            ahorroRow.classList.remove('d-none')
        } else {
            ahorroRow.classList.add('d-none')
        }
        const ahorroEl = ahorroRow.querySelector('.carrito-resumen-ahorro')
        if (ahorroEl) ahorroEl.textContent = `$${carrito.total_ahorro}`
    }
}

function quitarItem(card) {
    card.classList.add('carrito-item-removido')
    setTimeout(() => {
        card.remove()
        if (!document.querySelector('.carrito-item')) {
            location.reload()
        }
    }, 250)
}

async function actualizarCantidad(input, nuevaCantidad, csrfToken) {
    const card = input.closest('.carrito-item')
    mostrarCarga(card)
    try {
        const response = await fetch('/carrito/actualizar/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({item_id: input.dataset.itemId, cantidad: nuevaCantidad})
        })
        if (await redirigirSiNoAuth(response)) return
        const data = await response.json()
        if (data.success) {
            if (data.success.item_eliminado) {
                quitarItem(card)
                actualizarResumen(data.success.carrito)
            } else {
                actualizarItem(card, data.success.item)
                actualizarResumen(data.success.carrito)
            }
        } else {
            errorToast(data.errors || 'Error al actualizar')
        }
    } catch {
        errorToast('Ocurrió un error')
    } finally {
        restaurarControles()
    }
}

async function eliminarItem(itemId, csrfToken) {
    const card = document.querySelector(`.carrito-item[data-item-id="${itemId}"]`)
    mostrarCarga(card)
    try {
        const response = await fetch('/carrito/eliminar/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({item_id: itemId})
        })
        if (await redirigirSiNoAuth(response)) return
        const data = await response.json()
        if (data.success) {
            quitarItem(card)
            actualizarResumen(data.success.carrito)
        } else {
            errorToast(data.errors || 'Error al eliminar')
        }
    } catch {
        errorToast('Ocurrió un error')
    } finally {
        restaurarControles()
    }
}

async function vaciarCarrito(csrfToken) {
    try {
        const response = await fetch('/carrito/vaciar/', {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken}
        })
        if (await redirigirSiNoAuth(response)) return
        const data = await response.json()
        if (data.success) {
            location.reload()
        } else {
            errorToast(data.errors || 'Error al vaciar')
        }
    } catch {
        errorToast('Ocurrió un error')
    }
}
