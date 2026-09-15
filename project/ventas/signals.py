from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import VentaModel
from .services import sincronizar_stock_venta_service


@receiver(pre_save, sender=VentaModel)
def guardar_estado_anterior(sender, instance, **kwargs):
    if instance.pk:
        instance._estado_anterior = (
            VentaModel.objects.filter(pk=instance.pk)
            .values_list('estado', flat=True)
            .first()
        )


@receiver(post_save, sender=VentaModel)
def sincronizar_stock_al_cambiar_estado(sender, instance, **kwargs):
    if kwargs.get('created'):
        return
    anterior = getattr(instance, '_estado_anterior', None)
    sincronizar_stock_venta_service(instance, anterior)