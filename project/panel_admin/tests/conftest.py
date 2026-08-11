from decimal import Decimal

import pytest
from django.test import Client

from base.models import ConsultaModel
from productos.models import CategoriaModel, SubcategoriaModel, ProductoModel
from usuarios.models import UsuarioModel


@pytest.fixture
def admin_data():
    return {
        "email": "admin@example.com",
        "nombre_completo": "Admin Tienda",
        "password": "AdminPass123",
    }


@pytest.fixture
def cliente_data():
    return {
        "email": "cliente@example.com",
        "nombre_completo": "Cliente Test",
        "password": "ClientePass123",
    }


@pytest.fixture
def admin_user(db, admin_data):
    return UsuarioModel.objects.create_user(
        **admin_data, tipo=UsuarioModel.Tipos.ADMINISTRADOR_TIENDA
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def cliente_user(db, cliente_data):
    return UsuarioModel.objects.create_user(**cliente_data)


@pytest.fixture
def cliente_client(client, cliente_user):
    client.force_login(cliente_user)
    return client


@pytest.fixture
def categoria(db):
    return CategoriaModel.objects.create(nombre='Ropa', slug='ropa')


@pytest.fixture
def subcategoria(db, categoria):
    return SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Camisetas', slug='camisetas'
    )


@pytest.fixture
def producto(db, subcategoria):
    return ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Camiseta básica',
        descripcion='Camiseta de algodón',
        slug='camiseta-basica',
        sku='CAM-001',
        precio=Decimal('15000'),
        precio_transferencia=Decimal('13500'),
        stock=10,
        activo=True,
    )


@pytest.fixture
def consulta(db):
    return ConsultaModel.objects.create(
        nombre='Juan Pérez',
        email='juan@example.com',
        telefono='1122334455',
        mensaje='Mensaje de prueba válido.',
    )


@pytest.fixture
def client():
    return Client()
