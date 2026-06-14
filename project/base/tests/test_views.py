import pytest
from django.core import mail
from django.test.utils import override_settings
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


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_flujo_contacto_valido(client, consulta_data):
    response = client.post(reverse('contacto'), consulta_data)
    data = response.json()
    assert data['success'] is True
    assert 'Recibimos tu consulta' in data['message']
    assert ConsultaModel.objects.count() == 1
    assert len(mail.outbox) == 1
    assert 'Consulta en la web' in mail.outbox[0].subject

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_ratelimit_contacto_bloquea(client, consulta_data):
    from django.core.cache import cache
    cache.clear()

    for _ in range(5):
        response = client.post(reverse('contacto'), consulta_data)
        assert response.status_code == 200

    response = client.post(reverse('contacto'), consulta_data)
    assert response.status_code == 403