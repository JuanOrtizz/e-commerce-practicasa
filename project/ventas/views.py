import json
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from carrito.services import get_o_crear_carrito_service, vaciar_carrito_service
from .forms import CheckoutForm, EnvioForm, MetodoPagoForm
from . import mp
from .models import PagoModel, VentaModel
from .services import (
    crear_pago_mercado_pago_service,
    crear_venta_confirmada_service,
    eliminar_venta_service,
    enviar_factura_venta_service,
    expirar_pagos_vencidos_service,
    get_datos_venta_session,
    get_order_context_service,
    get_venta_context_service,
    limpiar_datos_venta_session,
    localidad_para_coordinar_entrega_service,
    permite_coordinar_entrega_service,
    permite_envio_domicilio_service,
    procesar_notificacion_pago_service,
    set_datos_venta_session,
    sincronizar_estado_pago_service,
    whatsapp_link_service,
)

logger = logging.getLogger('ventas.mp')

MENSAJE_RATE_LIMIT = 'Demasiados intentos. Esperá un minuto antes de volver a intentar.'

def _respuesta_sin_carrito(request, mensaje):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'redirect': reverse('ver_carrito'),
            'message': mensaje,
        })
    return redirect('ver_carrito')

@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def checkout(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return _respuesta_sin_carrito(request, 'Tu carrito está vacío.')
    if order_context['hay_sin_stock']:
        return _respuesta_sin_carrito(
            request,
            'Uno o más productos se quedaron sin stock. Revisá tu carrito para continuar.',
        )

    if request.method == 'POST' and getattr(request, 'limited', False):
        form = CheckoutForm(request.POST)
        form.add_error(None, MENSAJE_RATE_LIMIT)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'errors': {'__all__': [MENSAJE_RATE_LIMIT]}},
                status=429,
            )
        return render(request, 'ventas/checkout.html', {
            'form': form,
            'order_context': order_context,
        }, status=429)

    datos = get_datos_venta_session(request)
    form = CheckoutForm(initial={
        'nombre': datos.get('nombre', request.user.nombre_completo),
        'email': datos.get('email', request.user.email),
        'telefono': datos.get('telefono', ''),
        'direccion': datos.get('direccion', ''),
        'numero': datos.get('numero', ''),
        'ciudad': datos.get('ciudad', ''),
        'provincia': datos.get('provincia', ''),
        'codigo_postal': datos.get('codigo_postal', ''),
        'notas': datos.get('notas', ''),
    })

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            set_datos_venta_session(request, form.cleaned_data)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "redirect": reverse('envio')})
            return redirect('envio')
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors})
        for field_name in form.errors:
            widget = form.fields[field_name].widget
            widget.attrs['class'] = (widget.attrs.get('class', '') + ' is-invalid').strip()

    return render(request, 'ventas/checkout.html', {
        'form': form,
        'order_context': order_context,
    })


@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def envio(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

    datos = get_datos_venta_session(request)
    if not datos:
        return redirect('checkout')

    form = EnvioForm(initial={
        'metodo_envio': datos.get('metodo_envio'),
    })

    if request.method == 'POST':
        form = EnvioForm(request.POST)
        if form.is_valid():
            datos.update({'metodo_envio': form.cleaned_data['metodo_envio']})
            set_datos_venta_session(request, datos)
            return redirect('metodo_pago')

    return render(request, 'ventas/envio.html', {
        'form': form,
        'order_context': order_context,
        'datos': datos,
        'permite_coordinar_entrega': permite_coordinar_entrega_service(datos.get('codigo_postal')),
        'permite_envio_domicilio': permite_envio_domicilio_service(datos.get('codigo_postal')),
        'localidad_coordinar_entrega': localidad_para_coordinar_entrega_service(datos.get('codigo_postal')),
    })


@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def metodo_pago(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

    datos = get_datos_venta_session(request)
    if not datos or 'metodo_envio' not in datos:
        return redirect('envio')

    form = MetodoPagoForm(initial={
        'metodo_pago': datos.get('metodo_pago', VentaModel.MetodoPagoChoices.EFECTIVO),
    })

    if request.method == 'POST':
        form = MetodoPagoForm(request.POST)
        if form.is_valid():
            datos.update({'metodo_pago': form.cleaned_data['metodo_pago']})
            set_datos_venta_session(request, datos)
            return redirect('confirmacion')

    return render(request, 'ventas/metodo_pago.html', {
        'form': form,
        'order_context': order_context,
        'datos': datos,
        'mp_disponible': bool(settings.MP_ACCESS_TOKEN),
        'localidad_coordinar_entrega': localidad_para_coordinar_entrega_service(datos.get('codigo_postal')),
    })


@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def confirmacion(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

    datos = get_datos_venta_session(request)
    if not datos or 'metodo_envio' not in datos:
        return redirect('checkout')
    if 'metodo_pago' not in datos:
        return redirect('metodo_pago')

    context = {
        'order_context': order_context,
        'datos': datos,
        'modo_precio': (
            'normal'
            if datos.get('metodo_pago') == VentaModel.MetodoPagoChoices.MERCADO_PAGO
            else 'transferencia'
        ),
        'localidad_coordinar_entrega': localidad_para_coordinar_entrega_service(datos.get('codigo_postal')),
    }

    if request.method == 'POST':
        try:
            venta = crear_venta_confirmada_service(
                request.user, datos, datos['metodo_envio'], datos['metodo_pago'],
                vaciar_carrito=datos['metodo_pago'] != VentaModel.MetodoPagoChoices.MERCADO_PAGO,
            )
            limpiar_datos_venta_session(request)
        except ValueError as e:
            context['error'] = str(e)
            return render(request, 'ventas/confirmacion.html', context)

        if venta.metodo_pago == VentaModel.MetodoPagoChoices.MERCADO_PAGO:
            try:
                init_point = crear_pago_mercado_pago_service(venta, request)
            except mp.MercadoPagoError as e:
                logger.warning('Mercado Pago rechazó la preferencia (venta %s): %s', venta.id, e)
                eliminar_venta_service(venta)
                context['error'] = f'No pudimos iniciar el pago: {e}'
                return render(request, 'ventas/confirmacion.html', context)
            except mp.MercadoPagoNoConfigurado as e:
                eliminar_venta_service(venta)
                context['error'] = str(e)
                return render(request, 'ventas/confirmacion.html', context)
            except Exception:
                logger.exception('Error inesperado al iniciar el pago con Mercado Pago (venta %s)', venta.id)
                eliminar_venta_service(venta)
                context['error'] = 'No pudimos iniciar el pago. Intentalo de nuevo.'
                return render(request, 'ventas/confirmacion.html', context)
            vaciar_carrito_service(get_o_crear_carrito_service(request.user))
            return redirect(init_point)

        enviar_factura_venta_service(venta, request)
        return redirect('pago_local', venta_id=venta.id)

    return render(request, 'ventas/confirmacion.html', context)


@login_required
def pago_local(request, venta_id):
    venta = VentaModel.objects.filter(id=venta_id, usuario=request.user).first()
    if not venta:
        return redirect('ver_carrito')
    if venta.metodo_pago == VentaModel.MetodoPagoChoices.MERCADO_PAGO:
        return redirect('pago', venta_id=venta.id)
    return render(request, 'ventas/pago_local.html', {
        'venta': venta,
        'resumen_venta': get_venta_context_service(venta),
        'modo_precio': 'transferencia',
        'datos_local': settings.DATOS_LOCAL,
        'datos_bancarios': settings.DATOS_BANCARIOS,
        'whatsapp_link': whatsapp_link_service(),
    })


@login_required
def pago(request, venta_id):
    expirar_pagos_vencidos_service()
    venta = VentaModel.objects.filter(id=venta_id, usuario=request.user).first()
    if not venta:
        return redirect('ver_carrito')
    if venta.metodo_pago != VentaModel.MetodoPagoChoices.MERCADO_PAGO:
        return redirect('pago_local', venta_id=venta.id)

    sincronizar_estado_pago_service(
        venta,
        request,
        request.GET.get('payment_id') or request.GET.get('collection_id'),
    )
    venta.refresh_from_db()

    pagos = venta.pagos.all()
    pago_aprobado = venta.pagos.filter(estado=PagoModel.EstadoChoices.APROBADO).exists()
    pago_reembolsado = venta.pagos.filter(
        estado=PagoModel.EstadoChoices.REEMBOLSADO
    ).exists()
    reintentos = venta.pagos.count()
    max_reintentos = settings.MP_MAX_REINTENTOS
    reintentos_restantes = max(max_reintentos - reintentos, 0)
    puede_pagar = (
        venta.estado == VentaModel.EstadoChoices.PENDIENTE
        and not pago_aprobado
        and not pago_reembolsado
        and reintentos < max_reintentos
    )

    error = None
    if request.method == 'POST' and puede_pagar:
        try:
            init_point = crear_pago_mercado_pago_service(venta, request)
            return redirect(init_point)
        except mp.MercadoPagoError as e:
            error = f'No pudimos iniciar el pago: {e}'
        except mp.MercadoPagoNoConfigurado as e:
            error = str(e)
        except Exception:
            error = 'No pudimos iniciar el pago. Intentalo de nuevo.'

    return render(request, 'ventas/pago.html', {
        'venta': venta,
        'resumen_venta': get_venta_context_service(venta),
        'modo_precio': 'normal',
        'pagos': pagos,
        'pago_aprobado': pago_aprobado,
        'pago_reembolsado': pago_reembolsado,
        'reintentos': reintentos,
        'max_reintentos': settings.MP_MAX_REINTENTOS,
        'reintentos_restantes': reintentos_restantes,
        'puede_pagar': puede_pagar,
        'error': error,
        'volvio_de_mp': bool(
            request.GET.get('payment_id')
            or request.GET.get('collection_id')
            or request.GET.get('collection_status')
        ),
    })


@csrf_exempt
@require_POST
def mp_webhook(request):
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    data = payload.get('data') if isinstance(payload.get('data'), dict) else {}
    tipo = request.GET.get('type') or payload.get('type')
    data_id = (
        request.GET.get('data.id')
        or request.GET.get('data_id')
        or data.get('id')
        or payload.get('data_id')
    )
    if tipo and tipo != 'payment':
        data_id = None

    if not data_id:
        return HttpResponse('ok')

    try:
        procesado = procesar_notificacion_pago_service(str(data_id), request)
    except mp.MercadoPagoErrorTransitorio:
        logger.warning(
            'Mercado Pago no respondió al consultar el pago %s; se reintentará', data_id
        )
        return HttpResponse('retry', status=503)
    except Exception:
        logger.exception('Error procesando la notificación de pago %s', data_id)
        return HttpResponse('ok')

    if not procesado:
        logger.warning('Notificación de pago %s no procesada', data_id)
    return HttpResponse('ok')
