from decimal import Decimal

import pytest
from django.urls import reverse

from base.models import ConsultaModel
from productos.models import ProductoModel, ProductoImagenModel, SubcategoriaModel


def producto_form_data(subcategoria, **kwargs):
    data = {
        'subcategoria': subcategoria.id,
        'nombre': 'Camiseta básica',
        'descripcion': 'Camiseta de algodón',
        'slug': '',
        'sku': 'CAM-001',
        'precio': '15000',
        'precio_transferencia': '13500',
        'stock': '10',
        'colores': [],
        'medidas': [],
        'promocion': '',
        'tags': [],
        'imagenes-TOTAL_FORMS': '3',
        'imagenes-INITIAL_FORMS': '0',
        'imagenes-MIN_NUM_FORMS': '0',
        'imagenes-MAX_NUM_FORMS': '1000',
    }
    data.update(kwargs)
    return data


@pytest.mark.django_db
def test_dashboard_requiere_login(client):
    response = client.get(reverse('panel_inicio'))
    assert response.status_code == 302
    assert 'login-admin-tienda' in response.url


@pytest.mark.django_db
def test_dashboard_redirige_cliente(cliente_client):
    response = cliente_client.get(reverse('panel_inicio'))
    assert response.status_code == 302
    assert 'login-admin-tienda' in response.url


@pytest.mark.django_db
def test_dashboard_admin_200(admin_client, producto, consulta):
    response = admin_client.get(reverse('panel_inicio'))
    assert response.status_code == 200
    assert response.context['productos_activos'] == 1
    assert response.context['total_productos'] == 1
    assert response.context['total_consultas'] == 1
    assert response.context['consultas_mes'] == 1


@pytest.mark.django_db
def test_lista_productos_200(admin_client, producto):
    response = admin_client.get(reverse('panel_productos'))
    assert response.status_code == 200
    assert list(response.context['productos']) == [producto]


@pytest.mark.django_db
def test_lista_productos_requiere_admin(client, cliente_client):
    assert client.get(reverse('panel_productos')).status_code == 302
    assert cliente_client.get(reverse('panel_productos')).status_code == 302


@pytest.mark.django_db
def test_producto_detalle_200(admin_client, producto):
    response = admin_client.get(reverse('panel_producto_detalle', args=[producto.id]))
    assert response.status_code == 200
    assert response.context['producto'] == producto


@pytest.mark.django_db
def test_producto_detalle_inexistente_404(admin_client):
    response = admin_client.get(reverse('panel_producto_detalle', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_producto_nuevo_get_200(admin_client):
    response = admin_client.get(reverse('panel_producto_nuevo'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_producto_nuevo_post_crea(admin_client, subcategoria):
    data = producto_form_data(subcategoria, nombre='Nuevo producto', sku='NUE-001')
    response = admin_client.post(reverse('panel_producto_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is True
    producto = ProductoModel.objects.get(sku='NUE-001')
    assert producto.nombre == 'Nuevo producto'
    assert producto.slug == 'nuevo-producto'
    assert data_json['redirect'] == reverse('panel_producto_detalle', args=[producto.id])


@pytest.mark.django_db
def test_producto_nuevo_post_sku_duplicado_invalido(admin_client, producto, subcategoria):
    data = producto_form_data(subcategoria, nombre='Camiseta Negra', sku=producto.sku)
    response = admin_client.post(reverse('panel_producto_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe un producto con este código' in data_json['errors']['sku'][0]


@pytest.mark.django_db
def test_producto_nuevo_post_nombre_duplicado_invalido(admin_client, producto, subcategoria):
    data = producto_form_data(subcategoria, sku='CAM-002')
    response = admin_client.post(reverse('panel_producto_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe un producto creado con ese nombre.' in data_json['errors']['nombre'][0]


@pytest.mark.django_db
def test_producto_modificar_get_200(admin_client, producto):
    response = admin_client.get(reverse('panel_producto_modificar', args=[producto.id]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_producto_modificar_get_extra_imagenes_sin_imagenes(admin_client, producto):
    response = admin_client.get(reverse('panel_producto_modificar', args=[producto.id]))
    assert response.context['formset'].extra == 3


@pytest.mark.django_db
def test_producto_modificar_get_extra_imagenes_con_2_imagenes(admin_client, producto):
    for i in range(2):
        ProductoImagenModel.objects.create(
            producto=producto, imagen='productos/test.jpg', orden=i
        )
    response = admin_client.get(reverse('panel_producto_modificar', args=[producto.id]))
    assert response.context['formset'].extra == 1


@pytest.mark.django_db
def test_producto_modificar_get_extra_imagenes_con_3_imagenes(admin_client, producto):
    for i in range(3):
        ProductoImagenModel.objects.create(
            producto=producto, imagen='productos/test.jpg', orden=i
        )
    response = admin_client.get(reverse('panel_producto_modificar', args=[producto.id]))
    assert response.context['formset'].extra == 0


@pytest.mark.django_db
def test_producto_modificar_post_actualiza(admin_client, producto):
    data = producto_form_data(
        producto.subcategoria,
        nombre='Camiseta modificada',
        precio='16000',
        stock='8',
    )
    response = admin_client.post(reverse('panel_producto_modificar', args=[producto.id]), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_producto_detalle', args=[producto.id])
    producto.refresh_from_db()
    assert producto.nombre == 'Camiseta modificada'
    assert producto.precio == Decimal('16000')
    assert producto.stock == 8


@pytest.mark.django_db
def test_producto_modificar_post_sin_cambios(admin_client, producto):
    data = producto_form_data(producto.subcategoria, activo='on')
    response = admin_client.post(reverse('panel_producto_modificar', args=[producto.id]), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert data_json['message'] == 'No realizaste modificaciones.'
    producto.refresh_from_db()
    assert producto.nombre == 'Camiseta básica'


@pytest.mark.django_db
def test_producto_modificar_post_no_cambia_subcategoria(admin_client, producto, subcategoria):
    otra_sub = SubcategoriaModel.objects.create(
        categoria=subcategoria.categoria, nombre='Pantalones', slug='pantalones'
    )
    data = producto_form_data(otra_sub, nombre='Camiseta modificada')
    response = admin_client.post(reverse('panel_producto_modificar', args=[producto.id]), data)
    data_json = response.json()
    assert data_json['success'] is True
    producto.refresh_from_db()
    assert producto.subcategoria == subcategoria


@pytest.mark.django_db
def test_producto_eliminar_post_elimina(admin_client, producto):
    response = admin_client.post(reverse('panel_producto_eliminar', args=[producto.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_productos')
    assert not ProductoModel.objects.filter(id=producto.id).exists()


@pytest.mark.django_db
def test_producto_eliminar_get_405(admin_client, producto):
    response = admin_client.get(reverse('panel_producto_eliminar', args=[producto.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_lista_consultas_200(admin_client, consulta):
    response = admin_client.get(reverse('panel_consultas'))
    assert response.status_code == 200
    assert list(response.context['consultas']) == [consulta]


@pytest.mark.django_db
def test_consulta_detalle_200(admin_client, consulta):
    response = admin_client.get(reverse('panel_consulta_detalle', args=[consulta.id]))
    assert response.status_code == 200
    assert response.context['consulta'] == consulta


@pytest.mark.django_db
def test_consulta_modificar_post_actualiza(admin_client, consulta):
    data = {
        'nombre': consulta.nombre,
        'email': consulta.email,
        'telefono': consulta.telefono,
        'mensaje': 'Mensaje actualizado.',
    }
    response = admin_client.post(reverse('panel_consulta_modificar', args=[consulta.id]), data)
    assert response.status_code == 302
    consulta.refresh_from_db()
    assert consulta.mensaje == 'Mensaje actualizado.'


@pytest.mark.django_db
def test_consulta_modificar_post_invalido_200(admin_client, consulta):
    data = {
        'nombre': 'A',
        'email': consulta.email,
        'telefono': consulta.telefono,
        'mensaje': consulta.mensaje,
    }
    response = admin_client.post(reverse('panel_consulta_modificar', args=[consulta.id]), data)
    assert response.status_code == 200


@pytest.mark.django_db
def test_consulta_eliminar_post_elimina(admin_client, consulta):
    response = admin_client.post(reverse('panel_consulta_eliminar', args=[consulta.id]))
    assert response.status_code == 302
    assert not ConsultaModel.objects.filter(id=consulta.id).exists()


@pytest.mark.django_db
def test_pagos_200(admin_client):
    response = admin_client.get(reverse('panel_pagos'))
    assert response.status_code == 200
