from decimal import Decimal

import pytest
from django.db import IntegrityError

from productos.models import (
    CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel,
    TagModel, ProductoModel, ProductoImagenModel
)


@pytest.mark.django_db
def test_crear_categoria_con_slug(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    assert categoria.pk is not None
    assert categoria.slug == 'ropa'


@pytest.mark.django_db
def test_slug_autogenerado_categoria():
    categoria = CategoriaModel.objects.create(nombre='Ropa Deportiva')
    assert categoria.slug == 'ropa-deportiva'


@pytest.mark.django_db
def test_str_categoria(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    assert str(categoria) == 'Ropa'


@pytest.mark.django_db
def test_crear_subcategoria_con_fk(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    subcategoria = SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Camisetas', slug='camisetas'
    )
    assert subcategoria.pk is not None
    assert subcategoria.categoria == categoria


@pytest.mark.django_db
def test_slug_autogenerado_subcategoria(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    subcategoria = SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Pantalones'
    )
    assert subcategoria.slug == 'pantalones'


@pytest.mark.django_db
def test_str_subcategoria(categoria_data):
    categoria = CategoriaModel.objects.create(**categoria_data)
    subcategoria = SubcategoriaModel.objects.create(
        categoria=categoria, nombre='Camisetas', slug='camisetas'
    )
    assert str(subcategoria) == 'Camisetas (Ropa)'


@pytest.mark.django_db
def test_crear_color_y_str(color_data):
    color = ColorModel.objects.create(**color_data)
    assert color.pk is not None
    assert str(color) == 'Rojo'


@pytest.mark.django_db
def test_crear_medida_y_str(medida_data):
    medida = MedidaModel.objects.create(**medida_data)
    assert medida.pk is not None
    assert str(medida) == 'S'


@pytest.mark.django_db
def test_crear_tag_y_str(tag_data):
    tag, _ = TagModel.objects.get_or_create(**tag_data)
    assert tag.pk is not None
    assert str(tag) == 'Nuevo'


@pytest.mark.django_db
def test_crear_producto_completo(
    subcategoria_data, color_data, medida_data, tag_data
):
    subcategoria = subcategoria_data
    color = ColorModel.objects.create(**color_data)
    medida = MedidaModel.objects.create(**medida_data)
    tag, _ = TagModel.objects.get_or_create(**tag_data)

    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Camiseta básica',
        descripcion='Camiseta de algodón',
        slug='camiseta-basica',
        sku='CAM-001',
        precio=Decimal('15000'),
        precio_transferencia=Decimal('13500'),
        stock=10,
        peso=0.25,
        promocion=ProductoModel.PromocionChoices.DIEZ,
        destacado=True,
        activo=True,
    )
    producto.colores.add(color)
    producto.medidas.add(medida)

    assert producto.pk is not None
    assert producto.subcategoria == subcategoria
    assert producto.nombre == 'Camiseta básica'
    assert producto.sku == 'CAM-001'
    assert producto.precio == Decimal('15000')
    assert list(producto.colores.all()) == [color]
    assert list(producto.medidas.all()) == [medida]
    assert producto.precio_final == Decimal('13500.00')
    assert producto.precio_transferencia_final == Decimal('12150.00')


@pytest.mark.django_db
def test_save_calcula_precios_finales_sin_promocion(producto_data, subcategoria_data):
    subcategoria = subcategoria_data
    data = {**producto_data, 'precio': Decimal('200'), 'precio_transferencia': Decimal('180')}
    data.pop('promocion', None)
    producto = ProductoModel.objects.create(subcategoria=subcategoria, **data)
    assert producto.precio_final == Decimal('200.00')
    assert producto.precio_transferencia_final == Decimal('180.00')


@pytest.mark.django_db
def test_save_calcula_precios_finales_con_promocion_porcentaje(producto_data, subcategoria_data):
    subcategoria = subcategoria_data
    data = {**producto_data,
        'precio': Decimal('200'),
        'precio_transferencia': Decimal('180'),
        'promocion': ProductoModel.PromocionChoices.VEINTE,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria, **data)
    assert producto.precio_final == Decimal('160.00')
    assert producto.precio_transferencia_final == Decimal('144.00')


@pytest.mark.django_db
def test_save_calcula_precios_finales_con_2x1(producto_data, subcategoria_data):
    subcategoria = subcategoria_data
    data = {**producto_data,
        'precio': Decimal('200'),
        'precio_transferencia': Decimal('180'),
        'promocion': ProductoModel.PromocionChoices.DOS_POR_UNO,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria, **data)
    assert producto.precio_final == Decimal('200.00')
    assert producto.precio_transferencia_final == Decimal('180.00')


@pytest.mark.django_db
def test_2x1_sin_stock_suficiente_elimina_promocion(producto_data, subcategoria_data):
    data = {**producto_data,
        'stock': 1,
        'promocion': ProductoModel.PromocionChoices.DOS_POR_UNO,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria_data, **data)
    assert producto.promocion is None
    assert not producto.tags.filter(nombre=TagModel.TagChoices.OFERTA).exists()


@pytest.mark.django_db
def test_2x1_con_stock_suficiente_conserva_promocion(producto_data, subcategoria_data):
    data = {**producto_data,
        'stock': 2,
        'promocion': ProductoModel.PromocionChoices.DOS_POR_UNO,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria_data, **data)
    assert producto.promocion == ProductoModel.PromocionChoices.DOS_POR_UNO


@pytest.mark.django_db
def test_3x2_sin_stock_suficiente_elimina_promocion(producto_data, subcategoria_data):
    data = {**producto_data,
        'stock': 2,
        'promocion': ProductoModel.PromocionChoices.TRES_POR_DOS,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria_data, **data)
    assert producto.promocion is None
    assert not producto.tags.filter(nombre=TagModel.TagChoices.OFERTA).exists()


@pytest.mark.django_db
def test_3x2_con_stock_suficiente_conserva_promocion(producto_data, subcategoria_data):
    data = {**producto_data,
        'stock': 3,
        'promocion': ProductoModel.PromocionChoices.TRES_POR_DOS,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria_data, **data)
    assert producto.promocion == ProductoModel.PromocionChoices.TRES_POR_DOS


@pytest.mark.django_db
def test_bajar_stock_elimina_promocion_2x1(producto_data, subcategoria_data):
    data = {**producto_data,
        'stock': 10,
        'promocion': ProductoModel.PromocionChoices.DOS_POR_UNO,
    }
    producto = ProductoModel.objects.create(subcategoria=subcategoria_data, **data)
    producto.stock = 1
    producto.save()
    assert producto.promocion is None
    assert not producto.tags.filter(nombre=TagModel.TagChoices.OFERTA).exists()


@pytest.mark.django_db
def test_str_producto(producto_data, subcategoria_data):
    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria, **producto_data
    )
    assert str(producto) == 'Camiseta básica'


@pytest.mark.django_db
def test_slug_autogenerado_producto(subcategoria_data):
    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Camiseta Deportiva',
        descripcion='Test',
        sku='CAM-002',
        precio=100.00,
        precio_transferencia=90.00,
        stock=5,
    )
    assert producto.slug == 'camiseta-deportiva'


@pytest.mark.django_db
def test_sku_unico(subcategoria_data):
    subcategoria = subcategoria_data
    ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Producto A',
        descripcion='Test',
        slug='producto-a',
        sku='SKU-UNICO',
        precio=100.00,
        precio_transferencia=90.00,
        stock=5,
    )
    with pytest.raises(IntegrityError):
        ProductoModel.objects.create(
            subcategoria=subcategoria,
            nombre='Producto B',
            descripcion='Test',
            slug='producto-b',
            sku='SKU-UNICO',
            precio=200.00,
            precio_transferencia=180.00,
            stock=3,
        )


@pytest.mark.django_db
def test_tags_sin_stock_quita_otros(subcategoria_data, tag_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.OFERTA)
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.DESTACADO)
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.NUEVO)
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.ULTIMA_UNIDAD)
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.SIN_STOCK)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=Decimal('100'),
        precio_transferencia=Decimal('90'),
        stock=0,
        destacado=True,
        promocion=ProductoModel.PromocionChoices.DIEZ,
    )

    tags = list(producto.tags.all())
    assert len(tags) == 1
    assert tags[0].nombre == TagModel.TagChoices.SIN_STOCK


@pytest.mark.django_db
def test_tags_destacado(subcategoria_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.DESTACADO)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=100.00,
        precio_transferencia=90.00,
        stock=10,
        destacado=True,
    )

    assert producto.tags.filter(nombre=TagModel.TagChoices.DESTACADO).exists()


@pytest.mark.django_db
def test_tags_oferta_ultima_unidad(subcategoria_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.OFERTA)
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.ULTIMA_UNIDAD)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=Decimal('100'),
        precio_transferencia=Decimal('90'),
        stock=1,
        promocion=ProductoModel.PromocionChoices.DIEZ,
    )

    tags = {t.nombre for t in producto.tags.all()}
    assert TagModel.TagChoices.OFERTA in tags
    assert TagModel.TagChoices.ULTIMA_UNIDAD in tags


@pytest.mark.django_db
def test_tags_nuevo(subcategoria_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.NUEVO)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=100.00,
        precio_transferencia=90.00,
        stock=5,
    )

    assert producto.tags.filter(nombre=TagModel.TagChoices.NUEVO).exists()


@pytest.mark.django_db
def test_tags_nuevo_persiste_al_editar(subcategoria_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.NUEVO)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=100.00,
        precio_transferencia=90.00,
        stock=5,
    )

    producto.precio = Decimal('120')
    producto.destacado = True
    producto.save()

    assert producto.tags.filter(nombre=TagModel.TagChoices.NUEVO).exists()


@pytest.mark.django_db
def test_tags_quita_sin_stock_al_recuperar_stock(subcategoria_data):
    TagModel.objects.get_or_create(nombre=TagModel.TagChoices.SIN_STOCK)

    subcategoria = subcategoria_data
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria,
        nombre='Test',
        descripcion='Test',
        slug='test',
        sku='TEST-001',
        precio=100.00,
        precio_transferencia=90.00,
        stock=0,
    )
    assert producto.tags.filter(nombre=TagModel.TagChoices.SIN_STOCK).exists()

    producto.stock = 5
    producto.save()
    producto.refresh_from_db()
    assert not producto.tags.filter(nombre=TagModel.TagChoices.SIN_STOCK).exists()


@pytest.mark.django_db
def test_primera_imagen_valida_sin_imagen(producto):
    assert producto.primera_imagen_valida is None


@pytest.mark.django_db
def test_crear_producto_imagen_y_str(producto):
    imagen = ProductoImagenModel.objects.create(
        producto=producto, imagen='productos/test.jpg', orden=0
    )
    assert imagen.pk is not None
    assert imagen.orden == 0
    assert str(imagen) == 'Camiseta básica - Imagen 0'
