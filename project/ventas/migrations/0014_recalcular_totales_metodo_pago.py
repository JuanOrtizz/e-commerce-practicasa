from decimal import Decimal

from django.db import migrations


def _cantidad_paga(item):
    if item.promocion == '2x1':
        return (item.cantidad // 2) + (item.cantidad % 2)
    if item.promocion == '3x2':
        return ((item.cantidad // 3) * 2) + (item.cantidad % 3)
    return item.cantidad


def _recalcular(venta, items, transferencia):
    subtotal = Decimal('0')
    for item in items:
        precio = (
            item.precio_transferencia_unitario
            if transferencia
            else item.precio_unitario
        )
        subtotal += precio * _cantidad_paga(item)
    venta.subtotal = subtotal
    venta.total = subtotal + venta.costo_envio
    venta.save(update_fields=['subtotal', 'total'])


def recalcular_totales_metodo_pago(apps, schema_editor):
    VentaModel = apps.get_model('ventas', 'VentaModel')
    VentaItemModel = apps.get_model('ventas', 'VentaItemModel')

    ventas = VentaModel.objects.filter(
        metodo_pago__in=('efectivo', 'transferencia')
    )
    for venta in ventas:
        items = list(VentaItemModel.objects.filter(venta_id=venta.id))
        _recalcular(venta, items, transferencia=True)


def revertir_totales_metodo_pago(apps, schema_editor):
    VentaModel = apps.get_model('ventas', 'VentaModel')
    VentaItemModel = apps.get_model('ventas', 'VentaItemModel')

    ventas = VentaModel.objects.filter(
        metodo_pago__in=('efectivo', 'transferencia')
    )
    for venta in ventas:
        items = list(VentaItemModel.objects.filter(venta_id=venta.id))
        _recalcular(venta, items, transferencia=False)


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0013_alter_ventaitemmodel_nombre_producto_and_more'),
    ]

    operations = [
        migrations.RunPython(
            recalcular_totales_metodo_pago,
            revertir_totales_metodo_pago,
        ),
    ]
