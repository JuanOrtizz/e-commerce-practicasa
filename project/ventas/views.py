from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CheckoutForm, EnvioForm
from .models import VentaModel
from .services import (
    DATOS_LOCAL,
    crear_venta_confirmada_service,
    get_datos_venta_session,
    get_order_context_service,
    limpiar_datos_venta_session,
    set_datos_venta_session,
)


@login_required
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
        'ciudad': datos.get('ciudad', ''),
        'provincia': datos.get('provincia', ''),
        'codigo_postal': datos.get('codigo_postal', ''),
        'notas': datos.get('notas', ''),
    })

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            set_datos_venta_session(request, form.cleaned_data)
            return redirect('envio')

    return render(request, 'ventas/checkout.html', {
        'form': form,
        'order_context': order_context,
    })


@login_required
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
    })


@login_required
def confirmacion(request):
    order_context = get_order_context_service(request.user)
    if not order_context['items']:
        return redirect('ver_carrito')

    datos = get_datos_venta_session(request)
    if not datos or 'metodo_envio' not in datos:
        return redirect('checkout')

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        if metodo_pago not in VentaModel.MetodoPagoChoices.values:
            return render(request, 'ventas/confirmacion.html', {
                'order_context': order_context,
                'datos': datos,
                'error': 'Seleccioná una forma de pago.',
            })

        try:
            venta = crear_venta_confirmada_service(
                request.user, datos, datos['metodo_envio'], metodo_pago
            )
            limpiar_datos_venta_session(request)
        except ValueError as e:
            return render(request, 'ventas/confirmacion.html', {
                'order_context': order_context,
                'datos': datos,
                'error': str(e),
            })

        if metodo_pago == VentaModel.MetodoPagoChoices.EFECTIVO:
            return redirect('pago_local', venta_id=venta.id)
        return redirect('pago', venta_id=venta.id)

    return render(request, 'ventas/confirmacion.html', {
        'order_context': order_context,
        'datos': datos,
    })


@login_required
def pago_local(request, venta_id):
    venta = VentaModel.objects.filter(id=venta_id, usuario=request.user).first()
    if not venta:
        return redirect('ver_carrito')
    return render(request, 'ventas/pago_local.html', {
        'venta': venta,
        'datos_local': DATOS_LOCAL,
    })


@login_required
def pago(request, venta_id):
    venta = VentaModel.objects.filter(id=venta_id, usuario=request.user).first()
    if not venta:
        return redirect('ver_carrito')
    return render(request, 'ventas/pago.html', {
        'venta': venta,
    })
