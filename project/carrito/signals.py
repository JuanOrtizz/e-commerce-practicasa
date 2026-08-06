from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import CarritoModel


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_carrito_usuario(sender, instance, created, **kwargs):
    if created:
        CarritoModel.objects.create(usuario=instance)
