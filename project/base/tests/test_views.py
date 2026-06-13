import pytest
from django.urls import reverse
from base.models import ConsultaModel


@pytest.mark.django_db
def test_index_status_200(client):
    response = client.get(reverse('index'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_contacto_get_200(client):
    response = client.get(reverse('contacto'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_flujo_contacto_invalido(client, invalid_consulta_data):
    response = client.post(reverse('contacto'), invalid_consulta_data)
    data = response.json()
    assert data['success'] is False
    assert 'errors' in data
    assert ConsultaModel.objects.count() == 0


@pytest.mark.django_db
def test_flujo_contacto_valido(client, consulta_data):
    response = client.post(reverse('contacto'), consulta_data)
    data = response.json()
    assert data['success'] is True
    assert 'Recibimos tu consulta' in data['message']
    assert ConsultaModel.objects.count() == 1
