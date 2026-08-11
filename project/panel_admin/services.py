from datetime import timedelta
from django.utils import timezone
from base.models import ConsultaModel
from productos.models import ProductoModel


def get_metricas_dashboard():
    desde_mes = timezone.now() - timedelta(days=30)
    return {
        'total_productos': ProductoModel.objects.count(),
        'productos_activos': ProductoModel.objects.filter(activo=True).count(),
        'productos_sin_stock': ProductoModel.objects.filter(stock=0).count(),
        'productos_menos_stock': ProductoModel.objects.filter(activo=True).order_by('stock', 'nombre')[:5],
        'consultas_mes': ConsultaModel.objects.filter(fecha_y_hora__gte=desde_mes).count(),
        'total_consultas': ConsultaModel.objects.count(),
        'ultimas_consultas': ConsultaModel.objects.all()[:5],
    }
