import pytest
from base.forms import ConsultaAdminForm, ConsultaForm
from base.models import ConsultaModel


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


def test_consulta_admin_form_solo_campo_estado():
    assert list(ConsultaAdminForm().fields) == ['estado']


@pytest.mark.django_db
@pytest.mark.parametrize('estado', [
    ConsultaModel.Estados.PENDIENTE,
    ConsultaModel.Estados.RESUELTA,
])
def test_consulta_admin_form_estado_valido(estado):
    consulta = ConsultaModel.objects.create(
        nombre='Juan Pérez',
        email='juan@example.com',
        telefono='1122334455',
        mensaje='Mensaje de prueba válido.',
    )
    form = ConsultaAdminForm(data={'estado': estado}, instance=consulta)
    assert form.is_valid()


@pytest.mark.django_db
def test_consulta_admin_form_estado_invalido():
    consulta = ConsultaModel.objects.create(
        nombre='Juan Pérez',
        email='juan@example.com',
        telefono='1122334455',
        mensaje='Mensaje de prueba válido.',
    )
    form = ConsultaAdminForm(data={'estado': 'invalido'}, instance=consulta)
    assert not form.is_valid()


@pytest.mark.django_db
def test_consulta_por_defecto_pendiente(consulta_data):
    consulta = ConsultaModel.objects.create(**consulta_data)
    assert consulta.estado == ConsultaModel.Estados.PENDIENTE
