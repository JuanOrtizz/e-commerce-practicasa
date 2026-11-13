from decimal import Decimal

import pytest
from django.db.models.deletion import ProtectedError

from productos.models import ProductoModel
from ventas.models import PagoModel
from ventas.services import crear_venta_confirmada_service, eliminar_venta_service


@pytest.mark.django_db
def test_producto_con_items_de_venta_no_se_puede_eliminar(carrito, producto, item, usuario, datos_checkout):
    crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    with pytest.raises(ProtectedError):
        producto.delete()


@pytest.mark.django_db
def test_subtotales_con_transferencia(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    venta_item = venta.items.get()

    assert venta_item.subtotal == Decimal('30000.00')
    assert venta_item.subtotal_transferencia == Decimal('27000.00')
    assert venta.subtotal == Decimal('30000.00')
    assert venta.subtotal_transferencia == Decimal('27000.00')
    assert venta.total_transferencia == Decimal('27000.00')


@pytest.mark.django_db
def test_borrar_venta_elimina_pagos_en_cascada(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='mp-cascada',
        monto=venta.total,
        external_reference=str(venta.id),
    )

    venta.delete()

    assert not PagoModel.objects.filter(payment_id='mp-cascada').exists()


@pytest.mark.django_db
def test_borrar_venta_con_items_no_elimina_producto(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')

    venta.delete()

    assert ProductoModel.objects.filter(pk=producto.pk).exists()


@pytest.mark.django_db
def test_eliminar_venta_service_pendiente_sin_pago_repone_stock(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    producto.refresh_from_db()
    assert producto.stock == 8

    eliminar_venta_service(venta)

    producto.refresh_from_db()
    assert producto.stock == 10


@pytest.mark.django_db
def test_eliminar_venta_service_borra_pagos_asociados(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='mp-rechazado',
        monto=venta.total,
        external_reference=str(venta.id),
    )

    eliminar_venta_service(venta)

    assert not PagoModel.objects.filter(payment_id='mp-rechazado').exists()