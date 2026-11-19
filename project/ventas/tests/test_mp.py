import hashlib
import hmac
import time
from decimal import Decimal
from types import SimpleNamespace

import pytest
import requests
from django.test import RequestFactory, override_settings

from ventas import mp


def _request_con_firma(data_id, secreto, request_id='req-1', ts=None, separador=','):
    ts = ts or str(int(time.time()))
    cadena = f'id:{data_id};request-id:{request_id};ts:{ts};'
    firma = hmac.new(secreto.encode(), cadena.encode(), hashlib.sha256).hexdigest()
    return RequestFactory().post(
        '/',
        headers={
            'X-Signature': f'ts={ts}{separador}v1={firma}',
            'x-request-id': request_id,
        },
    )


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='SECRET-W')
def test_verificar_firma_webhook_usa_mp_webhook_secret():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'SECRET-W'), '1001') is True
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1001') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='')
def test_verificar_firma_webhook_sin_secret_es_invalida():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1001') is False
    assert mp.verificar_firma_webhook(_request_con_firma('1001', ''), '1001') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='TEST-123')
def test_verificar_firma_webhook_data_id_distinto_marca_invalida():
    assert mp.verificar_firma_webhook(_request_con_firma('1001', 'TEST-123'), '1002') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='TEST-123')
def test_verificar_firma_webhook_ts_viejo_marca_invalida():
    assert mp.verificar_firma_webhook(
        _request_con_firma('1001', 'TEST-123', ts='1600000000'), '1001'
    ) is False


def test_verificar_firma_webhook_faltan_parametros():
    request = RequestFactory().post('/')
    assert mp.verificar_firma_webhook(request, '1001') is False


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='SECRET-W')
def test_verificar_firma_webhook_acepta_header_con_punto_y_coma():
    assert mp.verificar_firma_webhook(
        _request_con_firma('1001', 'SECRET-W', separador=';'), '1001'
    ) is True


@override_settings(MP_ACCESS_TOKEN='TEST-123', MP_WEBHOOK_SECRET='SECRET-W')
def test_verificar_firma_webhook_acepta_ts_en_milisegundos():
    ts = str(int(time.time() * 1000))
    assert mp.verificar_firma_webhook(
        _request_con_firma('1001', 'SECRET-W', ts=ts), '1001'
    ) is True


class _PreferenciaFake:
    def __init__(self):
        self.payload = None

    def create(self, payload):
        self.payload = payload
        return {
            'status': 201,
            'response': {'id': 'pref-1', 'init_point': 'https://pay.mp/pref-1'},
        }


class _SdkFake:
    def __init__(self):
        self.preferencia = _PreferenciaFake()

    def preference(self):
        return self.preferencia


def _venta_fake():
    venta = SimpleNamespace(
        id=1, total=Decimal('3'), metodo_pago='mercado_pago', email='test@example.com'
    )
    item = SimpleNamespace(
        producto_id=1,
        nombre_producto='Producto',
        subtotal=Decimal('3'),
        subtotal_transferencia=Decimal('3'),
        venta=venta,
    )
    venta.items = SimpleNamespace(select_related=lambda *args, **kwargs: [item])
    return venta


def test_crear_preferencia_omite_auto_return_si_back_url_no_es_https():
    sdk = _SdkFake()
    mp.crear_preferencia_service(sdk, _venta_fake(), 4, '', 'http://localhost:8000/ventas/pago/1/')
    assert 'auto_return' not in sdk.preferencia.payload


def test_crear_preferencia_incluye_auto_return_si_back_url_es_https():
    sdk = _SdkFake()
    mp.crear_preferencia_service(sdk, _venta_fake(), 4, '', 'https://practicasa.com/ventas/pago/1/')
    assert sdk.preferencia.payload['auto_return'] == 'approved'


def test_crear_preferencia_solo_permite_tarjeta_de_credito():
    sdk = _SdkFake()
    mp.crear_preferencia_service(sdk, _venta_fake(), 4, '', 'https://practicasa.com/ventas/pago/1/')
    excluidos = {
        tipo['id']
        for tipo in sdk.preferencia.payload['payment_methods']['excluded_payment_types']
    }
    assert excluidos == {
        'ticket',
        'atm',
        'bank_transfer',
        'debit_card',
        'prepaid_card',
        'digital_currency',
        'crypto',
    }


def test_crear_preferencia_acepta_sandbox_init_point_sin_init_point():
    class _PreferenciaSandbox:
        def create(self, payload):
            return {
                'status': 201,
                'response': {'id': 'pref-1', 'sandbox_init_point': 'https://sandbox.mp/pay'},
            }

    sdk = SimpleNamespace(preference=lambda: _PreferenciaSandbox())
    respuesta = mp.crear_preferencia_service(sdk, _venta_fake(), 4, '', 'http://back')
    assert respuesta['sandbox_init_point'] == 'https://sandbox.mp/pay'


def test_crear_preferencia_falla_sin_urls_de_pago():
    class _PreferenciaSinUrl:
        def create(self, payload):
            return {'status': 201, 'response': {'id': 'pref-1'}}

    sdk = SimpleNamespace(preference=lambda: _PreferenciaSinUrl())
    with pytest.raises(mp.MercadoPagoError):
        mp.crear_preferencia_service(sdk, _venta_fake(), 4, '', 'http://back')


def _sdk_pago(get):
    return SimpleNamespace(payment=lambda: SimpleNamespace(get=get))


def test_consultar_pago_devuelve_none_si_no_existe():
    sdk = _sdk_pago(lambda pid: {'status': 404, 'response': None})
    assert mp.consultar_pago_service(sdk, '1') is None


def test_consultar_pago_lanza_transitorio_si_mp_devuelve_500():
    sdk = _sdk_pago(lambda pid: {'status': 500, 'response': None})
    with pytest.raises(mp.MercadoPagoErrorTransitorio):
        mp.consultar_pago_service(sdk, '1')


def test_consultar_pago_lanza_transitorio_si_falla_la_red():
    def _get(pid):
        raise requests.exceptions.ConnectionError('sin red')

    sdk = _sdk_pago(_get)
    with pytest.raises(mp.MercadoPagoErrorTransitorio):
        mp.consultar_pago_service(sdk, '1')


def test_consultar_pago_devuelve_datos_si_es_ok():
    sdk = _sdk_pago(lambda pid: {'status': 200, 'response': {'id': pid, 'status': 'approved'}})
    assert mp.consultar_pago_service(sdk, '1') == {'id': '1', 'status': 'approved'}