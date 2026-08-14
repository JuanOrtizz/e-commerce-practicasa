from functools import wraps

from django.shortcuts import redirect

from usuarios.services import es_administrador


def requiere_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not es_administrador(request.user):
            return redirect('login_admin_tienda')
        return view_func(request, *args, **kwargs)

    return _wrapped
