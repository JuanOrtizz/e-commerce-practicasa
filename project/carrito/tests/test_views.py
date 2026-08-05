from decimal import Decimal

import pytest
from django.urls import reverse

from carrito.models import CarritoItemModel
from productos.models import ColorModel, MedidaModel


@pytest.mark.django_db
def test_ver_carrito_anonimo_redirect(client):
    response = client.get(reverse('ver_carrito'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_ver_carrito_vacio_200(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('ver_carrito'))
    assert response.status_code == 200
    assert list(response.context['items']) == []
    assert response.context['cantidad_items'] == 0


@pytest.mark.django_db
def test_ver_carrito_con_items_200(client, usuario, producto):
    CarritoItemModel.objects.create(carrito=usuario.carrito, producto=producto, cantidad=2)
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('ver_carrito'))
    assert response.status_code == 200
    assert len(response.context['items']) == 1
    assert response.context['total'] == Decimal('30000.00')
    assert response.context['total_transferencia'] == Decimal('27000.00')
    assert response.context['total_ahorro'] == Decimal('0')
    assert response.context['cantidad_items'] == 1


@pytest.mark.django_db
def test_agregar_anonimo_401(client):
    response = client.post(reverse('agregar'), {'producto_id': 1})
    assert response.status_code == 401
    assert response.json() == {'login_required': True}


@pytest.mark.django_db
def test_agregar_exitoso(client, usuario, producto):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('agregar'), {'producto_id': producto.id})
    assert response.status_code == 200
    data = response.json()
    assert 'success' in data
    assert producto.nombre in data['success']['message']
    assert usuario.carrito.items.count() == 1


@pytest.mark.django_db
def test_agregar_sin_producto_id_400(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('agregar'), {})
    assert response.status_code == 400
    assert response.json() == {'errors': 'Producto no especificado'}


@pytest.mark.django_db
def test_agregar_producto_sin_stock_400(client, usuario, producto):
    producto.stock = 0
    producto.save()
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('agregar'), {'producto_id': producto.id})
    assert response.status_code == 400
    assert response.json() == {'errors': 'Producto sin stock'}


@pytest.mark.django_db
def test_agregar_con_color_y_medida(client, usuario, producto, color_data, medida_data):
    color = ColorModel.objects.create(**color_data)
    medida = MedidaModel.objects.create(**medida_data)
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('agregar'), {
        'producto_id': producto.id,
        'color': color.id,
        'medida': medida.id,
    })
    assert response.status_code == 200
    item = usuario.carrito.items.first()
    assert item.color_nombre == 'Rojo'
    assert item.color_hex == '#FF0000'
    assert item.medida_nombre == 'S'


@pytest.mark.django_db
def test_agregar_get_405(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('agregar'))
    assert response.status_code == 405


@pytest.mark.django_db
def test_agregar_producto_inexistente_404(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('agregar'), {'producto_id': 999})
    assert response.status_code == 404
    assert response.json() == {'errors': 'Producto no encontrado'}


@pytest.mark.django_db
def test_actualizar_anonimo_401(client):
    response = client.post(reverse('actualizar'), {'item_id': 1, 'cantidad': 2})
    assert response.status_code == 401
    assert response.json() == {'login_required': True}


@pytest.mark.django_db
def test_actualizar_exitoso(client, usuario, producto):
    item = CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, cantidad=2
    )
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('actualizar'), {
        'item_id': item.id, 'cantidad': 4,
    })
    assert response.status_code == 200
    data = response.json()['success']
    assert data['item_eliminado'] is False
    assert data['item']['id'] == item.id
    assert data['item']['cantidad'] == 4
    assert data['item']['subtotal'] == str(Decimal('60000.00'))
    assert data['item']['stock'] == producto.stock
    assert data['carrito']['total'] == str(Decimal('60000.00'))


@pytest.mark.django_db
def test_actualizar_cantidad_cero_elimina_item(client, usuario, producto):
    item = CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, cantidad=2
    )
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('actualizar'), {
        'item_id': item.id, 'cantidad': 0,
    })
    assert response.status_code == 200
    data = response.json()['success']
    assert data['item_eliminado'] is True
    assert 'item' not in data
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_actualizar_supera_stock_400(client, usuario, producto):
    item = CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, cantidad=1
    )
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('actualizar'), {
        'item_id': item.id, 'cantidad': producto.stock + 5,
    })
    assert response.status_code == 400
    assert response.json() == {'errors': 'Producto sin stock'}


@pytest.mark.django_db
def test_actualizar_item_inexistente_404(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('actualizar'), {'item_id': 999, 'cantidad': 2})
    assert response.status_code == 404
    assert response.json() == {'errors': 'Item no encontrado'}


@pytest.mark.django_db
def test_actualizar_cantidad_invalida_400(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('actualizar'), {'item_id': 1, 'cantidad': 'abc'})
    assert response.status_code == 400
    assert response.json() == {'errors': 'Cantidad inválida'}


@pytest.mark.django_db
def test_eliminar_anonimo_401(client):
    response = client.post(reverse('eliminar'), {'item_id': 1})
    assert response.status_code == 401
    assert response.json() == {'login_required': True}


@pytest.mark.django_db
def test_eliminar_exitoso(client, usuario, producto):
    item = CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, cantidad=2
    )
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('eliminar'), {'item_id': item.id})
    assert response.status_code == 200
    data = response.json()['success']
    assert 'carrito' in data
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_eliminar_item_inexistente_404(client, usuario):
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('eliminar'), {'item_id': 999})
    assert response.status_code == 404
    assert response.json() == {'errors': 'Item no encontrado'}


@pytest.mark.django_db
def test_vaciar_anonimo_401(client):
    response = client.post(reverse('vaciar'))
    assert response.status_code == 401
    assert response.json() == {'login_required': True}


@pytest.mark.django_db
def test_vaciar_exitoso(client, usuario, producto):
    CarritoItemModel.objects.create(carrito=usuario.carrito, producto=producto, cantidad=2)
    client.login(username=usuario.email, password='TestPass123')
    response = client.post(reverse('vaciar'))
    assert response.status_code == 200
    assert response.json()['success']['message'] == 'Carrito vaciado'
    assert CarritoItemModel.objects.count() == 0
