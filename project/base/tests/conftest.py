import pytest
from django.test import Client


@pytest.fixture
def consulta_data():
    return {
        'nombre': 'Juan Pérez',
        'email': 'juan@example.com',
        'telefono': '1122334455',
        'mensaje': 'Mensaje de prueba válido.',
    }


@pytest.fixture
def invalid_consulta_data():
    return {
        'nombre': 'A',
        'email': 'invalido',
        'telefono': '12',
        'mensaje': '',
    }


@pytest.fixture
def client():
    return Client()
