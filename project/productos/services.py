from django.shortcuts import get_object_or_404
from .models import ProductoModel, CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel, TagModel

def get_productos_activos():
    return ProductoModel.objects.filter(activo=True).select_related(
        'subcategoria__categoria'
    ).prefetch_related('imagenes', 'colores', 'medidas', 'tags')

def aplicar_filtros(request, productos):
    categoria = request.GET.get('categoria')
    subcategoria = request.GET.get('subcategoria')
    colores = request.GET.getlist('color')
    medidas = request.GET.getlist('medida')
    promocion = request.GET.get('promocion')
    tags = request.GET.getlist('tag')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    orden = request.GET.get('orden', '-created_at')

    if categoria:
        productos = productos.filter(subcategoria__categoria__slug=categoria)
    if subcategoria:
        productos = productos.filter(subcategoria__slug=subcategoria)
    if colores:
        productos = productos.filter(colores__id__in=colores)
    if medidas:
        productos = productos.filter(medidas__id__in=medidas)
    if promocion:
        productos = productos.filter(promocion=promocion)
    if tags:
        productos = productos.filter(tags__nombre__in=tags)
    if precio_min:
        productos = productos.filter(precio_transferencia__gte=precio_min)
    if precio_max:
        productos = productos.filter(precio_transferencia__lte=precio_max)

    ordenes_validos = [
        'precio', '-precio', 'precio_transferencia', '-precio_transferencia',
        'nombre', '-nombre', 'created_at', '-created_at'
    ]
    if orden in ordenes_validos:
        productos = productos.order_by(orden)
    else:
        productos = productos.order_by('-created_at')

    return productos.distinct()


def get_contexto_filtros(request, productos_filtrados=None):
    if productos_filtrados is None:
        productos_filtrados = get_productos_activos()

    categoria_slug = request.GET.get('categoria')
    subcategorias_qs = SubcategoriaModel.objects.none()
    if categoria_slug:
        subcategorias_qs = SubcategoriaModel.objects.filter(
            categoria__slug=categoria_slug
        )

    return {
        'todas_categorias': CategoriaModel.objects.prefetch_related('subcategorias').all(),
        'subcategorias_disponibles': subcategorias_qs,
        'todos_colores': ColorModel.objects.all(),
        'todas_medidas': MedidaModel.objects.all(),
        'tags_disponibles': TagModel.objects.all(),
    }


def get_producto_por_slug(categoria_slug, subcategoria_slug, slug):
    return get_object_or_404(
        ProductoModel,
        slug=slug,
        subcategoria__slug=subcategoria_slug,
        subcategoria__categoria__slug=categoria_slug,
        activo=True
    )
