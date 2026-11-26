const MAX_VISIBLE = 99

export function actualizarBadgeCarrito(cantidad) {
    const badge = document.getElementById('header-cart-badge')
    if (!badge) return

    const total = Number(cantidad) || 0
    badge.textContent = total > MAX_VISIBLE ? `${MAX_VISIBLE}+` : total
    badge.classList.toggle('d-none', total <= 0)

    if (total <= 0) return
    badge.classList.remove('is-animado')
    void badge.offsetWidth
    badge.classList.add('is-animado')
}
