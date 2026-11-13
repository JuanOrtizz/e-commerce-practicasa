from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
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
from ventas.models import PagoModel, VentaItemModel, VentaModel


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
def test_dashboard_recaudado_solo_confirmadas(admin_client, venta):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    VentaModel.objects.create(
        usuario=venta.usuario,
        estado=VentaModel.EstadoChoices.CANCELADA,
        metodo_envio=VentaModel.MetodoEnvioChoices.RETIRO_LOCAL,
        metodo_pago=VentaModel.MetodoPagoChoices.EFECTIVO,
        nombre='Cliente Test',
        email='cliente@example.com',
        telefono='1122334455',
        subtotal=Decimal('10000'),
        costo_envio=Decimal('0'),
        total=Decimal('10000'),
    )
    response = admin_client.get(reverse('panel_inicio'))
    assert response.context['ventas_recaudado_mes'] == Decimal('30000')


@pytest.mark.django_db
def test_dashboard_ventas_por_mes_incluye_monto(admin_client, venta):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    response = admin_client.get(reverse('panel_inicio'))
    assert response.context['ventas_por_mes'][-1][1] == Decimal('30000')


@pytest.mark.django_db
def test_dashboard_productos_mas_vendidos_por_unidades(admin_client, venta, producto):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    response = admin_client.get(reverse('panel_inicio'))
    assert response.context['productos_mas_vendidos'] == [[producto.nombre, 2]]


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
def test_producto_eliminar_post_con_ventas_bloquea(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    response = admin_client.post(reverse('panel_producto_eliminar', args=[producto.id]))
    data_json = response.json()
    assert data_json['success'] is False
    assert 'ventas' in data_json['message']
    assert ProductoModel.objects.filter(id=producto.id).exists()


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
def test_lista_ventas_marca_pago_duplicado(admin_client, venta):
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12002', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_ventas'))
    assert response.status_code == 200
    assert response.context['ventas'].get(id=venta.id).pagos_aprobados == 2
    assert 'Pago duplicado' in response.content.decode()


@pytest.mark.django_db
def test_lista_ventas_un_solo_aprobado_sin_badge_duplicado(admin_client, venta):
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='11999', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_ventas'))
    assert response.status_code == 200
    assert 'Pago duplicado' not in response.content.decode()


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
def test_venta_detalle_muestra_pagos(admin_client, venta):
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='11999', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Pagos' in content
    assert '12001' in content
    assert '11999' in content
    assert 'Aprobado' in content
    assert 'Rechazado' in content


@pytest.mark.django_db
def test_venta_detalle_efectivo_sin_pagos_no_muestra_seccion(admin_client, venta):
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    assert 'Pagos' not in response.content.decode()


@pytest.mark.django_db
def test_venta_detalle_marca_pago_duplicado(admin_client, venta):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12002', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    assert 'Pago duplicado' in response.content.decode()


@pytest.mark.django_db
def test_venta_detalle_un_solo_aprobado_sin_badge_duplicado(admin_client, venta):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='12001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='11999', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    assert 'Pago duplicado' not in response.content.decode()


@pytest.mark.django_db
def test_venta_detalle_inexistente_404(admin_client):
    response = admin_client.get(reverse('panel_venta_detalle', args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_venta_detalle_muestra_boton_reembolsar_pago_aprobado(admin_client, venta):
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_venta_detalle', args=[venta.id]))
    assert response.status_code == 200
    assert 'Marcar reembolsado' in response.content.decode()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_pago_estado_marca_reembolsado(admin_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'reembolsado'}
    )
    assert response.status_code == 200
    assert response.json()['success'] is True
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_pago_estado_reembolsado_envia_email_a_comercio_y_cliente(admin_client, venta):
    mail.outbox.clear()
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13002', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'reembolsado'}
    )
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert len(mail.outbox) == 2
    destinatarios = [m.to for m in mail.outbox]
    assert all(len(destino) == 1 for destino in destinatarios)
    assert 'reembolsado' in mail.outbox[0].subject.lower()
    assert 'reembolsado' in mail.outbox[1].subject.lower()
    htmls = [m.alternatives[0][0] for m in mail.outbox]
    assert any('Lamentamos los inconvenientes' in html for html in htmls)
    assert any('Acción sugerida' in html for html in htmls)
    assert htmls[0] != htmls[1]


@pytest.mark.django_db
def test_pago_estado_vuelve_a_aprobado(admin_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.REEMBOLSADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'aprobado'}
    )
    assert response.status_code == 200
    assert response.json()['success'] is True
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO


@pytest.mark.django_db
def test_pago_estado_rechaza_estado_invalido(admin_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'pendiente'}
    )
    assert response.json()['success'] is False
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO


@pytest.mark.django_db
def test_pago_estado_rechaza_pago_no_aprobado(admin_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'reembolsado'}
    )
    assert response.json()['success'] is False
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.RECHAZADO


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_pago_estado_quita_badge_pago_duplicado(admin_client, venta):
    primero = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13002', monto=venta.total, external_reference=str(venta.id),
    )
    assert venta.tiene_pagos_duplicados is True

    admin_client.post(
        reverse('panel_pago_estado', args=[primero.id]), {'estado': 'reembolsado'}
    )
    assert venta.tiene_pagos_duplicados is False


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@pytest.mark.django_db
def test_pago_reembolsado_ultimo_aprobado_cancela_venta_y_repone_stock(admin_client, venta, producto):
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    VentaItemModel.objects.create(
        venta=venta, producto=producto, nombre_producto=producto.nombre,
        cantidad=2, precio_unitario=producto.precio,
        precio_transferencia_unitario=producto.precio_transferencia,
        precio_original_unitario=producto.precio,
    )
    producto.stock -= 2
    producto.save(update_fields=['stock'])
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )

    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'reembolsado'}
    )
    assert response.json()['success'] is True
    venta.refresh_from_db()
    producto.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert producto.stock == 10


@pytest.mark.django_db
def test_pago_aprobado_reactiva_venta_cancelada_y_descuenta_stock(admin_client, venta, producto):
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    VentaItemModel.objects.create(
        venta=venta, producto=producto, nombre_producto=producto.nombre,
        cantidad=2, precio_unitario=producto.precio,
        precio_transferencia_unitario=producto.precio_transferencia,
        precio_original_unitario=producto.precio,
    )
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.REEMBOLSADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )

    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'aprobado'}
    )
    assert response.json()['success'] is True
    venta.refresh_from_db()
    producto.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    assert producto.stock == 8


@pytest.mark.django_db
def test_pago_aprobado_sin_stock_no_reactiva_venta(admin_client, venta, producto):
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    VentaItemModel.objects.create(
        venta=venta, producto=producto, nombre_producto=producto.nombre,
        cantidad=20, precio_unitario=producto.precio,
        precio_transferencia_unitario=producto.precio_transferencia,
        precio_original_unitario=producto.precio,
    )
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.REEMBOLSADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )

    response = admin_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'aprobado'}
    )
    assert response.json()['success'] is False
    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO


@pytest.mark.django_db
def test_pago_estado_requiere_admin(cliente_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = cliente_client.post(
        reverse('panel_pago_estado', args=[pago.id]), {'estado': 'reembolsado'}
    )
    assert response.status_code == 302
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO


@pytest.mark.django_db
def test_pago_estado_get_405(admin_client, venta):
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='13001', monto=venta.total, external_reference=str(venta.id),
    )
    response = admin_client.get(reverse('panel_pago_estado', args=[pago.id]))
    assert response.status_code == 405


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
def test_venta_eliminar_con_pago_pendiente_elimina_y_repone_stock(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    pago = PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-1',
        monto=venta.total,
        external_reference=str(venta.id),
    )
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not VentaModel.objects.filter(id=venta.id).exists()
    assert not PagoModel.objects.filter(id=pago.id).exists()
    producto.refresh_from_db()
    assert producto.stock == 10


@pytest.mark.django_db
def test_venta_eliminar_con_pago_aprobado_elimina_venta_y_pagos(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='mp-1',
        monto=venta.total,
        external_reference=str(venta.id),
    )
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not VentaModel.objects.filter(id=venta.id).exists()
    assert not PagoModel.objects.filter(external_reference=str(venta.id)).exists()
    producto.refresh_from_db()
    assert producto.stock == 8


@pytest.mark.django_db
def test_venta_eliminar_confirmada_con_pago_aprobado_no_repone_stock(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='mp-2',
        monto=venta.total,
        external_reference=str(venta.id),
    )
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not VentaModel.objects.filter(id=venta.id).exists()
    assert not PagoModel.objects.filter(external_reference=str(venta.id)).exists()
    producto.refresh_from_db()
    assert producto.stock == 8


@pytest.mark.django_db
def test_venta_eliminar_requiere_admin(cliente_client, venta):
    response = cliente_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    assert response.status_code == 302
    assert VentaModel.objects.filter(id=venta.id).exists()


@pytest.mark.django_db
def test_venta_eliminar_inexistente_404(admin_client):
    response = admin_client.post(reverse('panel_venta_eliminar', args=[999999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_venta_eliminar_confirmada_no_restaura_stock(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()
    assert data_json['success'] is True
    assert not VentaModel.objects.filter(id=venta.id).exists()
    producto.refresh_from_db()
    assert producto.stock == 8


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


def _marcar_venta_mp_con_pago_pendiente(venta):
    venta.metodo_pago = VentaModel.MetodoPagoChoices.MERCADO_PAGO
    venta.save(update_fields=['metodo_pago'])
    return PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='3776797576-1',
        monto=venta.total,
        external_reference=str(venta.id),
    )


@pytest.mark.django_db
def test_venta_eliminar_con_pago_mp_en_curso_bloquea(admin_client, producto, venta):
    VentaItemModel.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        precio_unitario=Decimal('15000'),
        precio_transferencia_unitario=Decimal('13500'),
    )
    producto.stock = 8
    producto.save(update_fields=['stock'])
    _marcar_venta_mp_con_pago_pendiente(venta)

    response = admin_client.post(reverse('panel_venta_eliminar', args=[venta.id]))
    data_json = response.json()

    assert data_json['success'] is False
    assert 'Mercado Pago en curso' in data_json['message']
    assert VentaModel.objects.filter(id=venta.id).exists()
    producto.refresh_from_db()
    assert producto.stock == 8


@pytest.mark.django_db
def test_venta_modificar_con_pago_mp_en_curso_bloquea(admin_client, venta):
    _marcar_venta_mp_con_pago_pendiente(venta)

    response = admin_client.post(
        reverse('panel_venta_modificar', args=[venta.id]), {'estado': 'confirmada'}
    )
    data_json = response.json()

    assert data_json['success'] is False
    assert 'Mercado Pago en curso' in data_json['message']
    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE