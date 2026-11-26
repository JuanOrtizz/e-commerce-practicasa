from .services import get_cantidad_total_carrito_service


def carrito_cantidad(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'carrito_cantidad': 0}
    return {'carrito_cantidad': get_cantidad_total_carrito_service(user)}
