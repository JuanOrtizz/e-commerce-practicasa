import pytest

from productos.models import CategoriaModel, SubcategoriaModel
from productos.context_processors import categorias_menu


@pytest.mark.django_db
def test_categorias_menu_retorna_categorias():
    cat1 = CategoriaModel.objects.create(nombre='Ropa', slug='ropa')
    cat2 = CategoriaModel.objects.create(nombre='Accesorios', slug='accesorios')
    SubcategoriaModel.objects.create(categoria=cat1, nombre='Camisetas', slug='camisetas')
    SubcategoriaModel.objects.create(categoria=cat2, nombre='Relojes', slug='relojes')

    class FakeRequest:
        pass

    result = categorias_menu(FakeRequest())
    assert 'categorias_menu' in result
    categorias = list(result['categorias_menu'])
    assert len(categorias) == 2
    for cat in categorias:
        assert list(cat.subcategorias.all())
