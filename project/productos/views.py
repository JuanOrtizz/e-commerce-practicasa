from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import ProductoModel, CategoriaModel, SubcategoriaModel
from .services import (get_productos_activos, aplicar_filtros,get_contexto_filtros, get_producto_por_slug)


def _build_contexto(request, productos, titulo):
    # lectura de filtros
    colores_seleccionados = request.GET.getlist('color')
    medidas_seleccionados = request.GET.getlist('medida')
    tags_seleccionados = request.GET.getlist('tag')

    #query params para el paginator
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params_str = query_params.urlencode()

    #query params para categorias y subcategorias
    query_params_filtros = request.GET.copy()
    query_params_filtros.pop('categoria', None)
    query_params_filtros.pop('subcategoria', None)
    query_params_filtros.pop('page', None)
    query_params_filtros_str = query_params_filtros.urlencode()

    contexto = get_contexto_filtros(request)
    contexto.update({
        'productos': productos,
        'titulo': titulo,
        'colores_seleccionados': colores_seleccionados,
        'medidas_seleccionados': medidas_seleccionados,
        'tags_seleccionados': tags_seleccionados,
        'query_params': query_params_str,
        'query_params_filtros': query_params_filtros_str,
        'promociones_choices': ProductoModel.PromocionChoices.choices,
    })
    return contexto


def _render_lista(request, qs, titulo):
    qs = aplicar_filtros(request, qs)
    paginator = Paginator(qs, settings.PRODUCTOS_POR_PAGINA)
    pagina = paginator.get_page(request.GET.get('page'))
    contexto = _build_contexto(request, pagina, titulo)
    return render(request, 'productos/lista.html', contexto)


def productos(request):
    return _render_lista(request, get_productos_activos(), 'Todos los productos')


def productos_por_categoria(request, categoria_slug):
    categoria = get_object_or_404(CategoriaModel, slug=categoria_slug)
    request.GET = request.GET.copy()
    request.GET['categoria'] = categoria_slug
    request.GET.pop('subcategoria', None)
    return _render_lista(request, get_productos_activos(), str(categoria))


def productos_por_subcategoria(request, categoria_slug, subcategoria_slug):
    subcategoria = get_object_or_404(
        SubcategoriaModel, slug=subcategoria_slug, categoria__slug=categoria_slug
    )
    request.GET = request.GET.copy()
    request.GET['categoria'] = categoria_slug
    request.GET['subcategoria'] = subcategoria_slug
    return _render_lista(request, get_productos_activos(), str(subcategoria))


def detalle_producto(request, categoria_slug, subcategoria_slug, slug):
    producto = get_producto_por_slug(categoria_slug, subcategoria_slug, slug)
    return render(request, 'productos/detalle.html', {'producto': producto})


def buscar_productos_json(request):
    search = request.GET.get('search', '').strip()
    if not search:
        return JsonResponse([], safe=False)

    productos = get_productos_activos().filter(nombre__icontains=search)[:4]
    resultados = []
    for p in productos:
        imagen_url = None
        primera = p.primera_imagen_valida
        if primera:
            imagen_url = primera.imagen.url
        resultados.append({
            'id': p.id,
            'nombre': p.nombre,
            'slug': p.slug,
            'precio': str(p.precio_final),
            'precio_transferencia': str(p.precio_transferencia_final),
            'imagen_url': imagen_url,
            'url': p.subcategoria.categoria.slug,
            'url_subcategoria': p.subcategoria.slug,
        })
    return JsonResponse(resultados, safe=False)


def resultados_busqueda(request):
    search = request.GET.get('search', '').strip()
    if not search:
        return _render_lista(request, get_productos_activos(), 'Todos los productos')
    qs = get_productos_activos().filter(nombre__icontains=search)
    return _render_lista(request, qs, f'Resultados para: "{search}"')
