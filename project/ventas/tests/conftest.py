from decimal import Decimal

import pytest
from django.test import Client

from carrito.models import CarritoItemModel
from productos.models import (
    CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel, ProductoModel
)
from usuarios.models import UsuarioModel


@pytest.fixture
def user_data():
    return {
        "email": "cliente@example.com",
        "nombre_completo": "Cliente Test",
        "password": "TestPass123",
    }


@pytest.fixture
def usuario(db, user_data):
    return UsuarioModel.objects.create_user(**user_data)


@pytest.fixture
def carrito(usuario):
    return usuario.carrito


@pytest.fixture
def categoria_data():
    return {'nombre': 'Ropa', 'slug': 'ropa'}


@pytest.fixture
def subcategoria_data(db, categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    return SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Camisetas', slug='camisetas'
    )


@pytest.fixture
def producto_data():
    return {
        'nombre': 'Camiseta básica',
        'descripcion': 'Camiseta de algodón',
        'slug': 'camiseta-basica',
        'sku': 'CAM-001',
        'precio': Decimal('15000'),
        'precio_transferencia': Decimal('13500'),
        'stock': 10,
        'activo': True,
    }


@pytest.fixture
def producto(db, subcategoria_data, producto_data):
    return ProductoModel.objects.create(
        subcategoria=subcategoria_data, **producto_data
    )


@pytest.fixture
def item(db, carrito, producto):
    return CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=2
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def datos_checkout():
    return {
        'nombre': 'Cliente Test',
        'email': 'cliente@example.com',
        'telefono': '3434567890',
        'direccion': 'Calle 1 123',
        'ciudad': 'Nogoyá',
        'provincia': 'Entre Ríos',
        'codigo_postal': '3150',
    }
