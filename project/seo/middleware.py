RUTAS_NOINDEX = (
    '/admin/',
    '/panel-admin/',
    '/carrito/',
    '/ventas/',
    '/usuarios/',
    '/productos/search/',
)


class NoIndexMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if any(request.path.startswith(ruta) for ruta in RUTAS_NOINDEX):
            response['X-Robots-Tag'] = 'noindex'
        return response