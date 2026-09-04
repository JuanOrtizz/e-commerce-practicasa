from decimal import Decimal

import pytest

from ventas.models import VentaModel
from ventas.services import crear_venta_confirmada_service


@pytest.mark.django_db
def test_cancelar_venta_restaura_stock(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    producto.refresh_from_db()
    stock_tras_compra = producto.stock
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    assert producto.stock == stock_tras_compra + 2


@pytest.mark.django_db
def test_cancelar_dos_veces_no_duplica_stock(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    stock_tras_cancelar = producto.stock
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    assert producto.stock == stock_tras_cancelar


@pytest.mark.django_db
def test_reapertura_de_cancelada_no_redescuenta_stock(carrito, producto, item, usuario, datos_checkout):
    stock_inicial = producto.stock
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    assert producto.stock == stock_inicial
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])
    producto.refresh_from_db()
    assert producto.stock == stock_inicial