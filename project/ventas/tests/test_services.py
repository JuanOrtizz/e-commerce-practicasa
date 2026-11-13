from decimal import Decimal
import threading

import pytest
from django.db import close_old_connections, connections
from django.test import RequestFactory, override_settings

from carrito.models import CarritoItemModel
from carrito.services import agregar_item_service, get_o_crear_carrito_service
from ventas.models import PagoModel, VentaItemModel, VentaModel
from ventas.services import (
    _descontar_stock_venta_service,
    crear_pago_mercado_pago_service,
    crear_venta_confirmada_service,
    eliminar_venta_service,
    get_order_context_service,
    get_venta_context_service,
    permite_envio_domicilio_service,
    revertir_stock_venta_service,
    sincronizar_pago_service,
    venta_mp_en_curso,
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


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_crear_venta_acepta_mercado_pago(carrito, producto, item, usuario, datos_checkout):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    assert VentaModel.objects.count() == 1
    assert venta.metodo_pago == 'mercado_pago'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert venta.total == Decimal('30000')
    assert carrito.items.count() == 0


@override_settings(MP_ACCESS_TOKEN='')
@pytest.mark.django_db
def test_crear_venta_mercado_pago_sin_token_lo_rechaza(carrito, producto, item, usuario, datos_checkout):
    stock_inicial = producto.stock
    with pytest.raises(ValueError, match='Mercado Pago'):
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
def test_get_venta_context_usa_precios_snapshot(carrito, producto, item, usuario, datos_checkout):
    producto.promocion = '10%'
    producto.save()
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )

    ctx = get_venta_context_service(venta)
    data = ctx['items'][0]

    assert data['precio_original'] == producto.precio
    assert data['precio_transferencia_original'] == producto.precio_transferencia
    assert data['precio_unitario'] == producto.precio_final
    assert data['precio_transferencia_unitario'] == producto.precio_transferencia_final
    assert data['tiene_promocion_porcentaje'] is True
    assert data['ahorro'] == Decimal('0')
    assert data['ahorro_transferencia'] == Decimal('0')
    assert ctx['total'] == venta.subtotal
    assert ctx['total_transferencia'] == venta.subtotal_transferencia


@pytest.mark.django_db
def test_get_venta_context_calcula_ahorro_transferencia(carrito, producto, item, usuario, datos_checkout):
    producto.promocion = '2x1'
    producto.save()
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'transferencia'
    )

    ctx = get_venta_context_service(venta)
    data = ctx['items'][0]

    assert data['ahorro'] == producto.precio_final
    assert data['ahorro_transferencia'] == producto.precio_transferencia_final
    assert ctx['total_ahorro'] == producto.precio_final
    assert ctx['total_ahorro_transferencia'] == producto.precio_transferencia_final


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
    assert venta_item.precio_original_unitario == producto.precio
    assert venta_item.precio_transferencia_original_unitario == producto.precio_transferencia
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


@override_settings(DATOS_LOCAL={
    'nombre': 'Practicasa', 'ciudad': 'Nogoyá', 'direccion': 'Lavalle 994',
    'horario': '16:00 a 21:00 hs', 'whatsapp': '+54 9 3435 46-8162', 'mapa_url': '',
})
def test_whatsapp_link_service_construye_link_desde_datos_local():
    assert whatsapp_link_service() == 'https://wa.me/5493435468162'


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_expirar_pagos_vencidos_cancela_venta_y_reponer_stock(carrito, producto, item, usuario, datos_checkout):
    from datetime import timedelta

    from django.utils import timezone

    from ventas.services import expirar_pagos_vencidos_service

    stock_inicial = producto.stock
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-1', monto=venta.total, external_reference=str(venta.id),
    )
    VentaModel.objects.filter(pk=venta.pk).update(
        created_at=timezone.now() - timedelta(hours=5)
    )
    producto.refresh_from_db()
    assert producto.stock == stock_inicial - 2

    assert expirar_pagos_vencidos_service() is True

    pago.refresh_from_db()
    venta.refresh_from_db()
    producto.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.VENCIDO
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert producto.stock == stock_inicial


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_expirar_cancela_venta_con_pagos_rechazados(carrito, producto, item, usuario, datos_checkout):
    from datetime import timedelta

    from django.utils import timezone

    from ventas.services import expirar_pagos_vencidos_service

    stock_inicial = producto.stock
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.RECHAZADO,
        payment_id='2001', monto=venta.total, external_reference=str(venta.id),
    )
    VentaModel.objects.filter(pk=venta.pk).update(
        created_at=timezone.now() - timedelta(hours=5)
    )

    assert expirar_pagos_vencidos_service() is True

    venta.refresh_from_db()
    producto.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert producto.stock == stock_inicial


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_expirar_no_cancela_venta_con_pago_aprobado(carrito, item, usuario, datos_checkout):
    from datetime import timedelta

    from django.utils import timezone

    from ventas.services import expirar_pagos_vencidos_service

    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    aprobado = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.APROBADO,
        payment_id='1001', monto=venta.total, external_reference=str(venta.id),
    )
    pendiente = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-2', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.filter(pk=pendiente.pk).update(
        created_at=timezone.now() - timedelta(hours=5)
    )

    assert expirar_pagos_vencidos_service() is False

    aprobado.refresh_from_db()
    pendiente.refresh_from_db()
    venta.refresh_from_db()
    assert aprobado.estado == PagoModel.EstadoChoices.APROBADO
    assert pendiente.estado == PagoModel.EstadoChoices.PENDIENTE
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_expirar_pagos_vencidos_no_toca_venta_ya_cancelada(carrito, item, usuario, datos_checkout):
    from datetime import timedelta

    from django.utils import timezone

    from ventas.services import expirar_pagos_vencidos_service

    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save()
    pago = PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-3', monto=venta.total, external_reference=str(venta.id),
    )
    PagoModel.objects.filter(pk=pago.pk).update(
        created_at=timezone.now() - timedelta(hours=5)
    )

    assert expirar_pagos_vencidos_service() is False
    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.PENDIENTE


@override_settings(MP_ACCESS_TOKEN='TEST-123')
@pytest.mark.django_db
def test_crear_preferencia_incluye_payer_email(carrito, item, usuario, datos_checkout):
    from ventas import mp as _mp

    class _FakePreference:
        def __init__(self):
            self.data = None

        def create(self, data):
            self.data = data
            return {'status': 201, 'response': {'id': 'pref-1', 'init_point': 'https://pay.mp/pref-1'}}

    class _FakeSdk:
        def __init__(self):
            self._pref = _FakePreference()

        def preference(self):
            return self._pref

    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'mercado_pago')
    sdk = _FakeSdk()
    _mp.crear_preferencia_service(sdk, venta, 4, '', 'http://back')
    assert sdk._pref.data['payer'] == {'email': venta.email}


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_crear_pago_usa_init_point_con_credenciales_de_prueba(
    monkeypatch, carrito, item, usuario, datos_checkout
):
    from ventas import mp as _mp

    monkeypatch.setattr(_mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        _mp, 'crear_preferencia_service',
        lambda *a, **k: {
            'id': 'pref-1',
            'init_point': 'https://www.mercadopago.com.ar/pay',
            'sandbox_init_point': 'https://sandbox.mercadopago.com.ar/pay',
        },
    )
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'mercado_pago')
    url = crear_pago_mercado_pago_service(venta, RequestFactory().get('/'))
    assert url == 'https://www.mercadopago.com.ar/pay'


@override_settings(MP_ACCESS_TOKEN='APP_USR-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_crear_pago_usa_init_point_con_token_de_produccion(
    monkeypatch, carrito, item, usuario, datos_checkout
):
    from ventas import mp as _mp

    monkeypatch.setattr(_mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        _mp, 'crear_preferencia_service',
        lambda *a, **k: {
            'id': 'pref-1',
            'init_point': 'https://www.mercadopago.com.ar/pay',
            'sandbox_init_point': 'https://sandbox.mercadopago.com.ar/pay',
        },
    )
    venta = crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'mercado_pago')
    url = crear_pago_mercado_pago_service(venta, RequestFactory().get('/'))
    assert url == 'https://www.mercadopago.com.ar/pay'


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_descontar_stock_falla_si_otro_cliente_compro_la_ultima_unidad(
    carrito, producto, item, usuario, datos_checkout
):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    producto.stock = 1
    producto.save(update_fields=['stock'])

    with pytest.raises(ValueError, match='Otro cliente compró la última unidad'):
        _descontar_stock_venta_service(venta)

    producto.refresh_from_db()
    assert producto.stock == 1


@pytest.mark.django_db(transaction=True)
def test_descontar_stock_es_atomico_con_dos_compras_simultaneas(usuario, producto):
    producto.stock = 1
    producto.save(update_fields=['stock'])

    ventas = []
    for _ in range(2):
        venta = VentaModel.objects.create(
            usuario=usuario,
            metodo_envio=VentaModel.MetodoEnvioChoices.RETIRO_LOCAL,
            metodo_pago=VentaModel.MetodoPagoChoices.EFECTIVO,
            nombre='Cliente',
            email='cliente@example.com',
            telefono='3434567890',
            subtotal=Decimal('100'),
            total=Decimal('100'),
        )
        VentaItemModel.objects.create(
            venta=venta,
            producto=producto,
            cantidad=1,
            precio_unitario=Decimal('100'),
            precio_transferencia_unitario=Decimal('90'),
        )
        ventas.append(venta)

    resultados = []
    barrera = threading.Barrier(2)

    def _intentar(venta):
        close_old_connections()
        try:
            barrera.wait(timeout=10)
            _descontar_stock_venta_service(venta)
            resultados.append('ok')
        except ValueError:
            resultados.append('sin_stock')
        finally:
            connections.close_all()

    hilos = [threading.Thread(target=_intentar, args=(venta,)) for venta in ventas]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=15)

    producto.refresh_from_db()
    assert resultados.count('ok') == 1
    assert resultados.count('sin_stock') == 1
    assert producto.stock == 0


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_no_permite_mas_de_dos_pedidos_mp_pendientes(
    carrito, producto, usuario, datos_checkout
):
    for _ in range(2):
        CarritoItemModel.objects.create(
            carrito=carrito, producto=producto, cantidad=1
        )
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'mercado_pago'
        )

    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    with pytest.raises(ValueError, match='2 pedidos pendientes'):
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'mercado_pago'
        )

    assert VentaModel.objects.filter(usuario=usuario).count() == 2


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_limite_pendientes_ignora_pedidos_vencidos(
    carrito, producto, usuario, datos_checkout
):
    from datetime import timedelta

    from django.utils import timezone

    for _ in range(2):
        CarritoItemModel.objects.create(
            carrito=carrito, producto=producto, cantidad=1
        )
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'mercado_pago'
        )

    VentaModel.objects.filter(usuario=usuario).update(
        created_at=timezone.now() - timedelta(hours=5)
    )

    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    assert venta is not None
    assert VentaModel.objects.filter(usuario=usuario).count() == 3


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_limite_pendientes_cuenta_cualquier_metodo_de_pago(
    carrito, producto, usuario, datos_checkout
):
    for _ in range(2):
        CarritoItemModel.objects.create(
            carrito=carrito, producto=producto, cantidad=1
        )
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'efectivo'
        )

    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    with pytest.raises(ValueError, match='2 pedidos pendientes'):
        crear_venta_confirmada_service(
            usuario, datos_checkout, 'retiro_local', 'transferencia'
        )

    assert VentaModel.objects.filter(usuario=usuario).count() == 2


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_sincronizar_pago_guarda_datos_de_tarjeta_y_cuotas(
    carrito, item, usuario, datos_checkout
):
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    pago = PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        monto=venta.total,
        external_reference=str(venta.id),
    )
    pago_data = {
        'id': '99001',
        'status': 'approved',
        'external_reference': str(venta.id),
        'transaction_amount': str(venta.total),
        'payment_method_id': 'visa',
        'installments': 3,
        'transaction_details': {
            'installment_amount': '11000.00',
            'total_paid_amount': '33000.00',
        },
        'card': {'last_four_digits': '1234'},
    }

    sincronizar_pago_service(pago_data, venta, RequestFactory().get('/'))

    pago.refresh_from_db()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO
    assert pago.metodo_pago_mp == 'visa'
    assert pago.cuotas == 3
    assert pago.monto_cuota == Decimal('11000.00')
    assert pago.total_pagado == Decimal('33000.00')
    assert pago.tarjeta_ultimos_digitos == '1234'
    assert pago.interes == Decimal('3000.00')


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_eliminar_venta_mp_en_curso_lanza_error(
    carrito, producto, item, usuario, datos_checkout
):
    stock_tras_compra = producto.stock - 2
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='3776797576-1',
        monto=venta.total,
        external_reference=str(venta.id),
    )
    assert venta_mp_en_curso(venta) is True

    with pytest.raises(ValueError, match='pago de Mercado Pago en curso'):
        eliminar_venta_service(venta)

    assert VentaModel.objects.filter(pk=venta.pk).exists()
    producto.refresh_from_db()
    assert producto.stock == stock_tras_compra


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_eliminar_venta_mp_vencida_permite_eliminar(
    carrito, producto, item, usuario, datos_checkout
):
    from datetime import timedelta

    from django.utils import timezone

    stock_inicial = producto.stock
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='3776797576-1',
        monto=venta.total,
        external_reference=str(venta.id),
    )
    VentaModel.objects.filter(pk=venta.pk).update(
        created_at=timezone.now() - timedelta(hours=5)
    )
    venta.refresh_from_db()
    assert venta_mp_en_curso(venta) is False

    eliminar_venta_service(venta)

    assert not VentaModel.objects.filter(pk=venta.pk).exists()
    producto.refresh_from_db()
    assert producto.stock == stock_inicial
