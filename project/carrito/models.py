from django.db import models
from django.conf import settings


class CarritoModel(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carrito'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carritos'
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'

    def __str__(self):
        return f'Carrito de {self.usuario.email}'

    @property
    def cantidad_items(self):
        return self.items.count()


class CarritoItemModel(models.Model):
    carrito = models.ForeignKey(
        CarritoModel, on_delete=models.CASCADE, related_name='items'
    )
    producto = models.ForeignKey(
        'productos.ProductoModel', on_delete=models.CASCADE
    )
    color_nombre = models.CharField(max_length=50, null=True, blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    medida_nombre = models.CharField(max_length=50, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carrito_items'
        verbose_name = 'Item del carrito'
        verbose_name_plural = 'Items del carrito'
        unique_together = ['carrito', 'producto', 'color_nombre', 'medida_nombre']

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
