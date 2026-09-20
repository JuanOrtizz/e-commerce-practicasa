import hashlib
import hmac

from django.test import RequestFactory, override_settings

from ventas import mp


def _request_con_firma(data_id, secreto, request_id='req-1', ts='1700000000'):
    cadena = f'id:{data_id};request-id:{request_id};ts:{ts};'
    firma = hmac.new(secreto.encode(), cadena.encode(), hashlib.sha256).hexdigest()
    return RequestFactory().post(
        '/',
        headers={
            'X-Signature': f'ts={ts};v1={firma};',
            'x-request-id': request_id,
        },
    )


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='SECRET-W')
def test_verificar_firma_webhook_usa_mp_webhook_secret():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'SECRET-W'), '1001') is True
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1001') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='')
def test_verificar_firma_webhook_cae_al_access_token():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1001') is True
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'otra-clave'), '1001') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='')
def test_verificar_firma_webhook_data_id_distinto_marca_invalida():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1002') is False


def test_verificar_firma_webhook_faltan_parametros():
    request = RequestFactory().post('/')
    assert mp.verificar_firma_webhook(request, '1001') is False