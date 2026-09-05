from django.conf import settings
from django.db import models


class VentaModel(models.Model):
    class EstadoChoices(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CONFIRMADA = 'confirmada', 'Confirmada'
        CANCELADA = 'cancelada', 'Cancelada'

    class MetodoEnvioChoices(models.TextChoices):
        RETIRO_LOCAL = 'retiro_local', 'Retiro en el local'
        ENVIO_DOMICILIO = 'envio_domicilio', 'Envío a domicilio'
        COORDINAR_ENTREGA = 'coordinar_entrega', 'Coordinar entrega'

    class MetodoPagoChoices(models.TextChoices):
        MERCADO_PAGO = 'mercado_pago', 'Mercado Pago'
        EFECTIVO = 'efectivo', 'Efectivo (local)'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ventas'
    )
    estado = models.CharField(
        max_length=20, choices=EstadoChoices.choices, default=EstadoChoices.PENDIENTE
    )
    metodo_envio = models.CharField(
        max_length=20, choices=MetodoEnvioChoices.choices
    )
    metodo_pago = models.CharField(
        max_length=20, choices=MetodoPagoChoices.choices
    )
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.CharField(max_length=100, null=True, blank=True)
    codigo_postal = models.CharField(max_length=10, null=True, blank=True)
    notas = models.TextField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Venta {self.id} de {self.nombre}'


class VentaItemModel(models.Model):
    venta = models.ForeignKey(
        VentaModel, on_delete=models.CASCADE, related_name='items'
    )
    producto = models.ForeignKey(
        'productos.ProductoModel', on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_transferencia_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    color_nombre = models.CharField(max_length=50, null=True, blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    medida_nombre = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ventas_items'
        verbose_name = 'Item de la venta'
        verbose_name_plural = 'Items de la venta'

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
