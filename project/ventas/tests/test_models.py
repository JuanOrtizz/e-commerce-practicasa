import pytest
from django.db.models.deletion import ProtectedError

from ventas.services import crear_venta_confirmada_service


@pytest.mark.django_db
def test_producto_con_items_de_venta_no_se_puede_eliminar(carrito, producto, item, usuario, datos_checkout):
    crear_venta_confirmada_service(usuario, datos_checkout, 'retiro_local', 'efectivo')
    with pytest.raises(ProtectedError):
        producto.delete()