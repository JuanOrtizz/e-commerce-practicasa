const form = document.getElementById('form-filtros')

form.addEventListener('change', (e) => {
    if (e.target.matches('input[type=radio], input[type=checkbox], select')) {
        form.submit()
    }
})
