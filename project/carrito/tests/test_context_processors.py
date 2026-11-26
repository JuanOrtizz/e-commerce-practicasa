import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from carrito.context_processors import carrito_cantidad
from carrito.models import CarritoItemModel
from productos.models import ColorModel


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
def test_carrito_cantidad_anonimo(request_factory):
    request = request_factory.get('/')
    request.user = AnonymousUser()
    assert carrito_cantidad(request) == {'carrito_cantidad': 0}


@pytest.mark.django_db
def test_carrito_cantidad_suma_unidades(request_factory, usuario, producto, carrito):
    rojo = ColorModel.objects.create(nombre='Rojo', codigo_hex='#FF0000')
    azul = ColorModel.objects.create(nombre='Azul', codigo_hex='#0000FF')
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, color_nombre=rojo.nombre, cantidad=2
    )
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, color_nombre=azul.nombre, cantidad=3
    )
    request = request_factory.get('/')
    request.user = usuario
    assert carrito_cantidad(request) == {'carrito_cantidad': 5}
