import logging
import re
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone
from project.services import enviar_email
from carrito.services import (
    get_o_crear_carrito_service,
    get_carrito_context_service,
    vaciar_carrito_service,
)
from productos.models import ProductoModel
from productos.services import actualizar_tags_stock_service
from . import mp
from .models import PagoModel, VentaModel, VentaItemModel

logger = logging.getLogger('ventas.mp')

SESSION_DATOS_CLAVE = 'datos_venta'
CODIGOS_POSTALES_COORDINAR = {'3156', '3158', '3164', '3100'}
CODIGOS_POSTALES_DOMICILIO = {'3150'}
LOCALIDADES_POR_CP = {
    '3150': 'Nogoyá',
    '3156': 'Hernández',
    '3158': 'Lucas González',
    '3164': 'Ramírez',
    '3100': 'Paraná',
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

def calcular_precios_venta_item_service(item):
    cantidad = item.cantidad
    cantidad_paga = item.cantidad_paga
    precio_unitario = item.precio_unitario
    precio_transferencia_unitario = item.precio_transferencia_unitario
    precio_original = item.precio_original_unitario or item.producto.precio
    precio_transferencia_original = (
        item.precio_transferencia_original_unitario
        or item.producto.precio_transferencia
    )
    subtotal = item.subtotal
    subtotal_transferencia = item.subtotal_transferencia
    ahorro = Decimal('0')
    ahorro_transferencia = Decimal('0')

    if item.promocion in ('2x1', '3x2'):
        ahorro = (precio_unitario * cantidad) - subtotal
        ahorro_transferencia = (
            precio_transferencia_unitario * cantidad
        ) - subtotal_transferencia

    return {
        'item': item,
        'producto': item.producto,
        'cantidad': cantidad,
        'cantidad_paga': cantidad_paga,
        'precio_unitario': precio_unitario,
        'precio_transferencia_unitario': precio_transferencia_unitario,
        'precio_original': precio_original,
        'precio_transferencia_original': precio_transferencia_original,
        'subtotal': subtotal,
        'subtotal_transferencia': subtotal_transferencia,
        'ahorro': ahorro,
        'ahorro_transferencia': ahorro_transferencia,
        'tiene_promocion_porcentaje': item.tiene_promocion_porcentaje,
        'promocion': item.promocion,
    }

def get_venta_context_service(venta):
    items_data = []
    total = Decimal('0')
    total_transferencia = Decimal('0')
    total_ahorro = Decimal('0')
    total_ahorro_transferencia = Decimal('0')

    for item in venta.items.select_related('producto').all():
        data = calcular_precios_venta_item_service(item)
        items_data.append(data)
        total += data['subtotal']
        total_transferencia += data['subtotal_transferencia']
        total_ahorro += data['ahorro']
        total_ahorro_transferencia += data['ahorro_transferencia']

    return {
        'items': items_data,
        'total': total,
        'total_transferencia': total_transferencia,
        'total_ahorro': total_ahorro,
        'total_ahorro_transferencia': total_ahorro_transferencia,
    }

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

def permite_envio_domicilio_service(codigo_postal):
    if not codigo_postal:
        return False
    return codigo_postal.strip() in CODIGOS_POSTALES_DOMICILIO

def whatsapp_link_service():
    numero = re.sub(r'\D', '', settings.DATOS_LOCAL['whatsapp'])
    return f'https://wa.me/{numero}'

def _validar_stock_service(carrito, carrito_context):
    sin_stock = [
        data['producto'].nombre
        for data in carrito_context['items']
        if data['sin_stock']
    ]
    if sin_stock:
        raise ValueError(
            'Estos productos ya no tienen stock: '
            + ', '.join(sin_stock)
            + '. Eliminalos del carrito para continuar.'
        )

def _validar_limite_pendientes_service(usuario):
    limite = timezone.now() - timedelta(hours=settings.PEDIDO_TTL_HORAS)
    pendientes = (
        VentaModel.objects.filter(
            usuario=usuario,
            estado=VentaModel.EstadoChoices.PENDIENTE,
            created_at__gte=limite,
        )
        .exclude(pagos__estado=PagoModel.EstadoChoices.APROBADO)
        .distinct()
        .count()
    )
    if pendientes >= settings.MAX_PEDIDOS_PENDIENTES:
        raise ValueError(
            f'Tenés {settings.MAX_PEDIDOS_PENDIENTES} pedidos pendientes. '
            'Completá alguno o esperá a que venza antes de crear otro.'
        )

def get_pedidos_pendientes_mp_service(usuario):
    limite = timezone.now() - timedelta(hours=settings.PEDIDO_TTL_HORAS)
    return (
        VentaModel.objects.filter(
            usuario=usuario,
            estado=VentaModel.EstadoChoices.PENDIENTE,
            metodo_pago=VentaModel.MetodoPagoChoices.MERCADO_PAGO,
            created_at__gte=limite,
        )
        .exclude(pagos__estado=PagoModel.EstadoChoices.APROBADO)
        .distinct()
        .order_by('-created_at')
    )

@transaction.atomic
def crear_venta_confirmada_service(usuario, datos, metodo_envio, metodo_pago, vaciar_carrito=True):
    if metodo_pago == VentaModel.MetodoPagoChoices.MERCADO_PAGO and not settings.MP_ACCESS_TOKEN:
        raise ValueError('El pago con Mercado Pago no está disponible por el momento.')

    carrito = get_o_crear_carrito_service(usuario)
    carrito_context = get_carrito_context_service(carrito)

    if not carrito_context['items']:
        raise ValueError('Tu carrito está vacío')

    _validar_stock_service(carrito, carrito_context)
    _validar_limite_pendientes_service(usuario)

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
            nombre_producto=data['producto'].nombre,
            promocion=data['promocion'],
            cantidad=item.cantidad,
            precio_unitario=data['precio_unitario'],
            precio_transferencia_unitario=data['precio_transferencia_unitario'],
            precio_original_unitario=data['precio_original'],
            precio_transferencia_original_unitario=data['precio_transferencia_original'],
            color_nombre=item.color_nombre,
            color_hex=item.color_hex,
            medida_nombre=item.medida_nombre,
        )

    _descontar_stock_venta_service(venta)
    if vaciar_carrito:
        vaciar_carrito_service(carrito)
    return venta


def _descontar_stock_venta_service(venta):
    producto_ids = []
    for item in venta.items.select_related('producto'):
        actualizados = ProductoModel.objects.filter(
            pk=item.producto_id, stock__gte=item.cantidad
        ).update(stock=F('stock') - item.cantidad)
        if not actualizados:
            raise ValueError(
                f'Otro cliente compró la última unidad de {item.producto.nombre}. '
                'Actualizá tu carrito.'
            )
        producto_ids.append(item.producto_id)
    actualizar_tags_stock_service(producto_ids)


@transaction.atomic
def revertir_stock_venta_service(venta):
    producto_ids = []
    for item in venta.items.select_related('producto'):
        ProductoModel.objects.filter(pk=item.producto_id).update(
            stock=F('stock') + item.cantidad
        )
        producto_ids.append(item.producto_id)
    actualizar_tags_stock_service(producto_ids)


def sincronizar_stock_venta_service(venta, anterior):
    cancelada = VentaModel.EstadoChoices.CANCELADA
    if anterior == cancelada and venta.estado != cancelada:
        _descontar_stock_venta_service(venta)
    elif anterior != cancelada and venta.estado == cancelada:
        revertir_stock_venta_service(venta)


def eliminar_venta_service(venta):
    if venta.estado != VentaModel.EstadoChoices.CANCELADA:
        revertir_stock_venta_service(venta)
    venta.delete()


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
        destinatarios=[settings.EMAIL_COMERCIO],
    )


@transaction.atomic
def crear_pago_mercado_pago_service(venta, request):
    from django.urls import reverse

    sdk = mp.get_sdk()
    back_url = request.build_absolute_uri(reverse('pago', args=[venta.id]))
    preferencia = mp.crear_preferencia_service(
        sdk, venta, settings.PEDIDO_TTL_HORAS, settings.MP_WEBHOOK_URL, back_url
    )
    PagoModel.objects.create(
        venta=venta,
        estado=PagoModel.EstadoChoices.PENDIENTE,
        mp_preference_id=preferencia['id'],
        monto=venta.total,
        external_reference=str(venta.id),
    )
    return preferencia['init_point']


def expirar_pagos_vencidos_service():
    limite = timezone.now() - timedelta(hours=settings.PEDIDO_TTL_HORAS)
    cancelada = VentaModel.EstadoChoices.CANCELADA
    pendiente = VentaModel.EstadoChoices.PENDIENTE
    vencidas = VentaModel.objects.filter(
        estado=pendiente,
        metodo_pago=VentaModel.MetodoPagoChoices.MERCADO_PAGO,
        created_at__lt=limite,
    ).exclude(
        pagos__estado=PagoModel.EstadoChoices.APROBADO
    ).distinct()
    procesados = False
    with transaction.atomic():
        for venta in vencidas:
            venta.pagos.filter(
                estado=PagoModel.EstadoChoices.PENDIENTE
            ).update(estado=PagoModel.EstadoChoices.VENCIDO)
            venta.estado = cancelada
            venta.save(update_fields=['estado'])
            procesados = True
    return procesados


def _reactivar_venta_service(venta):
    items = list(venta.items.select_related('producto'))
    producto_ids = [item.producto_id for item in items]
    bloqueados = {
        producto.id: producto
        for producto in ProductoModel.objects.select_for_update().filter(
            id__in=producto_ids
        )
    }
    sin_stock = [
        item.producto.nombre
        for item in items
        if bloqueados[item.producto_id].stock < item.cantidad
    ]
    if sin_stock:
        raise ValueError(
            'No hay stock suficiente para reactivar la venta: '
            + ', '.join(sin_stock)
        )
    venta.estado = VentaModel.EstadoChoices.CONFIRMADA
    venta.save(update_fields=['estado'])


def _sincronizar_venta_por_estado_pago_service(venta, nuevo_estado):
    if nuevo_estado == PagoModel.EstadoChoices.REEMBOLSADO:
        if (
            venta.estado == VentaModel.EstadoChoices.CONFIRMADA
            and not venta.pagos.filter(estado=PagoModel.EstadoChoices.APROBADO).exists()
        ):
            venta.estado = VentaModel.EstadoChoices.CANCELADA
            venta.save(update_fields=['estado'])
    elif nuevo_estado == PagoModel.EstadoChoices.APROBADO:
        if venta.estado == VentaModel.EstadoChoices.CANCELADA:
            _reactivar_venta_service(venta)
        elif venta.estado == VentaModel.EstadoChoices.PENDIENTE:
            venta.estado = VentaModel.EstadoChoices.CONFIRMADA
            venta.save(update_fields=['estado'])


@transaction.atomic
def actualizar_estado_pago_service(pago, nuevo_estado):
    pago.estado = nuevo_estado
    pago.save(update_fields=['estado'])

    venta = VentaModel.objects.select_for_update().get(pk=pago.venta_id)
    _sincronizar_venta_por_estado_pago_service(venta, nuevo_estado)
    return venta


def enviar_email_reembolso_service(venta, request):
    logo_url = request.build_absolute_uri('/static/img/logo_practicasa.png')

    def _html(para_comercio):
        return render_to_string('email/email_reembolso.html', {
            'titulo': 'Pago reembolsado',
            'venta': venta,
            'logo_url': logo_url,
            'para_comercio': para_comercio,
        })

    enviar_email(
        asunto=f'Tu pago fue reembolsado | Pedido #{venta.id} | Practicasa',
        mensaje_texto=(
            f'Te informamos que el pago del pedido #{venta.id} fue reembolsado. '
            f'Total: ${venta.total}. '
            'El plazo para verlo acreditado depende de tu medio de pago. '
            'Si tenés dudas, respondé este correo y te ayudamos.'
        ),
        mensaje_html=_html(False),
        destinatarios=[venta.email],
    )
    enviar_email(
        asunto=f'Pago reembolsado del pedido #{venta.id} | Practicasa',
        mensaje_texto=(
            f'El pago del pedido #{venta.id} de {venta.nombre} ({venta.email}) '
            f'fue marcado como reembolsado desde el panel. Total: ${venta.total}. '
            'Recordá que la venta quedó cancelada y el stock se repuso automáticamente.'
        ),
        mensaje_html=_html(True),
        destinatarios=[settings.EMAIL_COMERCIO],
    )


def _monto_coincide(monto_mp, esperado):
    try:
        monto_decimal = Decimal(str(monto_mp))
    except (TypeError, ValueError):
        return False
    return abs(monto_decimal - esperado) < Decimal('0.01')


def _venta_desde_referencia(pago_data):
    try:
        venta_id = int(pago_data.get('external_reference', ''))
    except (TypeError, ValueError):
        return None
    return VentaModel.objects.filter(id=venta_id).first()


def _alertar_reversion_pago(venta):
    mensaje_html = (
        f'<p>Se revirtió el pago del pedido <strong>#{venta.id}</strong> '
        f'de {venta.nombre} ({venta.email}). Total: ${venta.total}.</p>'
        '<p><strong>Si todavía no entregaste</strong>, cancelá la venta desde el panel '
        'y el stock se repone automáticamente.</p>'
        '<p><strong>Si ya entregaste</strong>, gestioná el reclamo con Mercado Pago.</p>'
    )
    enviar_email(
        asunto=f'Se revirtió el pago del pedido #{venta.id} | Practicasa',
        mensaje_texto=(
            f'Se revirtió el pago del pedido #{venta.id} de {venta.nombre} '
            f'({venta.email}). Total: ${venta.total}. '
            'Si todavía no entregaste, cancelá la venta desde el panel y el stock se repone solo. '
            'Si ya entregaste, gestioná el reclamo con Mercado Pago.'
        ),
        mensaje_html=mensaje_html,
        destinatarios=[settings.EMAIL_COMERCIO],
    )

CAMPOS_DATOS_MP = (
    'metodo_pago_mp',
    'cuotas',
    'monto_cuota',
    'total_pagado',
    'tarjeta_ultimos_digitos',
)

def _entero_o_none(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _decimal_o_none(valor):
    try:
        return Decimal(str(valor))
    except (TypeError, ValueError, ArithmeticError):
        return None


def _extraer_datos_mp(pago_data):
    tarjeta = pago_data.get('card') or {}
    detalles = pago_data.get('transaction_details') or {}
    metodo = pago_data.get('payment_method_id') or ''
    ultimos_digitos = tarjeta.get('last_four_digits') or ''
    return {
        'metodo_pago_mp': metodo[:50] or None,
        'cuotas': _entero_o_none(pago_data.get('installments')),
        'monto_cuota': _decimal_o_none(detalles.get('installment_amount')),
        'total_pagado': _decimal_o_none(detalles.get('total_paid_amount')),
        'tarjeta_ultimos_digitos': str(ultimos_digitos)[:4] or None,
    }


def _guardar_datos_mp(pago, pago_data):
    for campo, valor in _extraer_datos_mp(pago_data).items():
        setattr(pago, campo, valor)
    pago.save(update_fields=list(CAMPOS_DATOS_MP))


@transaction.atomic
def sincronizar_pago_service(pago_data, venta, request):
    venta = VentaModel.objects.select_for_update().filter(pk=venta.pk).first()
    if not venta:
        return None
    payment_id = str(pago_data.get('id'))
    estado_mp = pago_data.get('status', '')

    pago = PagoModel.objects.filter(payment_id=payment_id).first()
    if pago:
        if pago.venta_id != venta.id:
            return None
    else:
        pago = venta.pagos.filter(
            estado=PagoModel.EstadoChoices.PENDIENTE, payment_id__isnull=True
        ).order_by('-created_at').first()
        if pago:
            pago.payment_id = payment_id
            pago.save(update_fields=['payment_id'])
        else:
            pago = PagoModel.objects.create(
                venta=venta,
                estado=PagoModel.EstadoChoices.PENDIENTE,
                payment_id=payment_id,
                mp_preference_id=pago_data.get('preference_id', '') or '',
                monto=venta.total,
                external_reference=str(venta.id),
            )

    _guardar_datos_mp(pago, pago_data)

    aprobado = PagoModel.EstadoChoices.APROBADO
    confirmada = VentaModel.EstadoChoices.CONFIRMADA
    reembolsado = pago.estado == PagoModel.EstadoChoices.REEMBOLSADO
    ya_aprobado = pago.estado == aprobado
    hay_otro_aprobado = venta.pagos.filter(estado=aprobado).exclude(pk=pago.pk).exists()

    if estado_mp == 'approved' and not reembolsado:
        if not ya_aprobado and not hay_otro_aprobado:
            pago.estado = aprobado
            pago.save(update_fields=['estado', 'mp_preference_id', 'monto', 'external_reference'])
            estado_anterior = venta.estado
            try:
                _sincronizar_venta_por_estado_pago_service(venta, aprobado)
            except ValueError as e:
                logger.error(
                    'Venta %s con pago %s aprobado sin stock: %s', venta.id, payment_id, e
                )
                _alertar_reversion_pago(venta)
            else:
                if estado_anterior != confirmada and venta.estado == confirmada:
                    enviar_factura_venta_service(venta, request)
        elif not ya_aprobado:
            pago.estado = aprobado
            pago.save(update_fields=['estado', 'mp_preference_id', 'monto', 'external_reference'])
    elif estado_mp in ('rejected', 'cancelled'):
        nuevo = (
            PagoModel.EstadoChoices.RECHAZADO
            if estado_mp == 'rejected'
            else PagoModel.EstadoChoices.CANCELADO
        )
        if pago.estado != nuevo:
            pago.estado = nuevo
            pago.save(update_fields=['estado', 'mp_preference_id', 'monto', 'external_reference'])
    elif estado_mp in ('charged_back', 'refunded'):
        if pago.estado != PagoModel.EstadoChoices.REEMBOLSADO:
            pago.estado = PagoModel.EstadoChoices.REEMBOLSADO
            pago.save(update_fields=['estado', 'mp_preference_id', 'monto', 'external_reference'])
            _sincronizar_venta_por_estado_pago_service(
                venta, PagoModel.EstadoChoices.REEMBOLSADO
            )
            _alertar_reversion_pago(venta)
    elif estado_mp == 'in_mediation' and pago.estado == aprobado:
        _alertar_reversion_pago(venta)
    return pago


def _pago_pertenece_a_venta(pago_data, venta):
    collector_id = str(pago_data.get('collector_id') or '')
    if not collector_id:
        return False
    preferencias = venta.pagos.exclude(mp_preference_id='').values_list(
        'mp_preference_id', flat=True
    )
    return any(
        str(preferencia).startswith(f'{collector_id}-') for preferencia in preferencias
    )


def procesar_notificacion_pago_service(payment_id, request):
    try:
        sdk = mp.get_sdk()
    except mp.MercadoPagoNoConfigurado:
        logger.warning('Webhook %s ignorado: Mercado Pago no configurado', payment_id)
        return False

    if not mp.verificar_firma_webhook(request, payment_id):
        logger.warning('Webhook %s ignorado: firma inválida o vencida', payment_id)
        return False

    pago_data = mp.consultar_pago_service(sdk, payment_id)
    if not pago_data:
        logger.warning('Webhook %s ignorado: pago inexistente en Mercado Pago', payment_id)
        return False
    venta = _venta_desde_referencia(pago_data)
    if not venta:
        logger.warning('Webhook %s ignorado: venta inexistente', payment_id)
        return False
    if not _monto_coincide(pago_data.get('transaction_amount'), venta.total):
        logger.warning(
            'Webhook %s ignorado: monto no coincide con la venta #%s',
            payment_id,
            venta.id,
        )
        return False
    if not _pago_pertenece_a_venta(pago_data, venta):
        logger.warning(
            'Webhook %s ignorado: el pago no pertenece a la cuenta de la venta #%s',
            payment_id,
            venta.id,
        )
        return False
    sincronizar_pago_service(pago_data, venta, request)
    return True


def sincronizar_estado_pago_service(venta, request, payment_id=None):
    if venta.pagos.filter(estado=PagoModel.EstadoChoices.APROBADO).exists():
        return
    if payment_id:
        payment_id = str(payment_id)
        pago = venta.pagos.filter(payment_id=payment_id).first()
        if pago is None:
            pago = venta.pagos.filter(
                estado=PagoModel.EstadoChoices.PENDIENTE, payment_id__isnull=True
            ).order_by('-created_at').first()
    else:
        pago = venta.pagos.filter(
            estado=PagoModel.EstadoChoices.PENDIENTE
        ).order_by('-created_at').first()
        if not pago or not pago.payment_id:
            return
        payment_id = pago.payment_id
    if pago is None:
        return
    try:
        sdk = mp.get_sdk()
        pago_data = mp.consultar_pago_service(sdk, payment_id)
    except Exception:
        return
    if not pago_data:
        return
    if str(pago_data.get('external_reference', '')) != str(venta.id):
        return
    if not _monto_coincide(pago_data.get('transaction_amount'), venta.total):
        return
    sincronizar_pago_service(pago_data, venta, request)
