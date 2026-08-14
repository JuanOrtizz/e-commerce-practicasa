from datetime import timedelta
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from base.models import ConsultaModel
from productos.models import CategoriaModel, ProductoModel, TagModel


def formset_tiene_cambios(formset):
    for form in formset.forms:
        if form in formset.deleted_forms:
            return True
        if not form.initial:
            if 'imagen' in form.changed_data:
                return True
        elif form.changed_data:
            return True
    return False


def _serie_por_mes(queryset, campo_fecha, meses=6):
    hoy = timezone.now()
    periodos = []
    for i in range(meses - 1, -1, -1):
        fecha = hoy - timedelta(days=30 * i)
        periodos.append((fecha.year, fecha.month))

    agrupado = (
        queryset
        .annotate(mes=TruncMonth(campo_fecha))
        .values('mes')
        .annotate(total=Count('id'))
    )
    por_periodo = {
        (fila['mes'].year, fila['mes'].month): fila['total'] for fila in agrupado
    }
    return [
        [f'{mes:02d}/{anio}', por_periodo.get((anio, mes), 0)]
        for anio, mes in periodos
    ]


def get_metricas_dashboard():
    desde_mes = timezone.now() - timedelta(days=30)
    mes_anterior = timezone.now() - timedelta(days=60)

    total_productos = ProductoModel.objects.count()
    productos_activos = ProductoModel.objects.filter(activo=True).count()
    productos_sin_stock = ProductoModel.objects.filter(stock=0).count()

    consultas_mes = ConsultaModel.objects.filter(fecha_y_hora__gte=desde_mes).count()
    consultas_mes_anterior = ConsultaModel.objects.filter(
        fecha_y_hora__gte=mes_anterior, fecha_y_hora__lt=desde_mes
    ).count()
    if consultas_mes_anterior:
        consultas_variacion = round(
            (consultas_mes - consultas_mes_anterior) / consultas_mes_anterior * 100
        )
    else:
        consultas_variacion = 100 if consultas_mes else 0

    consultas_por_estado = {'pendiente': 0, 'resuelta': 0}
    for fila in ConsultaModel.objects.values('estado').annotate(total=Count('id')):
        consultas_por_estado[fila['estado']] = fila['total']

    categorias = (
        CategoriaModel.objects
        .annotate(
            total=Count(
                'subcategorias__productos',
                filter=Q(subcategorias__productos__activo=True),
            )
        )
        .order_by('-total')[:5]
    )
    productos_por_categoria = [
        [categoria.nombre, categoria.total]
        for categoria in categorias
        if categoria.total
    ]

    tags = TagModel.objects.annotate(total=Count('productomodel')).order_by('-total')
    tags_distribucion = [
        [tag.get_nombre_display(), tag.total] for tag in tags if tag.total
    ]

    stock_total = ProductoModel.objects.aggregate(total=Sum('stock'))['total'] or 0
    productos_en_promocion = (
        ProductoModel.objects.filter(activo=True)
        .exclude(promocion__isnull=True)
        .exclude(promocion='')
        .count()
    )
    pct_productos_activos = (
        round(productos_activos / total_productos * 100) if total_productos else 0
    )

    return {
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'productos_en_promocion': productos_en_promocion,
        'productos_sin_stock': productos_sin_stock,
        'productos_menos_stock': ProductoModel.objects.filter(activo=True).order_by('stock', 'nombre')[:5],
        'consultas_mes': consultas_mes,
        'consultas_mes_anterior': consultas_mes_anterior,
        'consultas_variacion': consultas_variacion,
        'total_consultas': ConsultaModel.objects.count(),
        'ultimas_consultas': ConsultaModel.objects.all()[:5],
        'stock_total': stock_total,
        'pct_productos_activos': pct_productos_activos,
        'consultas_por_mes': _serie_por_mes(ConsultaModel.objects.all(), 'fecha_y_hora'),
        'consultas_por_estado': consultas_por_estado,
        'productos_por_categoria': productos_por_categoria,
        'tags_distribucion': tags_distribucion,
    }
