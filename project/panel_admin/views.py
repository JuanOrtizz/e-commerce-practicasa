from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from base.forms import ConsultaForm
from base.models import ConsultaModel
from productos.forms import MAX_IMAGENES_PRODUCTO, ProductoForm, ProductoImagenFormset
from productos.models import ProductoModel
from usuarios.services import es_administrador

from .services import get_metricas_dashboard


def requiere_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not es_administrador(request.user):
            return redirect('login_admin_tienda')
        return view_func(request, *args, **kwargs)

    return _wrapped


def _formset_tiene_cambios(formset):
    for form in formset.forms:
        if form in formset.deleted_forms:
            return True
        if not form.initial:
            if 'imagen' in form.changed_data:
                return True
        elif form.changed_data:
            return True
    return False


@requiere_admin
def dashboard(request):
    contexto = get_metricas_dashboard()
    return render(request, 'panel_admin/dashboard.html', contexto)


@requiere_admin
def lista_productos(request):
    productos = ProductoModel.objects.select_related('subcategoria__categoria').prefetch_related('imagenes', 'colores', 'medidas', 'tags')
    return render(request, 'panel_admin/productos_lista.html', {'productos': productos})


@requiere_admin
def producto_detalle(request, id):
    producto = get_object_or_404(ProductoModel, id=id)
    return render(request, 'panel_admin/producto_detalle.html', {'producto': producto})


@requiere_admin
def producto_nuevo(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        formset = ProductoImagenFormset(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            producto = form.save()
            formset.instance = producto
            formset.save()
            return JsonResponse({
                "success": True,
                "message": "Producto creado correctamente.",
                "redirect": reverse('panel_producto_detalle', args=[producto.id]),
            })
        if not form.is_valid():
            return JsonResponse({"success": False, "errors": form.errors})
        return JsonResponse({
            "success": False,
            "errors": " ".join(formset.non_form_errors()) or "Revisá las imágenes del producto (Solo recibe JPG, JPEG, PNG y WEBP).",
        })
    else:
        form = ProductoForm()
        formset = ProductoImagenFormset()

    return render(request, 'panel_admin/producto_form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nuevo Producto',
    })


@requiere_admin
def producto_modificar(request, id):
    producto = get_object_or_404(ProductoModel, id=id)
    extra_imagenes = max(0, MAX_IMAGENES_PRODUCTO - producto.imagenes.count())
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        formset = ProductoImagenFormset(request.POST, request.FILES, instance=producto, extra=extra_imagenes)
        if form.is_valid() and formset.is_valid():
            if not form.changed_data and not _formset_tiene_cambios(formset):
                return JsonResponse({"success": False, "message": "No realizaste modificaciones."})
            form.save()
            formset.save()
            return JsonResponse({
                "success": True,
                "message": "Producto modificado correctamente.",
                "redirect": reverse('panel_producto_detalle', args=[producto.id]),
            })
        if not form.is_valid():
            return JsonResponse({"success": False, "errors": form.errors})
        return JsonResponse({
            "success": False,
            "errors": " ".join(formset.non_form_errors()) or "Revisá las imágenes del producto (Solo recibe JPG, JPEG, PNG y WEBP).",
        })
    else:
        form = ProductoForm(instance=producto)
        formset = ProductoImagenFormset(instance=producto, extra=extra_imagenes)

    return render(request, 'panel_admin/producto_form.html', {
        'form': form,
        'formset': formset,
        'titulo': f'Modificar: {producto.nombre}',
        'producto': producto,
    })


@require_POST
@requiere_admin
def producto_eliminar(request, id):
    producto = get_object_or_404(ProductoModel, id=id)
    producto.delete()
    return JsonResponse({
        "success": True,
        "message": f"Producto {producto.nombre} eliminado.",
        "redirect": reverse('panel_productos'),
    })


@requiere_admin
def lista_consultas(request):
    consultas = ConsultaModel.objects.all()
    return render(request, 'panel_admin/consultas_lista.html', {'consultas': consultas})


@requiere_admin
def consulta_detalle(request, id):
    consulta = get_object_or_404(ConsultaModel, id=id)
    return render(request, 'panel_admin/consulta_detalle.html', {'consulta': consulta})


@requiere_admin
def consulta_modificar(request, id):
    consulta = get_object_or_404(ConsultaModel, id=id)
    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta modificada correctamente.')
            return redirect('panel_consulta_detalle', id=consulta.id)
    else:
        form = ConsultaForm(instance=consulta)

    return render(request, 'panel_admin/consulta_form.html', {
        'form': form,
        'titulo': f'Modificar consulta de {consulta.nombre}',
        'consulta': consulta,
    })


@require_POST
@requiere_admin
def consulta_eliminar(request, id):
    consulta = get_object_or_404(ConsultaModel, id=id)
    consulta.delete()
    messages.success(request, 'Consulta eliminada correctamente.')
    return redirect('panel_consultas')


@requiere_admin
def pagos(request):
    return render(request, 'panel_admin/pagos.html')
