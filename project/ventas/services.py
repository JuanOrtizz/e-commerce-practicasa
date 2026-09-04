from decimal import Decimal

from django.db import transaction

from carrito.services import (
    get_o_crear_carrito_service,
    get_carrito_context_service,
    vaciar_carrito_service,
)
from .models import VentaModel, VentaItemModel

SESSION_DATOS_CLAVE = 'datos_venta'

DATOS_LOCAL = {
    'nombre': 'Practicasa',
    'ciudad': 'Nogoyá',
    'direccion': '',
    'horario': '',
    'whatsapp': '+54 3435 46-8162',
    'mapa_url': 'https://www.google.com/maps?q=-32.399059,-59.783521&z=16&output=embed',
}


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
    if metodo_envio == VentaModel.MetodoEnvioChoices.ENVIO_DOMICILIO:
        return Decimal('0')
    return Decimal('0')


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
