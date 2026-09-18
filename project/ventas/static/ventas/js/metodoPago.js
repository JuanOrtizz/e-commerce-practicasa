export function setupOpcionesPago() {
    const radios = document.querySelectorAll('input[name="metodo_pago"]')
    if (!radios.length) return

    const btn = document.getElementById('btn-submit')

    function actualizar() {
        const seleccionado = document.querySelector('input[name="metodo_pago"]:checked')
        document.querySelectorAll('.ventas-opcion').forEach(op => {
            op.classList.toggle('selected', op.dataset.metodo === (seleccionado && seleccionado.value))
        })
        if (btn) btn.disabled = !seleccionado
    }

    radios.forEach(radio => radio.addEventListener('change', actualizar))
    actualizar()
}

document.addEventListener('DOMContentLoaded', setupOpcionesPago)
