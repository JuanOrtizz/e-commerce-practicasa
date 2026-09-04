from decimal import Decimal

import pytest
from django.urls import reverse

from base.models import ConsultaModel
from productos.models import (
    CategoriaModel,
    ColorModel,
    MedidaModel,
    ProductoModel,
    ProductoImagenModel,
    SubcategoriaModel,
)
from ventas.models import VentaItemModel, VentaModel


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
    content = response.content.decode()
    assert 'id="buscador-productos"' in content
    assert 'id="filtro-productos"' in content
    assert 'id="orden-productos"' in content


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
    content = response.content.decode()
    assert 'id="filtro-consultas"' in content
    assert 'id="orden-consultas"' in content
    assert 'data-estado="pendiente"' in content
    assert 'data-fecha=' in content


@pytest.mark.django_db
def test_consulta_detalle_200(admin_client, consulta):
    response = admin_client.get(reverse('panel_consulta_detalle', args=[consulta.id]))
    assert response.status_code == 200
    assert response.context['consulta'] == consulta


@pytest.mark.django_db
def test_consulta_modificar_post_actualiza(admin_client, consulta):
    data = {
        'estado': 'resuelta',
        'nombre': 'Nombre cambiado',
        'mensaje': 'Mensaje actualizado.',
    }
    response = admin_client.post(reverse('panel_consulta_modificar', args=[consulta.id]), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_consulta_detalle', args=[consulta.id])
    consulta.refresh_from_db()
    assert consulta.estado == 'resuelta'
    assert consulta.nombre == 'Juan Pérez'
    assert consulta.mensaje == 'Mensaje de prueba válido.'


@pytest.mark.django_db
def test_consulta_modificar_post_invalido_200(admin_client, consulta):
    data = {'estado': 'invalido'}
    response = admin_client.post(reverse('panel_consulta_modificar', args=[consulta.id]), data)
    assert response.status_code == 200


@pytest.mark.django_db
def test_consulta_eliminar_post_elimina(admin_client, consulta):
    response = admin_client.post(reverse('panel_consulta_eliminar', args=[consulta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not ConsultaModel.objects.filter(id=consulta.id).exists()


@pytest.mark.django_db
def test_lista_consultas_requiere_admin(client, cliente_client):
    assert client.get(reverse('panel_consultas')).status_code == 302
    assert cliente_client.get(reverse('panel_consultas')).status_code == 302


@pytest.mark.django_db
def test_lista_consultas_muestra_estado_pendiente(admin_client, consulta):
    response = admin_client.get(reverse('panel_consultas'))
    assert 'Pendiente' in response.content.decode()


@pytest.mark.django_db
def test_consulta_detalle_inexistente_404(admin_client):
    response = admin_client.get(reverse('panel_consulta_detalle', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_consulta_modificar_get_200(admin_client, consulta):
    response = admin_client.get(reverse('panel_consulta_modificar', args=[consulta.id]))
    assert response.status_code == 200
    assert response.context['form'].instance == consulta


@pytest.mark.django_db
def test_consulta_modificar_post_sin_cambios(admin_client, consulta):
    data = {'estado': 'pendiente'}
    response = admin_client.post(reverse('panel_consulta_modificar', args=[consulta.id]), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert data_json['message'] == 'No realizaste modificaciones.'
    consulta.refresh_from_db()
    assert consulta.estado == 'pendiente'


@pytest.mark.django_db
def test_consulta_eliminar_get_405(admin_client, consulta):
    response = admin_client.get(reverse('panel_consulta_eliminar', args=[consulta.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_consulta_eliminar_404(admin_client):
    response = admin_client.post(reverse('panel_consulta_eliminar', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_pagos_200(admin_client):
    response = admin_client.get(reverse('panel_pagos'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_referencias_200(admin_client):
    response = admin_client.get(reverse('panel_referencias'))
    assert response.status_code == 200
    assert response.context['colores'].count() == 0
    assert response.context['medidas'].count() == 0
    assert response.context['categorias'].count() == 0
    assert response.context['subcategorias'].count() == 0


@pytest.mark.django_db
def test_referencias_requiere_admin(client, cliente_client):
    assert client.get(reverse('panel_referencias')).status_code == 302
    assert cliente_client.get(reverse('panel_referencias')).status_code == 302


@pytest.mark.django_db
def test_color_nuevo_get_200(admin_client):
    response = admin_client.get(reverse('panel_color_nuevo'))
    assert response.status_code == 200
    assert 'Nuevo color' in response.content.decode()


@pytest.mark.django_db
def test_medida_nuevo_get_200(admin_client):
    response = admin_client.get(reverse('panel_medida_nuevo'))
    assert response.status_code == 200
    assert 'Nueva medida' in response.content.decode()


@pytest.mark.django_db
def test_categoria_nuevo_get_200(admin_client):
    response = admin_client.get(reverse('panel_categoria_nuevo'))
    assert response.status_code == 200
    assert 'Nueva categoría' in response.content.decode()


@pytest.mark.django_db
def test_subcategoria_nuevo_get_200(admin_client):
    response = admin_client.get(reverse('panel_subcategoria_nuevo'))
    assert response.status_code == 200
    assert 'Nueva subcategoría' in response.content.decode()


@pytest.mark.django_db
def test_color_crear_post_crea(admin_client):
    data = {'nombre': 'Negro', 'codigo_hex': '#000000'}
    response = admin_client.post(reverse('panel_color_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_referencias')
    color = ColorModel.objects.get(nombre='Negro')
    assert color.codigo_hex == '#000000'


@pytest.mark.django_db
def test_color_crear_post_nombre_duplicado_invalido(admin_client, color):
    data = {'nombre': 'Negro', 'codigo_hex': '#111111'}
    response = admin_client.post(reverse('panel_color_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe un color' in data_json['errors']['nombre'][0]


@pytest.mark.django_db
def test_color_crear_post_hex_invalido(admin_client):
    data = {'nombre': 'Rojo', 'codigo_hex': 'FF0000'}
    response = admin_client.post(reverse('panel_color_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Código inválido' in data_json['errors']['codigo_hex'][0]


@pytest.mark.django_db
def test_color_eliminar_post_elimina(admin_client, color):
    response = admin_client.post(reverse('panel_color_eliminar', args=[color.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not ColorModel.objects.filter(id=color.id).exists()


@pytest.mark.django_db
def test_color_eliminar_get_405(admin_client, color):
    response = admin_client.get(reverse('panel_color_eliminar', args=[color.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_color_eliminar_404(admin_client):
    response = admin_client.post(reverse('panel_color_eliminar', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_medida_crear_post_crea(admin_client):
    data = {'nombre': 'Chica'}
    response = admin_client.post(reverse('panel_medida_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_referencias')
    assert MedidaModel.objects.filter(nombre='Chica').exists()


@pytest.mark.django_db
def test_medida_crear_post_nombre_duplicado_invalido(admin_client, medida):
    data = {'nombre': 'Extra Grande'}
    response = admin_client.post(reverse('panel_medida_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe una medida' in data_json['errors']['nombre'][0]


@pytest.mark.django_db
def test_medida_eliminar_post_elimina(admin_client, medida):
    response = admin_client.post(reverse('panel_medida_eliminar', args=[medida.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not MedidaModel.objects.filter(id=medida.id).exists()


@pytest.mark.django_db
def test_medida_eliminar_get_405(admin_client, medida):
    response = admin_client.get(reverse('panel_medida_eliminar', args=[medida.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_medida_eliminar_404(admin_client):
    response = admin_client.post(reverse('panel_medida_eliminar', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_categoria_crear_post_crea(admin_client):
    data = {'nombre': 'Ropa'}
    response = admin_client.post(reverse('panel_categoria_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_referencias')
    categoria = CategoriaModel.objects.get(nombre='Ropa')
    assert categoria.slug == 'ropa'


@pytest.mark.django_db
def test_categoria_crear_post_nombre_duplicado_invalido(admin_client, categoria):
    data = {'nombre': 'Ropa'}
    response = admin_client.post(reverse('panel_categoria_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe una categoría' in data_json['errors']['nombre'][0]


@pytest.mark.django_db
def test_categoria_eliminar_post_elimina(admin_client, categoria):
    response = admin_client.post(reverse('panel_categoria_eliminar', args=[categoria.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not CategoriaModel.objects.filter(id=categoria.id).exists()


@pytest.mark.django_db
def test_categoria_eliminar_post_con_subcategorias_bloquea(admin_client, subcategoria):
    categoria = subcategoria.categoria
    response = admin_client.post(reverse('panel_categoria_eliminar', args=[categoria.id]))
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Tiene subcategorías asociadas' in data_json['message']
    assert CategoriaModel.objects.filter(id=categoria.id).exists()


@pytest.mark.django_db
def test_categoria_eliminar_get_405(admin_client, categoria):
    response = admin_client.get(reverse('panel_categoria_eliminar', args=[categoria.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_categoria_eliminar_404(admin_client):
    response = admin_client.post(reverse('panel_categoria_eliminar', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_subcategoria_crear_post_crea(admin_client, categoria):
    data = {'categoria': categoria.id, 'nombre': 'Camisetas'}
    response = admin_client.post(reverse('panel_subcategoria_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_referencias')
    subcategoria = SubcategoriaModel.objects.get(nombre='Camisetas')
    assert subcategoria.categoria == categoria


@pytest.mark.django_db
def test_subcategoria_crear_post_nombre_duplicado_invalido(admin_client, subcategoria):
    data = {'categoria': subcategoria.categoria.id, 'nombre': 'Camisetas'}
    response = admin_client.post(reverse('panel_subcategoria_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Ya existe una subcategoría' in data_json['errors']['nombre'][0]


@pytest.mark.django_db
def test_subcategoria_crear_post_sin_categoria_invalido(admin_client):
    data = {'nombre': 'Camisetas'}
    response = admin_client.post(reverse('panel_subcategoria_nuevo'), data)
    data_json = response.json()
    assert data_json['success'] is False


@pytest.mark.django_db
def test_subcategoria_eliminar_post_elimina(admin_client, subcategoria):
    response = admin_client.post(reverse('panel_subcategoria_eliminar', args=[subcategoria.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not SubcategoriaModel.objects.filter(id=subcategoria.id).exists()


@pytest.mark.django_db
def test_subcategoria_eliminar_post_con_productos_bloquea(admin_client, producto):
    subcategoria = producto.subcategoria
    response = admin_client.post(reverse('panel_subcategoria_eliminar', args=[subcategoria.id]))
    data_json = response.json()
    assert data_json['success'] is False
    assert 'Tiene productos asociados' in data_json['message']
    assert SubcategoriaModel.objects.filter(id=subcategoria.id).exists()


@pytest.mark.django_db
def test_subcategoria_eliminar_get_405(admin_client, subcategoria):
    response = admin_client.get(reverse('panel_subcategoria_eliminar', args=[subcategoria.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_subcategoria_eliminar_404(admin_client):
    response = admin_client.post(reverse('panel_subcategoria_eliminar', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_lista_ventas_200(admin_client, venta):
    response = admin_client.get(reverse('panel_ventas'))
    assert response.status_code == 200
    assert list(response.context['ventas']) == [venta]
    content = response.content.decode()
    assert 'id="filtro-ventas"' in content
    assert 'id="orden-ventas"' in content
    assert f'venta-{venta.id}' in content


@pytest.mark.django_db
def test_lista_ventas_requiere_admin(client, cliente_client):
    assert client.get(reverse('panel_ventas')).status_code == 302
    assert cliente_client.get(reverse('panel_ventas')).status_code == 302


@pytest.mark.django_db
def test_venta_detalle_200(admin_client, venta):
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    assert response.context['venta'] == venta


@pytest.mark.django_db
def test_venta_detalle_inexistente_404(admin_client):
    response = admin_client.get(reverse('panel_venta_detalle', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_venta_modificar_get_200(admin_client, venta):
    response = admin_client.get(reverse('panel_venta_modificar', args=[venta.id]))
    assert response.status_code == 200
    assert response.context['form'].instance == venta


@pytest.mark.django_db
def test_venta_modificar_post_confirmada(admin_client, venta):
    data = {'estado': 'confirmada'}
    response = admin_client.post(reverse('panel_venta_modificar', args=[venta.id]), data)
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['redirect'] == reverse('panel_venta_detalle', args=[venta.id])
    venta.refresh_from_db()
    assert venta.estado == 'confirmada'


@pytest.mark.django_db
def test_venta_modificar_post_sin_cambios(admin_client, venta):
    data = {'estado': 'pendiente'}
    response = admin_client.post(reverse('panel_venta_modificar', args=[venta.id]), data)
    data_json = response.json()
    assert data_json['success'] is False
    assert data_json['message'] == 'No realizaste modificaciones.'


@pytest.mark.django_db
def test_venta_eliminar_post_elimina(admin_client, venta):
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not VentaModel.objects.filter(id=venta.id).exists()


@pytest.mark.django_db
def test_venta_eliminar_get_405(admin_client, venta):
    response = admin_client.get(reverse('panel_venta_eliminar', args=[venta.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_venta_modificar_post_cancelada_restaura_stock(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    data = {'estado': 'cancelada'}
    response = admin_client.post(reverse('panel_venta_modificar', args=[venta.id]), data)
    data_json = response.json()
    assert data_json['success'] is True
    venta.refresh_from_db()
    assert venta.estado == 'cancelada'
    producto.refresh_from_db()
    assert producto.stock == 10


@pytest.mark.django_db
def test_venta_eliminar_restaura_stock_y_mensaje_con_id(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert data_json['message'] == f'Venta #{venta.id} eliminada.'
    assert not VentaModel.objects.filter(id=venta.id).exists()
    producto.refresh_from_db()
    assert producto.stock == 10


@pytest.mark.django_db
def test_venta_eliminar_cancelada_no_duplica_stock(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    assert producto.stock == 10
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    producto.refresh_from_db()
    assert producto.stock == 10