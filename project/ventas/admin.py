from django.contrib import admin

from .models import VentaItemModel, VentaModel
from .services import revertir_stock_venta_service


class VentaItemInline(admin.TabularInline):
    model = VentaItemModel
    extra = 0
    readonly_fields = [
        'producto', 'cantidad', 'precio_unitario', 'precio_transferencia_unitario',
        'color_nombre', 'medida_nombre',
    ]


@admin.register(VentaModel)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'estado', 'metodo_pago', 'metodo_envio', 'total', 'created_at']
    list_filter = ['estado', 'metodo_pago', 'metodo_envio']
    readonly_fields = [
        'usuario', 'nombre', 'email', 'telefono', 'direccion', 'numero', 'ciudad',
        'provincia', 'codigo_postal', 'notas', 'metodo_envio', 'metodo_pago',
        'subtotal', 'costo_envio', 'total', 'created_at',
    ]
    inlines = [VentaItemInline]

    def delete_model(self, request, obj):
        if obj.estado != VentaModel.EstadoChoices.CANCELADA:
            revertir_stock_venta_service(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for venta in queryset:
            if venta.estado != VentaModel.EstadoChoices.CANCELADA:
                revertir_stock_venta_service(venta)
        super().delete_queryset(request, queryset)
