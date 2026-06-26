import pytest
from django.http import Http404

from productos.models import (
    CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel,
    TagModel, ProductoModel
)
from productos.services import (
    get_productos_activos, aplicar_filtros,
    get_contexto_filtros, get_producto_por_slug
)


@pytest.mark.django_db
def test_get_productos_activos_solo_retorna_activos(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Activo 1', descripcion='Test',
        slug='activo-1', sku='SKU-001', precio=100, precio_transferencia=90,
        stock=5, activo=True,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Activo 2', descripcion='Test',
        slug='activo-2', sku='SKU-002', precio=200, precio_transferencia=180,
        stock=3, activo=True,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Inactivo', descripcion='Test',
        slug='inactivo', sku='SKU-003', precio=300, precio_transferencia=270,
        stock=0, activo=False,
    )

    qs = get_productos_activos()
    assert qs.count() == 2
    nombres = {p.nombre for p in qs}
    assert nombres == {'Activo 1', 'Activo 2'}


@pytest.mark.django_db
def test_get_productos_activos_vacio():
    qs = get_productos_activos()
    assert qs.count() == 0


@pytest.mark.django_db
def test_aplicar_filtros_por_categoria(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()
    categoria = subcategoria_data['categoria']

    otra_categoria = CategoriaModel.objects.create(
        nombre='Otra', slug='otra'
    )
    otra_sub = SubcategoriaModel.objects.create(
        categoria=otra_categoria, nombre='Otra Sub', slug='otra-sub'
    )

    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='En Ropa', descripcion='Test',
        slug='en-ropa', sku='SKU-001', precio=100, precio_transferencia=90,
        stock=5,
    )
    ProductoModel.objects.create(
        subcategoria=otra_sub, nombre='En Otra', descripcion='Test',
        slug='en-otra', sku='SKU-002', precio=200, precio_transferencia=180,
        stock=3,
    )

    class FakeRequest:
        GET = {'categoria': 'ropa'}

    qs = aplicar_filtros(FakeRequest(), get_productos_activos())
    assert qs.count() == 1
    assert qs[0].nombre == 'En Ropa'


@pytest.mark.django_db
def test_aplicar_filtros_por_color(subcategoria_data, color_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()
    rojo = ColorModel.objects.create(**color_data)
    azul = ColorModel.objects.create(nombre='Azul', codigo_hex='#0000FF')

    p_rojo = ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Rojo', descripcion='Test',
        slug='rojo', sku='SKU-001', precio=100, precio_transferencia=90,
        stock=5,
    )
    p_rojo.colores.add(rojo)

    p_azul = ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Azul', descripcion='Test',
        slug='azul', sku='SKU-002', precio=200, precio_transferencia=180,
        stock=3,
    )
    p_azul.colores.add(azul)

    class FakeRequest:
        GET = {'color': [str(rojo.id)]}

    qs = aplicar_filtros(FakeRequest(), get_productos_activos())
    assert qs.count() == 1
    assert qs[0].nombre == 'Rojo'


@pytest.mark.django_db
def test_aplicar_filtros_por_precio_min_y_max(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()

    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Barato', descripcion='Test',
        slug='barato', sku='SKU-001', precio=100, precio_transferencia=50,
        stock=5,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Medio', descripcion='Test',
        slug='medio', sku='SKU-002', precio=200, precio_transferencia=150,
        stock=3,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Caro', descripcion='Test',
        slug='caro', sku='SKU-003', precio=300, precio_transferencia=250,
        stock=1,
    )

    class FakeRequest:
        GET = {'precio_min': '100', 'precio_max': '200'}

    qs = aplicar_filtros(FakeRequest(), get_productos_activos())
    assert qs.count() == 1
    assert qs[0].nombre == 'Medio'


@pytest.mark.django_db
def test_aplicar_filtros_orden_valido(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()

    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Zapatilla', descripcion='Test',
        slug='zapatilla', sku='SKU-001', precio=300, precio_transferencia=250,
        stock=5,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Bota', descripcion='Test',
        slug='bota', sku='SKU-002', precio=100, precio_transferencia=80,
        stock=3,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Campera', descripcion='Test',
        slug='campera', sku='SKU-003', precio=200, precio_transferencia=180,
        stock=1,
    )

    class FakeRequest:
        GET = {'orden': 'nombre'}

    qs = aplicar_filtros(FakeRequest(), get_productos_activos())
    nombres = [p.nombre for p in qs]
    assert nombres == ['Bota', 'Campera', 'Zapatilla']


@pytest.mark.django_db
def test_aplicar_filtros_orden_invalido_vuelve_default(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()

    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Ultimo', descripcion='Test',
        slug='ultimo', sku='SKU-001', precio=100, precio_transferencia=80,
        stock=5,
    )
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Primero', descripcion='Test',
        slug='primero', sku='SKU-002', precio=200, precio_transferencia=180,
        stock=3, created_at='2023-01-01 00:00:00+00',
    )

    class FakeRequest:
        GET = {'orden': 'invalido'}

    qs = aplicar_filtros(FakeRequest(), get_productos_activos())
    assert qs.first().nombre == 'Ultimo'


@pytest.mark.django_db
def test_get_producto_por_slug_exitoso(producto):
    result = get_producto_por_slug('ropa', 'camisetas', 'camiseta-basica')
    assert result == producto
    assert result.nombre == 'Camiseta básica'


@pytest.mark.django_db
def test_get_producto_por_slug_404_slug_inexistente(producto):
    with pytest.raises(Http404):
        get_producto_por_slug('ropa', 'camisetas', 'slug-inexistente')


@pytest.mark.django_db
def test_get_producto_por_slug_404_producto_inactivo(subcategoria_data):
    subcategoria = subcategoria_data['categoria'].subcategorias.first()
    ProductoModel.objects.create(
        subcategoria=subcategoria, nombre='Inactivo', descripcion='Test',
        slug='inactivo', sku='SKU-001', precio=100, precio_transferencia=90,
        stock=0, activo=False,
    )
    with pytest.raises(Http404):
        get_producto_por_slug('ropa', 'camisetas', 'inactivo')


@pytest.mark.django_db
def test_get_contexto_filtros_incluye_todos(categoria_data, color_data, medida_data):
    CategoriaModel.objects.create(**categoria_data)
    ColorModel.objects.create(**color_data)
    MedidaModel.objects.create(**medida_data)
    TagModel.objects.create(nombre=TagModel.TagChoices.NUEVO)

    class FakeRequest:
        GET = {}

    ctx = get_contexto_filtros(FakeRequest())
    assert ctx['todas_categorias'].count() == 1
    assert ctx['subcategorias_disponibles'].count() == 0
    assert ctx['todos_colores'].count() == 1
    assert ctx['todas_medidas'].count() == 1
    assert ctx['tags_disponibles'].count() == 1


@pytest.mark.django_db
def test_get_contexto_filtros_con_categoria_filtra_subcategorias(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    otra = CategoriaModel.objects.create(nombre='Otra', slug='otra')
    SubcategoriaModel.objects.create(categoria=categoria, nombre='Sub A', slug='sub-a')
    SubcategoriaModel.objects.create(categoria=otra, nombre='Sub B', slug='sub-b')

    class FakeRequest:
        GET = {'categoria': 'ropa'}

    ctx = get_contexto_filtros(FakeRequest())
    assert ctx['subcategorias_disponibles'].count() == 1
    assert ctx['subcategorias_disponibles'][0].nombre == 'Sub A'
