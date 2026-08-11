from productos.models import TagModel
from productos.services import get_productos_activos

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