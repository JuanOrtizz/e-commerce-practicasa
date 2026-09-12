from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import VentaModel
from .services import revertir_stock_venta_service


@receiver(pre_save, sender=VentaModel)
def guardar_estado_anterior(sender, instance, **kwargs):
    if instance.pk:
        instance._estado_anterior = (
            VentaModel.objects.filter(pk=instance.pk)
            .values_list('estado', flat=True)
            .first()
        )


@receiver(post_save, sender=VentaModel)
def revertir_stock_si_cancelada(sender, instance, **kwargs):
    anterior = getattr(instance, '_estado_anterior', None)
    if (
        instance.estado == VentaModel.EstadoChoices.CANCELADA
        and anterior != VentaModel.EstadoChoices.CANCELADA
    ):
        revertir_stock_venta_service(instance)