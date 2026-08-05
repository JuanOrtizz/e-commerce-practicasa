import pytest

from carrito.models import CarritoModel
from usuarios.models import UsuarioModel


@pytest.mark.django_db
def test_crear_usuario_crea_carrito(user_data):
    usuario = UsuarioModel.objects.create_user(**user_data)
    assert CarritoModel.objects.filter(usuario=usuario).count() == 1


@pytest.mark.django_db
def test_guardar_usuario_no_duplica_carrito(usuario, carrito):
    usuario.nombre_completo = 'Otro Nombre'
    usuario.save()
    assert CarritoModel.objects.filter(usuario=usuario).count() == 1
