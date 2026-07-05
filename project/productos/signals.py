from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage

from productos.models import ProductoImagenModel


@receiver(post_delete, sender=ProductoImagenModel)
def auto_delete_imagen_on_delete(sender, instance, **kwargs):
    if instance.imagen and default_storage.exists(instance.imagen.name):
        default_storage.delete(instance.imagen.name)
