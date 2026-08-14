import pytest
from django.conf import settings
from django.urls import reverse

from carrito.models import CarritoItemModel
from productos.models import (
    CategoriaModel, SubcategoriaModel, ProductoModel, TagModel, ColorModel
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
    subcategoria = subcategoria_data
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


@pytest.mark.django_db
def test_resultados_busqueda_con_search(client, producto):
    response = client.get(reverse('resultados_busqueda'), {'search': 'Camiseta'})
    assert response.status_code == 200
    assert len(response.context['productos']) == 1
    assert 'Camiseta' in response.context['titulo']


@pytest.mark.django_db
def test_resultados_busqueda_sin_resultados(client, producto):
    response = client.get(reverse('resultados_busqueda'), {'search': 'zzzzz'})
    assert response.status_code == 200
    assert list(response.context['productos']) == []


@pytest.mark.django_db
def test_buscar_productos_json_sin_search(client, producto):
    response = client.get(reverse('buscar_productos_json'))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_buscar_productos_json_con_search(client, producto):
    response = client.get(reverse('buscar_productos_json'), {'search': 'Camiseta'})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['nombre'] == 'Camiseta básica'
    assert data[0]['precio_transferencia'] == str(producto.precio_transferencia_final)


@pytest.mark.django_db
def test_buscar_productos_json_con_promocion_devuelve_precio_final(client, subcategoria_data):
    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Camiseta promo', descripcion='Test',
        slug='camiseta-promo', sku='SKU-PROMO', precio=200,
        precio_transferencia=180, stock=5,
        promocion=ProductoModel.PromocionChoices.VEINTE,
    )
    producto.refresh_from_db()
    response = client.get(reverse('buscar_productos_json'), {'search': 'Camiseta promo'})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['precio'] == str(producto.precio_final)
    assert data[0]['precio_transferencia'] == str(producto.precio_transferencia_final)


@pytest.mark.django_db
def test_buscar_productos_json_max_4(client, subcategoria_data):
    subcategoria = subcategoria_data
    for i in range(6):
        ProductoModel.objects.create(
            subcategoria=subcategoria,
            nombre=f'Producto {i}',
            descripcion='Test',
            slug=f'producto-{i}',
            sku=f'SKU-{i:03d}',
            precio=100.00 + i,
            precio_transferencia=90.00 + i,
            stock=5,
        )
    response = client.get(reverse('buscar_productos_json'), {'search': 'Producto'})
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.django_db
def test_buscar_productos_json_sin_resultados(client, producto):
    response = client.get(reverse('buscar_productos_json'), {'search': 'zzzzz'})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_lista_stock_restante_anonimo_igual_stock(client, producto):
    producto.stock = 4
    producto.save()
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert response.context['productos'][0].stock_restante == 4


@pytest.mark.django_db
def test_lista_stock_restante_descuenta_carrito(client, usuario, producto):
    producto.stock = 4
    producto.save()
    CarritoItemModel.objects.create(carrito=usuario.carrito, producto=producto, cantidad=3)
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert response.context['productos'][0].stock_restante == 1


@pytest.mark.django_db
def test_lista_stock_restante_suma_variantes(client, usuario, producto, color_data):
    producto.stock = 4
    producto.save()
    rojo = ColorModel.objects.create(**color_data)
    azul = ColorModel.objects.create(nombre='Azul', codigo_hex='#0000FF')
    CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, color_nombre=rojo.nombre, cantidad=2
    )
    CarritoItemModel.objects.create(
        carrito=usuario.carrito, producto=producto, color_nombre=azul.nombre, cantidad=2
    )
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    assert response.context['productos'][0].stock_restante == 0


@pytest.mark.django_db
def test_lista_muestra_boton_sin_stock_cuando_carrito_agota(client, usuario, producto):
    producto.stock = 4
    producto.save()
    CarritoItemModel.objects.create(carrito=usuario.carrito, producto=producto, cantidad=4)
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(reverse('productos'))
    assert response.status_code == 200
    contenido = response.content.decode()
    assert 'Sin stock' in contenido
    assert 'Agregar al Carrito' not in contenido


@pytest.mark.django_db
def test_detalle_stock_restante_descuenta_carrito(client, usuario, producto):
    producto.stock = 4
    producto.save()
    CarritoItemModel.objects.create(carrito=usuario.carrito, producto=producto, cantidad=4)
    client.login(username=usuario.email, password='TestPass123')
    response = client.get(
        reverse('detalle_producto', args=['ropa', 'camisetas', 'camiseta-basica'])
    )
    assert response.status_code == 200
    assert response.context['producto'].stock_restante == 0
    contenido = response.content.decode()
    assert 'Sin stock' in contenido
    assert 'Agregar al Carrito' not in contenido
