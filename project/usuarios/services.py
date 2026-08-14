from .models import UsuarioModel

def es_administrador(user):
    return (
        user.is_authenticated
        and user.tipo in (
            UsuarioModel.Tipos.ADMINISTRADOR_TIENDA,
            UsuarioModel.Tipos.SUPERUSER,
        )
    )
