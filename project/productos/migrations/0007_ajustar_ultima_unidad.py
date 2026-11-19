from django.db import migrations


def ajustar_ultima_unidad(apps, schema_editor):
    ProductoModel = apps.get_model('productos', 'ProductoModel')
    TagModel = apps.get_model('productos', 'TagModel')
    tag = TagModel.objects.filter(nombre='ultima_unidad').first()
    if not tag:
        return
    for producto in ProductoModel.objects.all():
        if producto.stock == 1:
            producto.tags.add(tag)
        else:
            producto.tags.remove(tag)


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0006_auto_crear_tags'),
    ]
    operations = [
        migrations.RunPython(ajustar_ultima_unidad, migrations.RunPython.noop),
    ]
