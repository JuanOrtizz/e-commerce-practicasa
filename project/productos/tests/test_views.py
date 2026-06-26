import pytest
from django.conf import settings
from django.urls import reverse

from productos.models import (
    CategoriaModel, SubcategoriaModel, ProductoModel, TagModel
)


@pytest.mark.django_db
def test_productos_lista_200_sin_productos(client):
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert 'productos' in response.context
    assert list(response.context['productos']) == []


@pytest.mark.django_db
def test_productos_lista_200_con_productos(client, producto):
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert response.context['titulo'] == 'Todos los productos'
    assert len(response.context['productos']) == 1


@pytest.mark.django_db
def test_productos_por_categoria_200(client, producto):
    response = client.get(reverse('productos_por_categoria', args=['ropa']))
    assert response.status_code == 200
    assert response.context['titulo'] == 'Ropa'


@pytest.mark.django_db
def test_productos_por_categoria_404(client):
    response = client.get(
        reverse('productos_por_categoria', args=['categoria-inexistente'])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_productos_por_subcategoria_200(client, producto):
    response = client.get(
        reverse('productos_por_subcategoria', args=['ropa', 'camisetas'])
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_productos_por_subcategoria_404(client):
    response = client.get(
        reverse('productos_por_subcategoria', args=['ropa', 'sub-inexistente'])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_detalle_producto_200(client, producto):
    response = client.get(
        reverse('detalle_producto', args=['ropa', 'camisetas', 'camiseta-basica'])
    )
    assert response.status_code == 200
    assert response.context['producto'] == producto


@pytest.mark.django_db
def test_detalle_producto_404(client):
    response = client.get(
        reverse('detalle_producto', args=['ropa', 'camisetas', 'slug-inexistente'])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_paginacion(client, subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()
    for i in range(settings.PRODUCTOS_POR_PAGINA + 1):
        ProductoModel.objects.create(
            subcategoria=subcategoria,
            nombre=f'Producto {i}',
            descripcion='Test',
            slug=f'producto-{i}',
            sku=f'SKU-P{i:03d}',
            precio=100.00 + i,
            precio_transferencia=90.00 + i,
            stock=5,
        )

    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert len(response.context['productos']) == settings.PRODUCTOS_POR_PAGINA


@pytest.mark.django_db
def test_filtros_en_query_params_se_pasan(client, producto):
    response = client.get(reverse('productos'), {'orden': 'nombre'})
    assert response.status_code == 200
    assert 'query_params' in response.context
    assert 'orden=nombre' in response.context['query_params']
