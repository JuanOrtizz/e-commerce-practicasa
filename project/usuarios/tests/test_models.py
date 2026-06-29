import pytest
from usuarios.models import UsuarioModel


@pytest.mark.django_db
def test_crear_usuario_cliente(user_data):
    usuario = UsuarioModel.objects.create_user(**user_data)
    assert usuario.pk is not None
    assert usuario.email == user_data["email"]
    assert usuario.nombre_completo == user_data["nombre_completo"]
    assert usuario.tipo == UsuarioModel.Tipos.CLIENTE
    assert usuario.is_active is True
    assert usuario.is_staff is False
    assert usuario.is_superuser is False


@pytest.mark.django_db
def test_crear_admin_tienda(user_data):
    usuario = UsuarioModel.objects.create_user(
        **user_data, tipo=UsuarioModel.Tipos.ADMINISTRADOR_TIENDA
    )
    assert usuario.tipo == UsuarioModel.Tipos.ADMINISTRADOR_TIENDA
    assert usuario.is_staff is False


@pytest.mark.django_db
def test_crear_superuser(user_data):
    usuario = UsuarioModel.objects.create_superuser(**user_data)
    assert usuario.is_staff is True
    assert usuario.is_superuser is True
    assert usuario.tipo == UsuarioModel.Tipos.SUPERUSER


@pytest.mark.django_db
def test_str_retorna_email(user_data):
    usuario = UsuarioModel.objects.create_user(**user_data)
    assert str(usuario) == user_data["email"]


@pytest.mark.django_db
def test_email_unico(user_data):
    UsuarioModel.objects.create_user(**user_data)
    with pytest.raises(Exception):
        UsuarioModel.objects.create_user(**user_data)


@pytest.mark.django_db
def test_create_user_sin_email_error():
    with pytest.raises(ValueError, match="El email es obligatorio"):
        UsuarioModel.objects.create_user(email="", nombre_completo="Juan", password="pass123")
