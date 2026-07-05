from django.apps import AppConfig


class ProductosConfig(AppConfig):
    name = 'productos'

    def ready(self):
        import productos.signals
