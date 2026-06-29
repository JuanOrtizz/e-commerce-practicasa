import pytest
from django.test import Client


@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "nombre_completo": "Test User",
        "password": "TestPass123",
    }


@pytest.fixture
def form_data():
    return {
        "email": "test@example.com",
        "nombre_completo": "Test User",
        "password1": "TestPass123",
        "password2": "TestPass123",
    }


@pytest.fixture
def client():
    return Client()
