from django.db import migrations


def crear_tags(apps, schema_editor):
    TagModel = apps.get_model('productos', 'TagModel')
    tags = [
        ('sin_stock', 'Sin Stock'),
        ('destacado', 'Destacado'),
        ('ultima_unidad', 'Última unidad'),
        ('nuevo', 'Nuevo'),
        ('oferta', 'Oferta'),
    ]
    for nombre, _ in tags:
        TagModel.objects.get_or_create(nombre=nombre)


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0005_productomodel_precio_final_and_more'),
    ]
    operations = [
        migrations.RunPython(crear_tags),
    ]
