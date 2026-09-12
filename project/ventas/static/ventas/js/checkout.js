function setupMetodoPago() {
    const radios = document.querySelectorAll('input[name="metodo_pago"]')
    if (!radios.length) return

    const hidden = document.getElementById('metodo-pago-hidden')
    const ayuda = document.getElementById('pago-ayuda')
    const btn = document.getElementById('btn-submit')

    function actualizar() {
        const seleccionado = document.querySelector('input[name="metodo_pago"]:checked')
        document.querySelectorAll('.ventas-opcion').forEach(op => {
            op.classList.toggle('selected', seleccionado && op.dataset.metodo === seleccionado.value)
        })

        if (hidden) hidden.value = seleccionado ? seleccionado.value : ''
        if (btn) btn.disabled = !seleccionado

        if (ayuda) {
            if (seleccionado) {
                if (seleccionado.value === 'efectivo') {
                    ayuda.textContent = 'Tu pedido queda pendiente. Pasá por el local a pagar y retirar.'
                } else {
                    ayuda.textContent = 'Vas a ser redirigido a Mercado Pago para completar tu pago.'
                }
            } else {
                ayuda.textContent = 'Seleccioná una forma de pago.'
            }
        }
    }

    radios.forEach(radio => radio.addEventListener('change', actualizar))
    actualizar()
}

function setupOpcionesEnvio() {
    const radios = document.querySelectorAll('input[name="metodo_envio"]')
    if (!radios.length) return

    const btn = document.getElementById('btn-submit')

    function actualizar() {
        const seleccionado = document.querySelector('input[name="metodo_envio"]:checked')
        document.querySelectorAll('.ventas-opcion').forEach(op => {
            op.classList.toggle('selected', op.dataset.metodo === (seleccionado && seleccionado.value))
        })
        if (btn) btn.disabled = !seleccionado
    }

    radios.forEach(radio => radio.addEventListener('change', actualizar))
    actualizar()
}

document.addEventListener('DOMContentLoaded', () => {
    setupMetodoPago()
    setupOpcionesEnvio()
})
