from decimal import Decimal

import pytest

from carrito.services import agregar_item_service, get_o_crear_carrito_service
from ventas.models import VentaItemModel, VentaModel
from ventas.services import (
    crear_venta_confirmada_service,
    get_order_context_service,
    permite_envio_domicilio_service,
    revertir_stock_venta_service,
    whatsapp_link_service,
)


@pytest.mark.django_db
def test_crear_venta_confirmada_descarta_stock_y_vacia_carrito(carrito, producto, item, usuario, datos_checkout):
    stock_inicial = producto.stock
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )

    assert VentaModel.objects.count() == 1
    assert venta.usuario == usuario
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert venta.metodo_envio == 'retiro_local'
    assert venta.metodo_pago == 'efectivo'
    assert venta.subtotal == Decimal('30000')
    assert venta.costo_envio == Decimal('0')
    assert venta.total == Decimal('30000')
    assert venta.direccion == datos_checkout['direccion']
    assert venta.numero == datos_checkout['numero']

    assert VentaItemModel.objects.filter(venta=venta).count() == 1
    venta_item = venta.items.first()
    assert venta_item.producto == producto
    assert venta_item.nombre_producto == producto.nombre
    assert venta_item.promocion is None
    assert venta_item.cantidad == 2
    assert venta_item.precio_unitario == producto.precio_final

    producto.refresh_from_db()
    assert producto.stock == stock_inicial - 2

    assert carrito.items.count() == 0


@pytest.mark.django_db
def test_crear_venta_envio_domicilio_costo_cero(carrito, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'envio_domicilio', 'efectivo'
    )
    assert venta.metodo_envio == 'envio_domicilio'
    assert venta.costo_envio == Decimal('0')
    assert venta.total == venta.subtotal


@pytest.mark.django_db
def test_crear_venta_carrito_vacio_lanza_error(carrito, usuario, datos_checkout):
    with pytest.raises(ValueError):
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'efectivo'
        )


@pytest.mark.django_db
def test_crear_venta_rechaza_mercado_pago(carrito, producto, item, usuario, datos_checkout):
    stock_inicial = producto.stock
    with pytest.raises(ValueError):
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'mercado_pago'
        )
    assert VentaModel.objects.count() == 0
    producto.refresh_from_db()
    assert producto.stock == stock_inicial
    assert carrito.items.count() == 1


@pytest.mark.django_db
def test_get_order_context_usa_carrito(carrito, item, usuario):
    ctx = get_order_context_service(usuario)
    assert ctx['cantidad_items'] == 1
    assert ctx['total'] == Decimal('30000')


@pytest.mark.django_db
def test_revertir_stock_devuelve_stock_a_productos(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    producto.refresh_from_db()
    stock_tras_compra = producto.stock
    revertir_stock_venta_service(venta)
    producto.refresh_from_db()
    assert producto.stock == stock_tras_compra + 2
    assert producto.stock == 10


@pytest.mark.django_db
def test_crear_venta_snapshotea_promocion_2x1(carrito, producto, item, usuario, datos_checkout):
    producto.promocion = '2x1'
    producto.save()
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    venta_item = venta.items.first()
    assert venta_item.promocion == '2x1'
    assert venta_item.etiqueta_promocion == '2x1'
    assert venta_item.cantidad_paga == 1
    assert venta_item.subtotal == producto.precio_final
    assert venta.subtotal == producto.precio_final
    assert venta.total == venta.subtotal


@pytest.mark.django_db
def test_crear_venta_snapshotea_promocion_porcentaje(carrito, producto, item, usuario, datos_checkout):
    producto.promocion = '10%'
    producto.save()
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    venta_item = venta.items.first()
    assert venta_item.promocion == '10%'
    assert venta_item.etiqueta_promocion == '10% OFF'
    assert venta_item.cantidad_paga == 2
    assert venta_item.precio_unitario == producto.precio_final
    assert venta_item.subtotal == producto.precio_final * 2


@pytest.mark.django_db
def test_nombre_producto_snapshot_no_cambia_con_el_producto(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    venta_item = venta.items.first()
    nombre_original = venta_item.nombre_producto
    producto.nombre = 'Nombre cambiado'
    producto.save()
    venta_item.refresh_from_db()
    assert venta_item.nombre_producto == nombre_original


def test_permite_envio_domicilio_service_3150():
    assert permite_envio_domicilio_service('3150') is True
    assert permite_envio_domicilio_service(' 3150 ') is True


def test_permite_envio_domicilio_service_otros_codigos():
    assert permite_envio_domicilio_service('3156') is False
    assert permite_envio_domicilio_service('3100') is False
    assert permite_envio_domicilio_service('') is False
    assert permite_envio_domicilio_service(None) is False


def test_whatsapp_link_service_construye_link_desde_datos_local():
    assert whatsapp_link_service() == 'https://wa.me/543435468162'
