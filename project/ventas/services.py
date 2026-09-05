from decimal import Decimal

from django.db import transaction
from django.template.loader import render_to_string

from project.services import enviar_email

from carrito.services import (
    get_o_crear_carrito_service,
    get_carrito_context_service,
    vaciar_carrito_service,
)
from .models import VentaModel, VentaItemModel

SESSION_DATOS_CLAVE = 'datos_venta'

CODIGOS_POSTALES_COORDINAR = {'3156', '3158', '3164', '3100'}

LOCALIDADES_POR_CP = {
    '3150': 'Nogoyá',
    '3156': 'Hernández',
    '3158': 'Lucas González',
    '3164': 'Ramírez',
    '3100': 'Paraná',
}

DATOS_LOCAL = {
    'nombre': 'Practicasa',
    'ciudad': 'Nogoyá',
    'direccion': '',
    'horario': '',
    'whatsapp': '+54 3435 46-8162',
    'mapa_url': 'https://www.google.com/maps?q=-32.399059,-59.783521&z=16&output=embed',
}

EMAIL_COMERCIO = 'practicasaok@gmail.com'


def get_datos_venta_session(request):
    return request.session.get(SESSION_DATOS_CLAVE, {})


def set_datos_venta_session(request, datos):
    request.session[SESSION_DATOS_CLAVE] = datos
    request.session.modified = True


def limpiar_datos_venta_session(request):
    request.session.pop(SESSION_DATOS_CLAVE, None)
    request.session.modified = True


def get_order_context_service(usuario):
    carrito = get_o_crear_carrito_service(usuario)
    return get_carrito_context_service(carrito)


def calcular_costo_envio_service(metodo_envio, subtotal):
    return Decimal('0')


def permite_coordinar_entrega_service(codigo_postal):
    if not codigo_postal:
        return False
    return codigo_postal.strip() in CODIGOS_POSTALES_COORDINAR


def localidad_para_coordinar_entrega_service(codigo_postal):
    if not codigo_postal:
        return None
    return LOCALIDADES_POR_CP.get(codigo_postal.strip())


def _validar_stock_service(carrito, carrito_context):
    for data in carrito_context['items']:
        item = data['item']
        if item.producto.stock < data['cantidad']:
            raise ValueError(f'Stock insuficiente para {item.producto.nombre}')


@transaction.atomic
def crear_venta_confirmada_service(usuario, datos, metodo_envio, metodo_pago):
    carrito = get_o_crear_carrito_service(usuario)
    carrito_context = get_carrito_context_service(carrito)

    if not carrito_context['items']:
        raise ValueError('Tu carrito está vacío')

    _validar_stock_service(carrito, carrito_context)

    subtotal = carrito_context['total']
    costo_envio = calcular_costo_envio_service(metodo_envio, subtotal)
    total = subtotal + costo_envio

    venta = VentaModel.objects.create(
        usuario=usuario,
        estado=VentaModel.EstadoChoices.PENDIENTE,
        metodo_envio=metodo_envio,
        metodo_pago=metodo_pago,
        nombre=datos.get('nombre'),
        email=datos.get('email'),
        telefono=datos.get('telefono'),
        direccion=datos.get('direccion') or None,
        numero=datos.get('numero') or None,
        ciudad=datos.get('ciudad') or None,
        provincia=datos.get('provincia') or None,
        codigo_postal=datos.get('codigo_postal') or None,
        notas=datos.get('notas') or None,
        subtotal=subtotal,
        costo_envio=costo_envio,
        total=total,
    )

    for data in carrito_context['items']:
        item = data['item']
        VentaItemModel.objects.create(
            venta=venta,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=data['precio_unitario'],
            precio_transferencia_unitario=data['precio_transferencia_unitario'],
            color_nombre=item.color_nombre,
            color_hex=item.color_hex,
            medida_nombre=item.medida_nombre,
        )
        item.producto.stock -= item.cantidad
        item.producto.save(update_fields=['stock'])

    vaciar_carrito_service(carrito)
    return venta


@transaction.atomic
def revertir_stock_venta_service(venta):
    for item in venta.items.select_related('producto'):
        item.producto.stock += item.cantidad
        item.producto.save(update_fields=['stock'])


def _render_factura_venta(venta, request, titulo):
    contexto = {
        'titulo': titulo,
        'venta': venta,
        'logo_url': request.build_absolute_uri('/static/img/logo_practicasa.png'),
    }
    return render_to_string('email/email_factura.html', contexto)


def enviar_factura_venta_service(venta, request):
    enviar_email(
        asunto=f'Tu pedido #{venta.id} | Practicasa',
        mensaje_texto=f'Tu pedido #{venta.id} fue registrado. Total: ${venta.total}.',
        mensaje_html=_render_factura_venta(venta, request, '¡Gracias por tu compra!'),
        destinatarios=[venta.email],
    )
    enviar_email(
        asunto=f'Nuevo pedido #{venta.id} | Practicasa',
        mensaje_texto=f'Nuevo pedido #{venta.id} de {venta.nombre} ({venta.email}).',
        mensaje_html=_render_factura_venta(venta, request, 'Nuevo pedido recibido'),
        destinatarios=[EMAIL_COMERCIO],
    )


def enviar_factura_venta_pagada_service(venta, request):
    enviar_email(
        asunto=f'Tu pago fue acreditado #{venta.id} | Practicasa',
        mensaje_texto=f'Tu pago del pedido #{venta.id} fue acreditado. Total: ${venta.total}.',
        mensaje_html=_render_factura_venta(venta, request, '¡Tu pago fue acreditado!'),
        destinatarios=[venta.email],
    )
    enviar_email(
        asunto=f'Pago recibido #{venta.id} | Practicasa',
        mensaje_texto=f'Pago del pedido #{venta.id} de {venta.nombre} ({venta.email}) acreditado.',
        mensaje_html=_render_factura_venta(venta, request, 'Pago recibido'),
        destinatarios=[EMAIL_COMERCIO],
    )
