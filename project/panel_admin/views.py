from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from base.forms import ConsultaAdminForm
from base.models import ConsultaModel
from productos.forms import (
    MAX_IMAGENES_PRODUCTO,
    CategoriaForm,
    ColorForm,
    MedidaForm,
    ProductoForm,
    ProductoImagenFormset,
    SubcategoriaForm,
)
from productos.models import (
    CategoriaModel,
    ColorModel,
    MedidaModel,
    ProductoModel,
    SubcategoriaModel,
)

from .decorators import requiere_admin
from .services import formset_tiene_cambios, get_metricas_dashboard


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
            if not form.changed_data and not formset_tiene_cambios(formset):
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
        "message": f"Producto {producto.nombre} eliminado."
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
        form = ConsultaAdminForm(request.POST, instance=consulta)
        if form.is_valid():
            if not form.changed_data:
                return JsonResponse({"success": False, "message": "No realizaste modificaciones."})
            form.save()
            return JsonResponse({
                "success": True,
                "message": "Consulta modificada correctamente.",
                "redirect": reverse('panel_consulta_detalle', args=[consulta.id]),
            })
    else:
        form = ConsultaAdminForm(instance=consulta)

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
    return JsonResponse({
        "success": True,
        "message": f"Consulta de {consulta.nombre} eliminada."
    })


@requiere_admin
def referencias(request):
    return render(request, 'panel_admin/referencias.html', {
        'colores': ColorModel.objects.all(),
        'medidas': MedidaModel.objects.all(),
        'categorias': CategoriaModel.objects.all(),
        'subcategorias': SubcategoriaModel.objects.select_related('categoria'),
        'form_color': ColorForm(),
        'form_medida': MedidaForm(),
        'form_categoria': CategoriaForm(),
        'form_subcategoria': SubcategoriaForm(),
    })


@requiere_admin
def color_nuevo(request):
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            color = form.save()
            return JsonResponse({
                "success": True,
                "message": f"Color {color.nombre} creado.",
                "redirect": reverse('panel_referencias'),
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return render(request, 'panel_admin/referencia_form.html', {
        'form': ColorForm(),
        'titulo': 'Nuevo color',
        'entidad': 'color',
        'btn_text': 'Crear color',
    })


@requiere_admin
def medida_nuevo(request):
    if request.method == 'POST':
        form = MedidaForm(request.POST)
        if form.is_valid():
            medida = form.save()
            return JsonResponse({
                "success": True,
                "message": f"Medida {medida.nombre} creada.",
                "redirect": reverse('panel_referencias'),
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return render(request, 'panel_admin/referencia_form.html', {
        'form': MedidaForm(),
        'titulo': 'Nueva medida',
        'entidad': 'medida',
        'btn_text': 'Crear medida',
    })


@requiere_admin
def categoria_nuevo(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            return JsonResponse({
                "success": True,
                "message": f"Categoría {categoria.nombre} creada.",
                "redirect": reverse('panel_referencias'),
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return render(request, 'panel_admin/referencia_form.html', {
        'form': CategoriaForm(),
        'titulo': 'Nueva categoría',
        'entidad': 'categoria',
        'btn_text': 'Crear categoría',
    })


@requiere_admin
def subcategoria_nuevo(request):
    if request.method == 'POST':
        form = SubcategoriaForm(request.POST)
        if form.is_valid():
            subcategoria = form.save()
            return JsonResponse({
                "success": True,
                "message": f"Subcategoría {subcategoria.nombre} creada.",
                "redirect": reverse('panel_referencias'),
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return render(request, 'panel_admin/referencia_form.html', {
        'form': SubcategoriaForm(),
        'titulo': 'Nueva subcategoría',
        'entidad': 'subcategoria',
        'btn_text': 'Crear subcategoría',
    })


@require_POST
@requiere_admin
def color_eliminar(request, id):
    color = get_object_or_404(ColorModel, id=id)
    color.delete()
    return JsonResponse({
        "success": True,
        "message": f"Color {color.nombre} eliminado."
    })


@require_POST
@requiere_admin
def medida_eliminar(request, id):
    medida = get_object_or_404(MedidaModel, id=id)
    medida.delete()
    return JsonResponse({
        "success": True,
        "message": f"Medida {medida.nombre} eliminada."
    })


@require_POST
@requiere_admin
def categoria_eliminar(request, id):
    categoria = get_object_or_404(CategoriaModel, id=id)
    if categoria.subcategorias.exists():
        return JsonResponse({
            "success": False,
            "message": f"No se puede eliminar la categoría '{categoria.nombre}'. Tiene subcategorías asociadas.",
        })
    categoria.delete()
    return JsonResponse({
        "success": True,
        "message": f"Categoría {categoria.nombre} eliminada."
    })


@require_POST
@requiere_admin
def subcategoria_eliminar(request, id):
    subcategoria = get_object_or_404(SubcategoriaModel, id=id)
    if subcategoria.productos.exists():
        return JsonResponse({
            "success": False,
            "message": f"No se puede eliminar la subcategoría '{subcategoria.nombre}'. Tiene productos asociados.",
        })
    subcategoria.delete()
    return JsonResponse({
        "success": True,
        "message": f"Subcategoría {subcategoria.nombre} eliminada."
    })


@requiere_admin
def pagos(request):
    return render(request, 'panel_admin/pagos.html')
