from decimal import Decimal

import pytest
from django.test import Client

from productos.models import (
    CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel,
    TagModel, ProductoModel
)


@pytest.fixture
def categoria_data():
    return {'nombre': 'Ropa', 'slug': 'ropa'}


@pytest.fixture
def subcategoria_data(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    return SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Camisetas', slug='camisetas'
    )


@pytest.fixture
def color_data():
    return {'nombre': 'Rojo', 'codigo_hex': '#FF0000'}


@pytest.fixture
def medida_data():
    return {'nombre': 'S'}


@pytest.fixture
def tag_data():
    return {'nombre': TagModel.TagChoices.NUEVO}


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
def producto_data_completa(subcategoria_data, color_data, medida_data, tag_data):
    color = ColorModel.objects.create(**color_data)
    medida = MedidaModel.objects.create(**medida_data)
    tag, _ = TagModel.objects.get_or_create(**tag_data)
    return {
        'subcategoria': subcategoria_data,
        'nombre': 'Camiseta básica',
        'descripcion': 'Camiseta de algodón',
        'slug': 'camiseta-basica',
        'sku': 'CAM-001',
        'precio': Decimal('15000'),
        'precio_transferencia': Decimal('13500'),
        'stock': 10,
        'peso': 0.25,
        'promocion': ProductoModel.PromocionChoices.DIEZ,
        'destacado': True,
        'activo': True,
    }


@pytest.fixture
def producto(db, producto_data_completa):
    producto = ProductoModel.objects.create(**producto_data_completa)
    return producto


@pytest.fixture
def client():
    return Client()
