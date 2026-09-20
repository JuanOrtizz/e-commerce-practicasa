import json

import pytest

from django.core import mail
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


def test_checkout_get(client_logueado):
    response = client_logueado.get('/ventas/checkout/')
    assert response.status_code == 200
    assert b'Datos de facturaci' in response.content


def test_checkout_carrito_vacio_redirige(client, usuario):
    client.force_login(usuario)
    response = client.get('/ventas/checkout/')
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


def test_checkout_post_cp_invalido_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'codigo_postal': 'abc'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200
    assert b'4 d' in response.content


def test_checkout_post_direccion_invalida_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'direccion': 'x!!!'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200


def test_checkout_post_ciudad_invalida_muestra_error(client_logueado, datos_checkout):
    datos_checkout = {**datos_checkout, 'ciudad': 'Nogoy 123'}
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 200


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
    assert b'Retiro desde sucursal' in response.content


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


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4)
def test_metodo_pago_mercado_pago_redirige_a_confirmacion(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'envio_domicilio'})
    response = client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
    assert response.status_code == 302
    assert response.url == '/ventas/confirmacion/'
    assert VentaModel.objects.count() == 0


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_flujo_completo_efectivo_envia_factura(client_logueado, datos_checkout):
    from django.core import mail

    from ventas.services import EMAIL_COMERCIO

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
    assert [EMAIL_COMERCIO] in destinatarios

    html = mail.outbox[0].alternatives[0][0]
    assert f'#{venta.id}' in html
    assert 'Camiseta' in html
    assert 'Cliente Test' in html


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
def test_confirmacion_mercado_pago_redirige_a_mp_sin_email(client_logueado, datos_checkout, monkeypatch):
    mail.outbox.clear()
    monkeypatch.setattr(mp, 'get_sdk', lambda: object())
    monkeypatch.setattr(
        mp, 'crear_preferencia_service',
        lambda sdk, venta, ttl, webhook_url, back_url: {
            'id': 'pref-1', 'init_point': 'https://pay.mp/pref-1',
        },
    )

    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    client_logueado.post('/ventas/metodo-pago/', {'metodo_pago': 'mercado_pago'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 302
    assert response.url == 'https://pay.mp/pref-1'

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'mercado_pago'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE
    pago = PagoModel.objects.get(venta=venta)
    assert pago.estado == PagoModel.EstadoChoices.PENDIENTE
    assert pago.mp_preference_id == 'pref-1'
    assert pago.monto == venta.total
    assert len(mail.outbox) == 0


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


def test_metodo_pago_get_muestra_efectivo_y_mercado_pago_habilitado(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/metodo-pago/')
    assert response.status_code == 200
    assert b'Efectivo' in response.content
    assert b'Mercado Pago' in response.content
    assert b'No disponible por el momento' not in response.content
    assert b'online al instante' in response.content


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
        mp_preference_id='pref-1',
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
        'preference_id': 'pref-1',
    }


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_PEDIDO_TTL_HORAS=4,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
@pytest.mark.django_db
def test_webhook_pago_aprobado_confirma_venta_y_envia_facturas(client, usuario, item, datos_checkout, monkeypatch):
    from ventas.services import EMAIL_COMERCIO

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
    assert [EMAIL_COMERCIO] in destinatarios


@override_settings(
    MP_ACCESS_TOKEN='TEST-123',
    MP_PEDIDO_TTL_HORAS=4,
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
    MP_PEDIDO_TTL_HORAS=4,
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
    MP_PEDIDO_TTL_HORAS=4,
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
    MP_PEDIDO_TTL_HORAS=4,
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


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4)
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


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
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


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
@pytest.mark.django_db
def test_pago_view_pendiente_muestra_volver_a_pagar(client_logueado, usuario, item, datos_checkout):
    venta = _crear_venta_mp_pendiente(usuario, datos_checkout)
    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'Complet' in response.content
    assert b'Volver a pagar' in response.content


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=5)
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


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_PEDIDO_TTL_HORAS=4, MP_MAX_REINTENTOS=2)
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
    MP_PEDIDO_TTL_HORAS=4,
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
    MP_PEDIDO_TTL_HORAS=4,
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
