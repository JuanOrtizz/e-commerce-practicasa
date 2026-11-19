import pytest

from ventas.forms import CheckoutForm


def test_checkout_form_acepta_ciudad_con_digitos(datos_checkout):
    form = CheckoutForm({
        **datos_checkout,
        'provincia': 'Buenos Aires',
        'ciudad': '25 de Mayo',
    })
    assert form.is_valid(), form.errors


def test_checkout_form_acepta_provincia_con_coma(datos_checkout):
    form = CheckoutForm({
        **datos_checkout,
        'provincia': 'Tierra del Fuego, Antártida e Islas del Atlántico Sur',
        'ciudad': 'Ushuaia',
    })
    assert form.is_valid(), form.errors


def test_checkout_form_rechaza_ciudad_que_no_es_de_la_provincia(datos_checkout):
    form = CheckoutForm({
        **datos_checkout,
        'provincia': 'Entre Ríos',
        'ciudad': 'Ushuaia',
    })
    assert not form.is_valid()
    assert (
        form.errors['ciudad'][0]
        == 'Ciudad inválida. Seleccioná una opción válida.'
    )


def test_checkout_form_rechaza_provincia_inexistente(datos_checkout):
    form = CheckoutForm({**datos_checkout, 'provincia': 'Provincia Falsa'})
    assert not form.is_valid()
    assert (
        form.errors['provincia'][0]
        == 'Provincia inválida. Seleccioná una opción válida.'
    )


@pytest.mark.parametrize('ciudad', ['Nogoy@123', '123'])
def test_checkout_form_rechaza_ciudad_invalida(datos_checkout, ciudad):
    form = CheckoutForm({**datos_checkout, 'ciudad': ciudad})
    assert not form.is_valid()
    assert 'ciudad' in form.errors


@pytest.mark.parametrize('codigo_postal, mensaje', [
    ('315', 'El CP debe tener 4 dígitos.'),
    ('315a', 'El CP debe tener solo números.'),
    ('a315', 'El CP debe tener solo números.'),
    ('31-5', 'El CP debe tener solo números.'),
])
def test_checkout_form_cp_invalido(datos_checkout, codigo_postal, mensaje):
    form = CheckoutForm({**datos_checkout, 'codigo_postal': codigo_postal})
    assert not form.is_valid()
    assert mensaje in form.errors['codigo_postal'][0]
