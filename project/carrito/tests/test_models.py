import pytest
from django.db import IntegrityError

from carrito.models import CarritoModel, CarritoItemModel


@pytest.mark.django_db
def test_str_carrito(usuario, carrito):
    assert str(carrito) == f'Carrito de {usuario.email}'


@pytest.mark.django_db
def test_cantidad_items_carrito(carrito, producto):
    assert carrito.cantidad_items == 0
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=2)
    assert carrito.cantidad_items == 1


@pytest.mark.django_db
def test_crear_item_y_str(carrito, producto):
    item = CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=3
    )
    assert item.pk is not None
    assert item.cantidad == 3
    assert str(item) == f'3 x {producto.nombre}'


@pytest.mark.django_db
def test_unique_together_misma_combinacion_integrity_error(carrito, producto):
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto,
        color_nombre='Rojo', medida_nombre='S', cantidad=1,
    )
    with pytest.raises(IntegrityError):
        CarritoItemModel.objects.create(
            carrito=carrito, producto=producto,
            color_nombre='Rojo', medida_nombre='S', cantidad=2,
        )


@pytest.mark.django_db
def test_combinacion_color_medida_distinta_permite_items_separados(carrito, producto):
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto,
        color_nombre='Rojo', medida_nombre='S', cantidad=1,
    )
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto,
        color_nombre='Azul', medida_nombre='S', cantidad=1,
    )
    CarritoItemModel.objects.create(
        carrito=carrito, producto=producto, cantidad=1,
    )
    assert CarritoItemModel.objects.filter(carrito=carrito).count() == 3


@pytest.mark.django_db
def test_eliminar_usuario_borra_carrito_e_items(usuario, carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    usuario.delete()
    assert CarritoModel.objects.count() == 0
    assert CarritoItemModel.objects.count() == 0


@pytest.mark.django_db
def test_eliminar_producto_borra_item(carrito, producto):
    CarritoItemModel.objects.create(carrito=carrito, producto=producto, cantidad=1)
    producto.delete()
    assert CarritoItemModel.objects.count() == 0
