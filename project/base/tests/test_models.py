import pytest
from base.models import ConsultaModel

@pytest.mark.django_db
def test_crear_consulta(consulta_data):
    consulta = ConsultaModel.objects.create(**consulta_data)
    assert consulta.pk is not None
    assert consulta.nombre == 'Juan Pérez'
    assert consulta.email == 'juan@example.com'

@pytest.mark.django_db
def test_str_consulta(consulta_data):
    consulta = ConsultaModel.objects.create(**consulta_data)
    assert str(consulta) == consulta.nombre
