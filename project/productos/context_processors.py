from .models import CategoriaModel


def categorias_menu(request):
    categorias = CategoriaModel.objects.prefetch_related('subcategorias').all()
    return {'categorias_menu': categorias}
