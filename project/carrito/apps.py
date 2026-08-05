from django.apps import AppConfig


class CarritoConfig(AppConfig):
    name = 'carrito'

    def ready(self):
        import carrito.signals
