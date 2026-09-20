import hashlib
import hmac
from datetime import timedelta
from decimal import Decimal

import mercadopago

from .models import VentaModel


class MercadoPagoError(Exception):
    pass


class MercadoPagoNoConfigurado(Exception):
    pass


def get_sdk():
    from django.conf import settings

    if not settings.MP_ACCESS_TOKEN:
        raise MercadoPagoNoConfigurado('El pago con Mercado Pago no está disponible por el momento.')
    return mercadopago.SDK(settings.MP_ACCESS_TOKEN)


def _precio_item(item):
    return item.subtotal_transferencia if item.venta.metodo_pago == VentaModel.MetodoPagoChoices.EFECTIVO else item.subtotal


def _items_preferencia(venta):
    items = []
    acumulado = Decimal('0')
    iteraciones = list(venta.items.select_related('producto'))
    total = venta.total
    for i, item in enumerate(iteraciones):
        precio = _precio_item(item)
        if i == len(iteraciones) - 1:
            precio = total - acumulado
        items.append({
            'id': str(item.producto_id),
            'title': item.nombre_producto,
            'quantity': 1,
            'unit_price': float(precio),
            'currency_id': 'ARS',
        })
        acumulado += precio
    return items


def crear_preferencia_service(sdk, venta, ttl_horas, webhook_url, back_url):
    from django.utils import timezone

    data = {
        'external_reference': str(venta.id),
        'items': _items_preferencia(venta),
        'currency_id': 'ARS',
        'statement_descriptor': 'PRACTICASA',
        'expires': True,
        'expiration_date_from': timezone.now().isoformat(),
        'expiration_date_to': (timezone.now() + timedelta(hours=ttl_horas)).isoformat(),
        'back_urls': {
            'success': back_url,
            'pending': back_url,
            'failure': back_url,
        },
        'auto_return': 'approved',
    }
    if webhook_url:
        data['notification_url'] = webhook_url
    res = sdk.preference().create(data)
    response = res.get('response') or {}
    if res.get('status', 400) >= 400:
        raise MercadoPagoError(response.get('message', 'No pudimos generar el pago.'))
    if 'init_point' not in response:
        raise MercadoPagoError('No pudimos generar el pago.')
    return response


def consultar_pago_service(sdk, payment_id):
    res = sdk.payment().get(payment_id)
    response = res.get('response')
    if res.get('status', 400) >= 400 or not response:
        return None
    return response


def _parsear_params_signature(valor):
    params = {}
    for parte in (valor or '').split(';'):
        if '=' in parte:
            clave, _, valor_parte = parte.partition('=')
            params[clave.strip()] = valor_parte.strip()
    return params


def verificar_firma_webhook(request, data_id):
    from django.conf import settings

    params = _parsear_params_signature(request.headers.get('X-Signature', ''))
    ts = params.get('ts')
    v1 = params.get('v1')
    request_id = request.headers.get('x-request-id', '')
    if not (ts and v1 and request_id):
        return False
    cadena = f'id:{data_id};request-id:{request_id};ts:{ts};'
    secreto = settings.MP_WEBHOOK_SECRET or settings.MP_ACCESS_TOKEN
    if not secreto:
        return False
    firma_esperada = hmac.new(
        secreto.encode(), cadena.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(firma_esperada, v1)