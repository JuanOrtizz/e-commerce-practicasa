from django.db import migrations


def ajustar_stock_maximo(apps, schema_editor):
    ProductoModel = apps.get_model('productos', 'ProductoModel')
    ProductoModel.objects.filter(stock__gt=1000).update(stock=1000)


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0008_alter_categoriamodel_slug_alter_productomodel_slug_and_more'),
    ]

    operations = [
        migrations.RunPython(ajustar_stock_maximo, migrations.RunPython.noop),
    ]
