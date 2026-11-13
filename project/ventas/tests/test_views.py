import hashlib
import hmac
import json
import time

import pytest

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from usuarios.models import UsuarioModel
from ventas import mp
from ventas.models import PagoModel, VentaModel
from ventas.services import crear_venta_confirmada_service


@pytest.fixture
def client_logueado(client, usuario, item):
    client.force_login(usuario)
    return client


def test_checkout_requiere_login(client):
    response = client.get('/ventas/checkout/')
    assert response.status_code == 302
    assert '/usuarios/login/' in response.headers.get('Location', '')


def test_checkout_ajax_sin_stock_devuelve_json_con_redirect(client_logueado, producto):
    producto.stock = 0
    producto.save()
    response = client_logueado.post(
        '/ventas/checkout/',
        {},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is False
    assert data['redirect'] == '/carrito/'
    assert 'sin stock' in data['message'].lower()


def test_checkout_get(client_logueado):
    response = client_logueado.get('/ventas/checkout/')
    assert response.status_code == 200
    assert b'Datos de facturaci' in response.content


def test_checkout_resumen_muestra_detalle_compacto(client_logueado, item, producto):
    producto.promocion = '2x1'
    producto.save(update_fields=['promocion'])
    item.color_nombre = 'Rojo'
    item.color_hex = '#ff0000'
    item.medida_nombre = 'M'
    item.save(update_fields=['color_nombre', 'color_hex', 'medida_nombre'])

    response = client_logueado.get('/ventas/checkout/')
    content = response.content.decode()
    assert 'Cant. 2' in content
    assert 'Rojo' in content
    assert '#ff0000' in content
    assert 'M' in content
    assert '2x1' in content
    assert 'Ahorrás' in content
    assert 'Subtotal transferencia' in content
    assert 'Ahorro total' in content
    assert 'Total transferencia' in content


def test_checkout_carrito_vacio_redirige(client, usuario):
    client.force_login(usuario)
    response = client.get('/ventas/checkout/')
    assert response.status_code == 302
    assert response.url == reverse('ver_carrito')


def test_checkout_con_item_sin_stock_redirige_al_carrito(client_logueado, item, producto):
    producto.stock = 0
    producto.save(update_fields=['stock'])
    response = client_logueado.get('/ventas/checkout/')
    assert response.status_code == 302
    assert response.url == reverse('ver_carrito')


def test_checkout_post_valido_redirige_envio(client_logueado, datos_checkout):
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 302
    assert response.url == '/ventas/envio/'


def test_checkout_post_invalido_muestra_errores(client_logueado):
    response = client_logueado.post('/ventas/checkout/', {
        'nombre': 'X',
        'email': 'mal',
        'telefono': '123',
    })
    assert response.status_code == 200


def test_checkout_post_numero_invalido_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'numero': 'abc'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200
    assert b'solo d' in response.content


def test_checkout_post_cp_corto_muestra_error_de_4_digitos(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'codigo_postal': '315'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200
    assert b'4 d' in response.content


@pytest.mark.parametrize('codigo_postal', ['315a', 'a315', '31-5'])
def test_checkout_post_cp_con_no_digitos_muestra_error_de_numeros(
    client_logueado, datos_checkout, codigo_postal
):
    datos_checkout = {**datos_checkout, 'codigo_postal': codigo_postal}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200
    assert b'solo n' in response.content


def test_checkout_post_direccion_invalida_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'direccion': 'x!!!'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200


def test_checkout_post_ciudad_invalida_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'ciudad': 'Nogoy@123'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200
    assert b'ciudad no es v' in response.content


def test_checkout_post_ajax_valido_devuelve_json_redirect(client_logueado, datos_checkout):
    response = client_logueado.post(
        '/ventas/checkout/', datos_checkout, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['redirect'] == reverse('envio')


def test_checkout_post_ajax_invalido_devuelve_errores_json(client_logueado):
    response = client_logueado.post(
        '/ventas/checkout/', {
            'nombre': 'X',
            'email': 'mal',
            'telefono': '123',
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is False
    assert 'nombre' in data['errors']
    assert 'email' in data['errors']


def test_envio_requiere_datos_previos(client_logueado):
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 302
    assert response.url == '/ventas/checkout/'


def _set_session_datos(client, **kwargs):
    session = client.session
    session['datos_venta'] = {
        'nombre': 'Cliente Test',
        'email': 'cliente@example.com',
        'telefono': '3434567890',
        'direccion': 'Calle 1',
        'numero': '123',
        'ciudad': 'Nogoyá',
        'provincia': 'Entre Ríos',
        'codigo_postal': '3150',
        'notas': '',
        'metodo_pago': 'efectivo',
    }
    session['datos_venta'].update(kwargs)
    session.save()


def test_envio_get_muestra_retiro_y_sucursal_deshabilitada(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'Retiro en el local' in response.content
    assert 'Envío a domicilio/sucursal (Correo Argentino)'.encode() in response.content


def test_envio_get_envio_domicilio_con_cp_3150(client_logueado):
    _set_session_datos(client_logueado, codigo_postal='3150', metodo_envio='envio_domicilio')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'Env' in response.content and b'domicilio' in response.content


def test_envio_get_coordinar_entrega_con_cp_3156(client_logueado):
    _set_session_datos(client_logueado, codigo_postal='3156', ciudad='Nogoyá', metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'coordinar_entrega' in response.content
    assert b'Coordinar entrega' in response.content
    assert b'localidad (Hern' in response.content


def test_envio_get_no_muestra_coordinar_entrega_con_cp_3150(client_logueado):
    _set_session_datos(client_logueado, codigo_postal='3150', metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'coordinar_entrega' not in response.content


def test_confirmacion_get_coordinar_entrega_muestra_efectivo(client_logueado):
    _set_session_datos(client_logueado, codigo_postal='3164', ciudad='Nogoyá', metodo_envio='coordinar_entrega')
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 200
    assert b'entrega (Ram' in response.content
    assert b'Efectivo' in response.content
    assert b'Mercado Pago' not in response.content


def test_confirmacion_get_retiro_local_muestra_efectivo(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 200
    assert b'Efectivo' in response.content
    assert b'Forma de pago' in response.content
    assert b'Mercado Pago' not in response.content


def test_confirmacion_get_domicilio_muestra_efectivo(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='envio_domicilio')
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 200
    assert b'Efectivo' in response.content
    assert b'Mercado Pago' not in response.content


@pytest.mark.parametrize('metodo_pago', ['efectivo', 'transferencia'])
def test_confirmacion_muestra_solo_precio_transferencia(client_logueado, metodo_pago):
    _set_session_datos(
        client_logueado, metodo_envio='retiro_local', metodo_pago=metodo_pago
    )
    response = client_logueado.get('/ventas/confirmacion/')
    content = response.content.decode()
    assert '$13.500,00 con transferencia' in content
    assert '$15.000,00' not in content
    assert 'Subtotal transferencia' not in content
    assert 'Total transferencia' not in content


def test_confirmacion_mercado_pago_muestra_solo_precio_normal(client_logueado):
    _set_session_datos(
        client_logueado, metodo_envio='retiro_local', metodo_pago='mercado_pago'
    )
    response = client_logueado.get('/ventas/confirmacion/')
    content = response.content.decode()
    assert '$15.000,00' in content
    assert 'con transferencia' not in content
    assert 'Subtotal transferencia' not in content
    assert 'Total transferencia' not in content


def test_flujo_completo_efectivo(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    response = client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    assert response.status_code == 302
    assert response.url == '/ventas/metodo-pago/'

    response = client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'efectivo'})
    assert response.status_code == 302
    assert response.url == '/ventas/confirmacion/'

    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 302
    assert response.url.startswith('/ventas/pago-local/')

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'efectivo'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DATOS_LOCAL={
        'nombre': 'Practicasa',
        'ciudad': 'Nogoyá',
        'direccion': 'Lavalle 994',
        'horario': '16:00 a 21:00 hs',
        'whatsapp': '+54 9 3435 46-8162',
        'mapa_url': '',
    },
    DATOS_BANCARIOS={
        'alias': 'practicasa',
        'cvu': '0000003100039988324864',
        'nombre': 'Maria Jose Amestoy',
        'banco': 'Mercado Pago',
        'cuil': '27-26874896-8',
    },
)
def test_flujo_completo_transferencia_muestra_datos_bancarios(
    client_logueado, datos_checkout, carrito
):
    mail.outbox.clear()
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'transferencia'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 302
    assert response.url.startswith('/ventas/pago-local/')

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'transferencia'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert carrito.items.count() == 0
    assert len(mail.outbox) == 2

    response = client_logueado.get(f'/ventas/pago-local/{venta.id}/')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Nuestros datos bancarios' in content
    assert 'ventas-datos-bancarios' in content
    assert 'practicasa' in content
    assert '0000003100039988324864' in content
    assert 'Enviar Comprobante de pago' in content
    assert '+54 9 3435 46-8162' in content
    assert 'Detalle del pedido' in content
    assert 'ventas-resumen' in content
    assert '$13.500,00 con transferencia' in content
    assert '$15.000,00' not in content


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
def test_metodo_pago_mercado_pago_redirige_a_confirmacion(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'envio_domicilio'})
    response = client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
    assert response.status_code == 302
    assert response.url == '/ventas/confirmacion/'
    assert VentaModel.objects.count() == 0


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_COMERCIO='comercio@test.com',
)
def test_flujo_completo_efectivo_envia_factura(client_logueado, datos_checkout):
    from django.conf import settings
    from django.core import mail

    mail.outbox.clear()
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'efectivo'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 302

    venta = VentaModel.objects.get()
    asuntos = [m.subject for m in mail.outbox]
    destinatarios = [m.to for m in mail.outbox]
    assert len(mail.outbox) == 2
    assert f'Tu pedido #{venta.id} | Practicasa' in asuntos
    assert f'Nuevo pedido #{venta.id} | Practicasa' in asuntos
    assert [venta.email] in destinatarios
    assert [settings.EMAIL_COMERCIO] in destinatarios

    html = mail.outbox[0].alternatives[0][0]
    assert f'#{venta.id}' in html
    assert 'Camiseta' in html
    assert 'Cliente Test' in html


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
def test_confirmacion_mercado_pago_redirige_a_mp_sin_email(client_logueado, datos_checkout, monkeypatch):
    mail.outbox.clear()
    preference_id = '3776797576-bbd0f01a-3ccd-4f0a-a584-f9e736c0a858'
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'crear_preferencia_service',
        lambda sdk, venta, ttl, webhook_url, back_url: {
            'id': preference_id, 'init_point': f'https://pay.mp/{preference_id}',
        },
    )

    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 302
    assert response.url == f'https://pay.mp/{preference_id}'

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'mercado_pago'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    pago = PagoModel.objects.get(venta=venta)
    assert pago.estado == PagoModel.EstadoChoices.PENDIENTE
    assert pago.mp_preference_id == preference_id
    assert pago.monto == venta.total
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_confirmacion_mp_falla_y_el_carrito_queda_intacto(client_logueado, carrito, item, datos_checkout, monkeypatch):
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())

    def _preferencia_que_falla(*args, **kwargs):
        raise mp.MercadoPagoError('boom')

    monkeypatch.setattr(mp, 'crear_preferencia_service', _preferencia_que_falla)

    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 200
    assert b'No pudimos iniciar el pago' in response.content
    assert VentaModel.objects.count() == 0
    assert carrito.items.count() == 1


def test_confirmacion_sin_metodo_pago_redirige_metodo_pago(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    session = client_logueado.session
    session['datos_venta'].pop('metodo_pago', None)
    session.save()
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 302
    assert response.url == '/ventas/metodo-pago/'
    assert VentaModel.objects.count() == 0


def test_metodo_pago_requiere_datos_previos(client_logueado):
    response = client_logueado.get('/ventas/metodo-pago/')
    assert response.status_code == 302
    assert response.url == '/ventas/envio/'


@override_settings(MP_ACCESS_TOKEN='TEST-123')
def test_metodo_pago_get_muestra_efectivo_y_mercado_pago_habilitado(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/metodo-pago/')
    assert response.status_code == 200
    assert b'Efectivo' in response.content
    assert b'Transferencia' in response.content
    assert b'comprobante de pago' in response.content
    assert b'Mercado Pago' in response.content
    assert b'No disponible por el momento' not in response.content
    assert b'tarjeta en cuotas' in response.content


@override_settings(MP_ACCESS_TOKEN='')
def test_metodo_pago_sin_token_deshabilita_mercado_pago(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/metodo-pago/')
    assert response.status_code == 200
    assert b'Mercado Pago' in response.content
    assert b'disabled' in response.content
    assert b'No disponible por el momento' in response.content


def test_pago_local_muestra_datos(client_logueado, usuario, datos_checkout):
    from ventas.services import crear_venta_confirmada_service
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    response = client_logueado.get(f'/ventas/pago-local/{venta.id}/')
    assert response.status_code == 200
    assert b'efectivo' in response.content
    assert b'ventas-resumen-mapa-wrap' in response.content
    assert b'ventas-btn-wsp' in response.content
    assert b'Coordinar horarios' in response.content
    content = response.content.decode()
    assert 'Detalle del pedido' in content
    assert '$13.500,00 con transferencia' in content
    assert '$15.000,00' not in content


def test_pago_local_retiro_no_muestra_mercado_pago(client_logueado, usuario, datos_checkout):
    from ventas.services import crear_venta_confirmada_service
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    response = client_logueado.get(f'/ventas/pago-local/{venta.id}/')
    assert response.status_code == 200
    assert b'Mercado Pago' not in response.content


def _crear_venta_mp_pendiente(usuario, datos_checkout):
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
    return venta


def _webhook_payload(payment_id='12001'):
    return {'type': 'payment', 'data': {'id': payment_id}}


def _pago_data_mp(status, venta_id, amount, payment_id='12001'):
    return {
        'id': payment_id,
        'status': status,
        'status_detail': 'accredited' if status == 'approved' else status,
        'external_reference': str(venta_id),
        'transaction_amount': amount,
        'preference_id': '3776797576-1',
        'collector_id': 3776797576,
    }


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_COMERCIO='comercio@test.com',
)
@pytest.mark.django_db
def test_webhook_pago_aprobado_confirma_venta_y_envia_facturas(client, usuario, item, datos_checkout, monkeypatch):
    from django.conf import settings

    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    pago = venta.pagos.get()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO
    assert pago.payment_id == '12001'

    asuntos = [m.subject for m in mail.outbox]
    destinatarios = [m.to for m in mail.outbox]
    assert len(mail.outbox) == 2
    assert f'Tu pedido #{venta.id} | Practicasa' in asuntos
    assert f'Nuevo pedido #{venta.id} | Practicasa' in asuntos
    assert [venta.email] in destinatarios
    assert [settings.EMAIL_COMERCIO] in destinatarios


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_idempotente_no_duplica_emails_ni_pagos(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    body = json.dumps(_webhook_payload())
    assert client.post(
        '/ventas/mp-webhook/', data=body, content_type='application/json'
    ).status_code == 200
    assert client.post(
        '/ventas/mp-webhook/', data=body, content_type='application/json'
    ).status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    assert venta.pagos.count() == 1
    assert len(mail.outbox) == 2


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_firma_invalida_loguea_motivo(client, usuario, item, datos_checkout, monkeypatch, caplog):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: False)

    with caplog.at_level('WARNING', logger='ventas.mp'):
        response = client.post(
            '/ventas/mp-webhook/',
            data=json.dumps(_webhook_payload()),
            content_type='application/json',
        )

    assert response.status_code == 200
    assert 'firma inválida' in caplog.text
    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_firma_invalida_no_confirma_venta(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: False)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    pago = venta.pagos.get()
    assert pago.estado == PagoModel.EstadoChoices.PENDIENTE
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_monto_distinto_no_confirma_venta(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total) + 100),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_rechazado_no_confirma_venta(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('rejected', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    pago = venta.pagos.get()
    assert pago.estado == PagoModel.EstadoChoices.RECHAZADO
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_charged_back_marca_reembolsado_y_cancela_venta(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    pago = venta.pagos.get()
    pago.estado = PagoModel.EstadoChoices.APROBADO
    pago.payment_id = '12001'
    pago.save()

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('charged_back', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO
    assert len(mail.outbox) == 1
    assert f'Se revirtió el pago del pedido #{venta.id}' in mail.outbox[0].subject
    assert 'Si ya entregaste' in mail.outbox[0].body


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_refunded_marca_reembolsado_y_cancela_venta(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    pago = venta.pagos.get()
    pago.estado = PagoModel.EstadoChoices.APROBADO
    pago.payment_id = '12001'
    pago.save()

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('refunded', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO
    assert len(mail.outbox) == 1


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_in_mediation_solo_avisa_y_no_cambia_estados(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    pago = venta.pagos.get()
    pago.estado = PagoModel.EstadoChoices.APROBADO
    pago.payment_id = '12001'
    pago.save()

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('in_mediation', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    assert pago.estado == PagoModel.EstadoChoices.APROBADO
    assert len(mail.outbox) == 1


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_aprobado_reactiva_venta_cancelada(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    assert item.producto.stock == 10

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    item.producto.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    assert venta.pagos.get().estado == PagoModel.EstadoChoices.APROBADO
    assert item.producto.stock == 8
    assert len(mail.outbox) == 2


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_aprobado_sin_stock_no_reactiva_y_avisa(
    client, usuario, item, datos_checkout, monkeypatch, caplog
):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CANCELADA
    venta.save(update_fields=['estado'])
    item.producto.stock = 1
    item.producto.save(update_fields=['stock'])

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    item.producto.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert venta.pagos.get().estado == PagoModel.EstadoChoices.APROBADO
    assert item.producto.stock == 1
    assert len(mail.outbox) == 1
    assert 'sin stock' in caplog.text


@pytest.mark.parametrize(
    'status_mp, estado_pago, estado_venta, emails',
    [
        ('pending', PagoModel.EstadoChoices.PENDIENTE, VentaModel.EstadoChoices.PENDIENTE, 0),
        ('in_process', PagoModel.EstadoChoices.PENDIENTE, VentaModel.EstadoChoices.PENDIENTE, 0),
        ('authorized', PagoModel.EstadoChoices.PENDIENTE, VentaModel.EstadoChoices.PENDIENTE, 0),
        ('cancelled', PagoModel.EstadoChoices.CANCELADO, VentaModel.EstadoChoices.PENDIENTE, 0),
    ],
)
@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_matriz_estados_mp(
    client,
    usuario,
    item,
    datos_checkout,
    monkeypatch,
    status_mp,
    estado_pago,
    estado_venta,
    emails,
):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp(status_mp, venta.id, float(venta.total)),
    )
    monkeypatch.setattr(mp, 'verificar_firma_webhook', lambda request, data_id: True)

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps(_webhook_payload()), content_type='application/json'
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == estado_venta
    assert venta.pagos.get().estado == estado_pago
    assert len(mail.outbox) == emails


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_webhook_sin_data_id_responde_ok(client, usuario, item, datos_checkout, monkeypatch):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())

    response = client.post(
        '/ventas/mp-webhook/', data=json.dumps({'type': 'payment'}), content_type='application/json'
    )
    assert response.status_code == 200
    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_WEBHOOK_SECRET='SECRET-W',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_procesa_data_id_en_query_con_firma_real(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )

    request_id = 'req-real'
    ts = str(int(time.time()))
    cadena = f'id:12001;request-id:{request_id};ts:{ts};'
    firma = hmac.new(b'SECRET-W', cadena.encode(), hashlib.sha256).hexdigest()

    response = client.post(
        '/ventas/mp-webhook/?data.id=12001&type=payment',
        data=json.dumps(_webhook_payload()),
        content_type='application/json',
        headers={
            'X-Signature': f'ts={ts},v1={firma}',
            'x-request-id': request_id,
        },
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    pago = venta.pagos.get()
    assert pago.estado == PagoModel.EstadoChoices.APROBADO
    assert pago.payment_id == '12001'
    assert len(mail.outbox) == 2


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_WEBHOOK_SECRET='SECRET-W',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_ignora_formato_legacy_id_topic(client, usuario, item, datos_checkout, monkeypatch):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: _pago_data_mp('approved', venta.id, float(venta.total)),
    )

    request_id = 'req-legacy'
    ts = str(int(time.time()))
    cadena = f'id:12001;request-id:{request_id};ts:{ts};'
    firma = hmac.new(b'SECRET-W', cadena.encode(), hashlib.sha256).hexdigest()

    response = client.post(
        '/ventas/mp-webhook/?id=12001&topic=payment',
        data='',
        content_type='application/json',
        headers={
            'X-Signature': f'ts={ts},v1={firma}',
            'x-request-id': request_id,
        },
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert venta.pagos.get().payment_id is None
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_WEBHOOK_SECRET='SECRET-W',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_pago_de_otra_cuenta_no_confirma(
    client, usuario, item, datos_checkout, monkeypatch, caplog
):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.pagos.update(mp_preference_id='777-pref-legacy')

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'consultar_pago_service',
        lambda sdk, pid: {
            **_pago_data_mp('approved', venta.id, float(venta.total)),
            'collector_id': 999,
        },
    )

    request_id = 'req-otra-cuenta'
    ts = str(int(time.time()))
    cadena = f'id:12001;request-id:{request_id};ts:{ts};'
    firma = hmac.new(b'SECRET-W', cadena.encode(), hashlib.sha256).hexdigest()

    with caplog.at_level('WARNING', logger='ventas.mp'):
        response = client.post(
            '/ventas/mp-webhook/?data.id=12001&type=payment',
            data=json.dumps(_webhook_payload()),
            content_type='application/json',
            headers={
                'X-Signature': f'ts={ts},v1={firma}',
                'x-request-id': request_id,
            },
        )
    assert response.status_code == 200
    assert 'no pertenece a la cuenta' in caplog.text

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert len(mail.outbox) == 0


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_WEBHOOK_SECRET='SECRET-W',
    PEDIDO_TTL_HORAS=4,
)
@pytest.mark.django_db
def test_webhook_error_transitorio_responde_503(
    client, usuario, item, datos_checkout, monkeypatch
):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())

    def _consulta_que_falla(sdk, pid):
        raise mp.MercadoPagoErrorTransitorio('timeout')

    monkeypatch.setattr(mp, 'consultar_pago_service', _consulta_que_falla)

    request_id = 'req-503'
    ts = str(int(time.time()))
    cadena = f'id:12001;request-id:{request_id};ts:{ts};'
    firma = hmac.new(b'SECRET-W', cadena.encode(), hashlib.sha256).hexdigest()

    response = client.post(
        '/ventas/mp-webhook/?data.id=12001&type=payment',
        data=json.dumps(_webhook_payload()),
        content_type='application/json',
        headers={
            'X-Signature': f'ts={ts},v1={firma}',
            'x-request-id': request_id,
        },
    )
    assert response.status_code == 503

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_WEBHOOK_SECRET='SECRET-W',
    PEDIDO_TTL_HORAS=4,
)
@pytest.mark.django_db
def test_webhook_pago_inexistente_responde_200(
    client, usuario, item, datos_checkout, monkeypatch
):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)

    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: None)

    request_id = 'req-404'
    ts = str(int(time.time()))
    cadena = f'id:12001;request-id:{request_id};ts:{ts};'
    firma = hmac.new(b'SECRET-W', cadena.encode(), hashlib.sha256).hexdigest()

    response = client.post(
        '/ventas/mp-webhook/?data.id=12001&type=payment',
        data=json.dumps(_webhook_payload()),
        content_type='application/json',
        headers={
            'X-Signature': f'ts={ts},v1={firma}',
            'x-request-id': request_id,
        },
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4)
@pytest.mark.django_db
def test_webhook_ignora_merchant_order(client, usuario, item, datos_checkout, monkeypatch):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())

    response = client.post(
        '/ventas/mp-webhook/?id=45496050527&topic=merchant_order',
        data='',
        content_type='application/json',
    )
    assert response.status_code == 200

    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    assert venta.pagos.count() == 1


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_usuario_ajeno_redirige_a_carrito(client_logueado, usuario, item, datos_checkout):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    otro = UsuarioModel.objects.create_user(
        email='otro@example.com', nombre_completo='Otro Usuario', password='Pass1234'
    )
    client_logueado.force_login(otro)
    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 302
    assert response.url == reverse('ver_carrito')


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_pendiente_muestra_volver_a_pagar(client_logueado, usuario, item, datos_checkout):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'Complet' in response.content
    assert b'Volver a pagar' in response.content
    content = response.content.decode()
    assert 'Detalle del pedido' in content
    assert 'ventas-resumen' in content
    assert '$15.000,00' in content
    assert 'con transferencia' not in content
    assert 'Pendiente' in content
    assert 'text-bg-warning' in content


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_actualiza_reintentos_restantes(client_logueado, usuario, item, datos_checkout, monkeypatch):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-2', monto=venta.total, external_reference=str(venta.id),
    )
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: None)

    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'<strong>3</strong> reintentos' in response.content


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_aprobado_muestra_acreditado(client_logueado, usuario, item, datos_checkout):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    pago = venta.pagos.get()
    pago.estado = PagoModel.EstadoChoices.APROBADO
    pago.payment_id = '12001'
    pago.save()

    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'acreditado' in response.content


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    MP_MAX_REINTENTOS=5,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_pago_view_sincroniza_pago_aprobado_desde_url(
    client_logueado, usuario, item, datos_checkout, monkeypatch
):
    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    pago_data = _pago_data_mp('approved', venta.id, float(venta.total), payment_id='12001')
    pago_data.update({
        'installments': 6,
        'payment_method_id': 'master',
        'card': {'last_four_digits': '4602'},
        'transaction_details': {
            'installment_amount': 100.0,
            'total_paid_amount': 600.0,
        },
    })
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: pago_data)

    response = client_logueado.get(f'/ventas/pago/{venta.id}/?payment_id=12001')

    assert response.status_code == 200
    assert b'acreditado' in response.content
    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CONFIRMADA
    pago = venta.pagos.get(payment_id='12001')
    assert pago.estado == PagoModel.EstadoChoices.APROBADO
    assert pago.cuotas == 6
    assert pago.monto_cuota == 100
    assert pago.total_pagado == 600
    assert pago.tarjeta_ultimos_digitos == '4602'
    assert '**** 4602' in response.content.decode()
    factura = next(m for m in mail.outbox if 'Tu pedido' in m.subject)
    assert 'Master terminada en 4602' in factura.alternatives[0][0]


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    MP_MAX_REINTENTOS=5,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_pago_view_no_reactiva_pago_reembolsado_desde_url(
    client_logueado, usuario, item, datos_checkout, monkeypatch
):
    from ventas.services import actualizar_estado_pago_service

    mail.outbox.clear()
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save()
    pago = venta.pagos.get()
    pago.estado = PagoModel.EstadoChoices.APROBADO
    pago.payment_id = '12001'
    pago.save()

    actualizar_estado_pago_service(pago, PagoModel.EstadoChoices.REEMBOLSADO)
    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO

    pago_data = _pago_data_mp('approved', venta.id, float(venta.total), payment_id='12001')
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: pago_data)

    response = client_logueado.get(
        f'/ventas/pago/{venta.id}/?collection_id=12001&payment_id=12001&status=approved'
    )

    assert response.status_code == 200
    venta.refresh_from_db()
    pago.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.CANCELADA
    assert pago.estado == PagoModel.EstadoChoices.REEMBOLSADO
    assert len(mail.outbox) == 0
    contenido = response.content.decode()
    assert 'Pago reembolsado' in contenido
    assert 'Reembolsado' in contenido
    assert 'El pago venció' not in contenido


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=2)
@pytest.mark.django_db
def test_pago_view_reintentos_agotados_no_muestra_boton(client_logueado, usuario, item, datos_checkout, monkeypatch):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-2', monto=venta.total, external_reference=str(venta.id),
    )
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: None)

    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'Contactanos' in response.content
    assert b'Volver a pagar' not in response.content


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    MP_MAX_REINTENTOS=2,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_pago_view_post_sin_reintentos_no_redirige(client_logueado, usuario, item, datos_checkout, monkeypatch):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    PagoModel.objects.create(
        venta=venta, estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id='pref-2', monto=venta.total, external_reference=str(venta.id),
    )
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(mp, 'consultar_pago_service', lambda sdk, pid: None)
    monkeypatch.setattr(
        mp, 'crear_preferencia_service',
        lambda *a, **k: {'id': 'x', 'init_point': 'https://pay.mp/x'},
    )

    response = client_logueado.post(f'/ventas/pago/{venta.id}/', {})
    assert response.status_code == 200
    assert venta.pagos.count() == 2


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_confirmacion_mercado_pago_sin_token_no_crea_venta(client_logueado, usuario, item, datos_checkout, monkeypatch):
    monkeypatch.setattr(mp, 'crear_preferencia_service', lambda *a, **k: {'id': 'x', 'init_point': 'x'})
    with override_settings(MP_ACCESS_TOKEN=''):
        client_logueado.post('/ventas/checkout/', datos_checkout)
        client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
        client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
        response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 200
    assert b'disponible' in response.content
    assert VentaModel.objects.count() == 0


@override_settings(RATELIMIT_ENABLE=True)
@pytest.mark.django_db
def test_checkout_rate_limit_ajax_devuelve_429(client_logueado, item, datos_checkout):
    cache.clear()
    try:
        for _ in range(5):
            response = client_logueado.post(
                '/ventas/checkout/',
                datos_checkout,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
            assert response.status_code == 200
        response = client_logueado.post(
            '/ventas/checkout/',
            datos_checkout,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
    finally:
        cache.clear()

    assert response.status_code == 429
    data = response.json()
    assert data['success'] is False
    assert data['errors']['__all__'] == [
        'Demasiados intentos. Esperá un minuto antes de volver a intentar.'
    ]


@override_settings(RATELIMIT_ENABLE=True)
@pytest.mark.django_db
def test_checkout_rate_limit_html_devuelve_429(client_logueado, item, datos_checkout):
    cache.clear()
    try:
        for _ in range(5):
            response = client_logueado.post('/ventas/checkout/', datos_checkout)
            assert response.status_code == 302
        response = client_logueado.post('/ventas/checkout/', datos_checkout)
    finally:
        cache.clear()

    assert response.status_code == 429
    assert b'Demasiados intentos' in response.content


@override_settings(MP_ACCESS_TOKEN='TEST-123', PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_post_no_repaga_tras_reembolso(
    client_logueado, usuario, item, datos_checkout, monkeypatch
):
    from ventas import views
    from ventas.services import actualizar_estado_pago_service

    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    pago = venta.pagos.get()
    actualizar_estado_pago_service(pago, PagoModel.EstadoChoices.REEMBOLSADO)
    venta.refresh_from_db()
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE

    llamadas = []
    monkeypatch.setattr(
        views,
        'crear_pago_mercado_pago_service',
        lambda *a, **k: llamadas.append(True) or 'https://pay.mp/x',
    )

    response = client_logueado.post(f'/ventas/pago/{venta.id}/')

    assert response.status_code == 200
    assert llamadas == []
    assert venta.pagos.count() == 1
