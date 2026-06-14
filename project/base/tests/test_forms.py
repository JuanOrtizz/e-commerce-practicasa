import pytest
from base.forms import ConsultaForm


@pytest.mark.parametrize('nombre', [
    'Juan Pérez',
    'María José Fernández',
    'José',
    'Luis',
])
def test_nombre_valido(nombre, consulta_data):
    data = {**consulta_data, 'nombre': nombre}
    form = ConsultaForm(data=data)
    assert form.is_valid()


@pytest.mark.parametrize('nombre', [
    'A',
    'Juan123',
    'Juan@Pérez',
    'Juan  Pérez',
])
def test_nombre_invalido(nombre, consulta_data):
    data = {**consulta_data, 'nombre': nombre}
    form = ConsultaForm(data=data)
    assert not form.is_valid()


@pytest.mark.parametrize('email', [
    'invalido',
    'usuario@',
    'a@b.c',
    '@dominio.com',
])
def test_email_invalido(email, consulta_data):
    data = {**consulta_data, 'email': email}
    form = ConsultaForm(data=data)
    assert not form.is_valid()


@pytest.mark.parametrize('telefono,esperado', [
    ('1122334455', True),
    ('+54 11 1234-5678', True),
    ('12', False),
    ('1234ABCD', False),
])
def test_telefono(telefono, esperado, consulta_data):
    data = {**consulta_data, 'telefono': telefono}
    form = ConsultaForm(data=data)
    assert form.is_valid() == esperado


@pytest.mark.parametrize('mensaje,esperado', [
    ('Mensaje válido.', True),
    ('A', False),
    ('B' * 1001, False),
])
def test_mensaje(mensaje, esperado, consulta_data):
    data = {**consulta_data, 'mensaje': mensaje}
    form = ConsultaForm(data=data)
    assert form.is_valid() == esperado
