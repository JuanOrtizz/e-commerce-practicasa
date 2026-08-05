from decimal import Decimal

import pytest
from django.http import Http404

from carrito.models import CarritoModel, CarritoItemModel
from carrito.services import (
    get_o_crear_carrito_service, agregar_item_service, actualizar_cantidad_service,
    eliminar_item_service, vaciar_carrito_service, calcular_precios_item_service,
    get_carrito_context_service,
)
from productos.models import ColorModel, MedidaModel, ProductoModel
from usuarios.models import UsuarioModel


@pytest.mark.django_db
def test_get_o_crear_carrito_crea_si_no_existe(usuario):
    CarritoModel.objects.filter(usuario=usuario).delete()
    carrito = get_o_crear_carrito_service(usuario)
    assert carrito.pk is not None
    assert CarritoModel.objects.filter(usuario=usuario).count() == 1


@pytest.mark.django_db
def test_get_o_crear_carrito_retorna_existente(carrito):
    result = get_o_crear_carrito_service(carrito.usuario)
    assert result == carrito
    assert CarritoModel.objects.count() == 1


@pytest.mark.django_db
def test_agregar_item_nuevo(carrito, producto):
    item = agregar_item_service(carrito, producto.id)
    assert item.cantidad == 1
    assert CarritoItemModel.objects.count() == 1


@pytest.mark.django_db
def test_agregar_item_incrementa_cantidad(carrito, producto):
    agregar_item_service(carrito, producto.id)
    item = agregar_item_service(carrito, producto.id)
    assert item.cantidad == 2
    assert CarritoItemModel.objects.count() == 1


@pytest.mark.django_db
def test_agregar_item_sin_stock_raise(carrito, producto):
    producto.stock = 0
    producto.save()
    with pytest.raises(ValueError, match='Producto sin stock'):
        agregar_item_service(carrito, producto.id)


@pytest.mark.django_db
def test_agregar_item_supera_stock_raise(carrito, producto):
    producto.stock = 2
    producto.save()
    agregar_item_service(carrito, producto.id, cantidad=2)
    with pytest.raises(ValueError, match='Producto sin stock'):
        agregar_item_service(carrito, producto.id, cantidad=1)


@pytest.mark.django_db
def test_agregar_item_con_color_y_medida(carrito, producto, color_data, medida_data):
    color = ColorModel.objects.create(**color_data)
    medida = MedidaModel.objects.create(**medida_data)
    item = agregar_item_service(
        carrito, producto.id, color_id=color.id, medida_id=medida.id
    )
    assert item.color_nombre == 'Rojo'
    assert item.color_hex == '#FF0000'
    assert item.medida_nombre == 'S'


@pytest.mark.django_db
def test_agregar_item_combinacion_distinta_crea_separado(carrito, producto, color_data):
    rojo = ColorModel.objects.create(**color_data)
    azul = ColorModel.objects.create(nombre='Azul', codigo_hex='#0000FF')
    item_rojo = agregar_item_service(carrito, producto.id, color_id=rojo.id)
    item_azul = agregar_item_service(carrito, producto.id, color_id=azul.id)
    assert item_rojo.id != item_azul.id
    assert CarritoItemModel.objects.count() == 2


@pytest.mark.django_db
def test_agregar_producto_inactivo_http404(carrito, subcategoria_data):
    inactivo = ProductoModel.objects.create(
        subcategoria=subcategoria_data, nombre='Inactivo', descripcion='Test',
        slug='inactivo', sku='SKU-INA', precio=Decimal('100'),
        precio_transferencia=Decimal('90'), stock=5, activo=False,
    )
    with pytest.raises(Http404):
        agregar_item_service(carrito, inactivo.id)


@pytest.mark.django_db
def test_actualizar_cantidad_valida(carrito, item):
    result = actualizar_cantidad_service(carrito, item.id, 5)
    assert result == item
    item.refresh_from_db()
    assert item.cantidad == 5


@pytest.mark.django_db
def test_actualizar_cantidad_cero_elimina(carrito, item):
    result = actualizar_cantidad_service(carrito, item.id, 0)
    assert result is None
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_actualizar_cantidad_negativa_elimina(carrito, item):
    result = actualizar_cantidad_service(carrito, item.id, -1)
    assert result is None
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_actualizar_cantidad_supera_stock_raise(carrito, item):
    item.producto.stock = 3
    item.producto.save()
    with pytest.raises(ValueError, match='Producto sin stock'):
        actualizar_cantidad_service(carrito, item.id, 5)


@pytest.mark.django_db
def test_actualizar_cantidad_producto_sin_stock_elimina(carrito, item):
    item.producto.stock = 0
    item.producto.save()
    result = actualizar_cantidad_service(carrito, item.id, 2)
    assert result is None
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_actualizar_cantidad_item_otro_carrito_http404(carrito, producto):
    otro_usuario = UsuarioModel.objects.create_user(
        email='otro@example.com', nombre_completo='Otro', password='OtroPass123'
    )
    item_otro = CarritoItemModel.objects.create(
        carrito=otro_usuario.carrito, producto=producto, cantidad=1
    )
    with pytest.raises(Http404):
        actualizar_cantidad_service(carrito, item_otro.id, 3)


@pytest.mark.django_db
def test_eliminar_item_service(carrito, item):
    eliminar_item_service(carrito, item.id)
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_eliminar_item_inexistente_http404(carrito):
    with pytest.raises(Http404):
        eliminar_item_service(carrito, 999)


@pytest.mark.django_db
def test_vaciar_carrito_service(carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, color_nombre='Rojo', cantidad=1
    )
    vaciar_carrito_service(carrito)
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_calcular_precios_sin_promocion(carrito, producto):
    item = CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=2
    )
    data = calcular_precios_item_service(item)
    assert data['cantidad'] == 2
    assert data['cantidad_paga'] == 2
    assert data['precio_unitario'] == Decimal('15000')
    assert data['precio_transferencia_unitario'] == Decimal('13500')
    assert data['subtotal'] == Decimal('30000')
    assert data['subtotal_transferencia'] == Decimal('27000')
    assert data['ahorro'] == Decimal('0')
    assert data['tiene_promocion_porcentaje'] is False
    assert data['promocion'] is None


@pytest.mark.django_db
def test_calcular_precios_con_promocion_porcentaje(carrito, subcategoria_data):
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria_data, nombre='Promo 10', descripcion='Test',
        slug='promo-10', sku='SKU-P10', precio=Decimal('200'),
        precio_transferencia=Decimal('180'), stock=5,
        promocion=ProductoModel.PromocionChoices.DIEZ,
    )
    item = CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=2
    )
    data = calcular_precios_item_service(item)
    assert data['precio_unitario'] == Decimal('180.00')
    assert data['precio_transferencia_unitario'] == Decimal('162.00')
    assert data['precio_original'] == Decimal('200')
    assert data['precio_transferencia_original'] == Decimal('180')
    assert data['subtotal'] == Decimal('360.00')
    assert data['subtotal_transferencia'] == Decimal('324.00')
    assert data['ahorro'] == Decimal('0')
    assert data['tiene_promocion_porcentaje'] is True
    assert data['porcentaje_descuento'] == Decimal('10')
    assert data['cantidad_paga'] == 2


@pytest.mark.django_db
def test_calcular_precios_2x1(carrito, subcategoria_data):
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria_data, nombre='Promo 2x1', descripcion='Test',
        slug='promo-2x1', sku='SKU-2X1', precio=Decimal('200'),
        precio_transferencia=Decimal('180'), stock=10,
        promocion=ProductoModel.PromocionChoices.DOS_POR_UNO,
    )
    item = CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=3
    )
    data = calcular_precios_item_service(item)
    assert data['cantidad_paga'] == 2
    assert data['subtotal'] == Decimal('400.00')
    assert data['subtotal_transferencia'] == Decimal('360.00')
    assert data['ahorro'] == Decimal('200.00')


@pytest.mark.django_db
def test_calcular_precios_3x2(carrito, subcategoria_data):
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria_data, nombre='Promo 3x2', descripcion='Test',
        slug='promo-3x2', sku='SKU-3X2', precio=Decimal('200'),
        precio_transferencia=Decimal('180'), stock=10,
        promocion=ProductoModel.PromocionChoices.TRES_POR_DOS,
    )
    item = CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=5
    )
    data = calcular_precios_item_service(item)
    assert data['cantidad_paga'] == 4
    assert data['subtotal'] == Decimal('800.00')
    assert data['subtotal_transferencia'] == Decimal('720.00')
    assert data['ahorro'] == Decimal('200.00')


@pytest.mark.django_db
def test_contexto_vacio(carrito):
    ctx = get_carrito_context_service(carrito)
    assert ctx['items'] == []
    assert ctx['total'] == Decimal('0')
    assert ctx['total_transferencia'] == Decimal('0')
    assert ctx['total_ahorro'] == Decimal('0')
    assert ctx['cantidad_items'] == 0


@pytest.mark.django_db
def test_contexto_con_items_y_totales(carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=2)
    ctx = get_carrito_context_service(carrito)
    assert len(ctx['items']) == 1
    assert ctx['total'] == Decimal('30000.00')
    assert ctx['total_transferencia'] == Decimal('27000.00')
    assert ctx['total_ahorro'] == Decimal('0')
    assert ctx['cantidad_items'] == 1


@pytest.mark.django_db
def test_contexto_elimina_items_sin_stock(carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=2)
    producto.stock = 0
    producto.save()
    ctx = get_carrito_context_service(carrito)
    assert ctx['items'] == []
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_contexto_cantidad_items(carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=2)
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, color_nombre='Rojo', cantidad=1
    )
    ctx = get_carrito_context_service(carrito)
    assert ctx['cantidad_items'] == 2
