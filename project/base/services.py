from productos.models import TagModel
from productos.services import get_productos_activos
from carrito.services import get_cantidades_en_carrito

CANTIDAD_MOSTRAR = 15

def _get_productos_por_tag(tag_nombre):
    return (
        get_productos_activos()
        .filter(tags__nombre=tag_nombre)
        .order_by('-created_at')[:CANTIDAD_MOSTRAR]
    )

def obtener_productos_destacados():
    return _get_productos_por_tag(TagModel.TagChoices.DESTACADO)

def obtener_productos_en_oferta():
    return _get_productos_por_tag(TagModel.TagChoices.OFERTA)

def obtener_productos_ultima_unidad():
    return _get_productos_por_tag(TagModel.TagChoices.ULTIMA_UNIDAD)

def set_stock_restante_productos(usuario, productos):
    cantidades = {}
    if usuario.is_authenticated:
        ids = [p.id for p in productos]
        cantidades = get_cantidades_en_carrito(usuario, ids)
    for p in productos:
        p.stock_restante = p.stock - cantidades.get(p.id, 0)