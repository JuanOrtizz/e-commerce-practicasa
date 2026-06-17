import pytest
from usuarios.forms import RegistroForm, LoginForm, LoginAdminTiendaForm, CustomSetPasswordForm
from usuarios.models import UsuarioModel


@pytest.mark.django_db
def test_registro_valido(form_data):
    form = RegistroForm(data=form_data)
    assert form.is_valid()


@pytest.mark.parametrize("nombre", [
    "Juan Pérez",
    "María José Fernández",
    "José",
    "Luis",
])
@pytest.mark.django_db
def test_registro_nombre_valido(nombre, form_data):
    data = {**form_data, "nombre_completo": nombre}
    form = RegistroForm(data=data)
    assert form.is_valid()


@pytest.mark.parametrize("nombre", [
    "A",
    "Juan123",
    "Juan@Pérez",
    "Juan  Pérez",
])
@pytest.mark.django_db
def test_registro_nombre_invalido(nombre, form_data):
    data = {**form_data, "nombre_completo": nombre}
    form = RegistroForm(data=data)
    assert not form.is_valid()


@pytest.mark.parametrize("email", [
    "invalido",
    "usuario@",
    "a@b.c",
    "@dominio.com",
])
@pytest.mark.django_db
def test_registro_email_invalido(email, form_data):
    data = {**form_data, "email": email}
    form = RegistroForm(data=data)
    assert not form.is_valid()


@pytest.mark.django_db
def test_registro_email_duplicado(form_data, user_data):
    UsuarioModel.objects.create_user(**user_data)
    form = RegistroForm(data=form_data)
    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.parametrize("password", [
    "12345678",
    "abcdefgh",
])
@pytest.mark.django_db
def test_registro_password_invalida(password, form_data):
    data = {**form_data, "password1": password, "password2": password}
    form = RegistroForm(data=data)
    assert not form.is_valid()


@pytest.mark.django_db
def test_login_valido(user_data):
    UsuarioModel.objects.create_user(**user_data)
    form = LoginForm(data={"username": user_data["email"], "password": user_data["password"]})
    assert form.is_valid()


@pytest.mark.django_db
def test_login_invalido():
    form = LoginForm(data={"username": "no@existe.com", "password": "wrong"})
    assert not form.is_valid()


@pytest.mark.django_db
def test_login_admin_tienda_valido(user_data):
    UsuarioModel.objects.create_user(**user_data, tipo=UsuarioModel.Tipos.ADMINISTRADOR_TIENDA)
    form = LoginAdminTiendaForm(data={"username": user_data["email"], "password": user_data["password"]})
    assert form.is_valid()


@pytest.mark.django_db
def test_login_admin_tienda_cliente_rechazado(user_data):
    UsuarioModel.objects.create_user(**user_data)
    form = LoginAdminTiendaForm(data={"username": user_data["email"], "password": user_data["password"]})
    assert not form.is_valid()
    assert "No tenés permisos" in str(form.errors)


@pytest.mark.django_db
def test_set_password_valido(user_data):
    usuario = UsuarioModel.objects.create_user(**user_data)
    form = CustomSetPasswordForm(user=usuario, data={
        "new_password1": "NuevaPass123",
        "new_password2": "NuevaPass123",
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_set_password_no_coinciden(user_data):
    usuario = UsuarioModel.objects.create_user(**user_data)
    form = CustomSetPasswordForm(user=usuario, data={
        "new_password1": "NuevaPass123",
        "new_password2": "OtraPass456",
    })
    assert not form.is_valid()
