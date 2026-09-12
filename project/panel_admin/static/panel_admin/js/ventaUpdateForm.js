import {successAlertRedirectOnClose, errorAlert} from '/static/js/alertas.js'

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form')
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value

    form.addEventListener('submit', (e) => {
        e.preventDefault()
        const formData = new FormData(form)
        postForm(formData, csrfToken, form)
    })
})

async function postForm(formData, csrfToken, form) {
    const btnSubmit = document.getElementById('btn-submit')
    const text = document.getElementById('btn-text')
    const spinner = document.getElementById('btn-spinner')
    btnSubmit.disabled = true
    text.textContent = ''
    spinner.classList.remove('d-none')

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': csrfToken }
        })
        const data = await response.json()
        if (data.success) {
            successAlertRedirectOnClose(data.message, data.redirect)
        } else if (data.message) {
            errorAlert(data.message)
        } else {
            errorAlert('Ocurrió un error al guardar.')
        }
    } catch (error) {
        console.log(error)
        errorAlert('Ocurrió un error inesperado. Intentá más tarde.')
    } finally {
        btnSubmit.disabled = false
        text.textContent = 'Guardar'
        spinner.classList.add('d-none')
    }
}
