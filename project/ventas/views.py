from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from .forms import CheckoutForm, EnvioForm
from .models import VentaModel
from .services import (
    DATOS_LOCAL,
    crear_venta_confirmada_service,
    enviar_factura_venta_service,
    get_datos_venta_session,
    get_order_context_service,
    limpiar_datos_venta_session,
    localidad_para_coordinar_entrega_service,
    permite_coordinar_entrega_service,
    permite_envio_domicilio_service,
    set_datos_venta_session,
    whatsapp_link_service,
)


@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def checkout(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

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
            return redirect('confirmacion')

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
def confirmacion(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

    datos = get_datos_venta_session(request)
    if not datos or 'metodo_envio' not in datos:
        return redirect('checkout')

    context = {
        'order_context': order_context,
        'datos': datos,
        'localidad_coordinar_entrega': localidad_para_coordinar_entrega_service(datos.get('codigo_postal')),
    }

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        if metodo_pago != VentaModel.MetodoPagoChoices.EFECTIVO:
            context['error'] = 'Seleccioná una forma de pago.'
            return render(request, 'ventas/confirmacion.html', context)

        try:
            venta = crear_venta_confirmada_service(
                request.user, datos, datos['metodo_envio'], metodo_pago
            )
            limpiar_datos_venta_session(request)
        except ValueError as e:
            context['error'] = str(e)
            return render(request, 'ventas/confirmacion.html', context)

        enviar_factura_venta_service(venta, request)
        return redirect('pago_local', venta_id=venta.id)

    return render(request, 'ventas/confirmacion.html', context)


@login_required
def pago_local(request, venta_id):
    venta = VentaModel.objects.filter(id=venta_id, usuario=request.user).first()
    if not venta:
        return redirect('ver_carrito')
    return render(request, 'ventas/pago_local.html', {
        'venta': venta,
        'datos_local': DATOS_LOCAL,
        'whatsapp_link': whatsapp_link_service(),
    })
