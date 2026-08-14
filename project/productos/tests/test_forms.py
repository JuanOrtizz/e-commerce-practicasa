import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from productos.forms import ProductoForm, ProductoImagenForm, ProductoImagenFormset
from productos.models import ProductoImagenModel, ProductoModel, SubcategoriaModel


def _imagen_png(nombre):
    png = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
    )
    return SimpleUploadedFile(nombre, png, content_type='image/png')


def imagen_png_valida():
    return _imagen_png('foto.png')


def producto_form_data(subcategoria, **kwargs):
    data = {
        'subcategoria': subcategoria.id,
        'nombre': 'Camiseta básica',
        'descripcion': 'Camiseta de algodón',
        'sku': 'CAM-001',
        'precio': '15000',
        'precio_transferencia': '13500',
        'stock': '10',
        'colores': [],
        'medidas': [],
        'promocion': '',
        'tags': [],
        'destacado': False,
        'activo': True,
    }
    data.update(kwargs)
    return data


@pytest.mark.django_db
def test_producto_form_valido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data))
    assert form.is_valid()


@pytest.mark.django_db
def test_nombre_menor_a_2_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, nombre='A'))
    assert not form.is_valid()
    assert 'Nombre: de 2 a 200 caracteres.' in form.errors['nombre']


@pytest.mark.django_db
def test_nombre_mayor_a_200_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, nombre='a' * 201))
    assert not form.is_valid()
    assert 'Nombre: de 2 a 200 caracteres.' in form.errors['nombre']


@pytest.mark.django_db
def test_descripcion_menor_a_2_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, descripcion='X'))
    assert not form.is_valid()
    assert 'Descripción: de 2 a 1000 caracteres.' in form.errors['descripcion']


@pytest.mark.django_db
def test_descripcion_mayor_a_1000_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, descripcion='a' * 1001))
    assert not form.is_valid()
    assert 'Descripción: de 2 a 1000 caracteres.' in form.errors['descripcion']


@pytest.mark.django_db
def test_sku_menor_a_2_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, sku='A'))
    assert not form.is_valid()
    assert 'SKU: de 2 a 50 caracteres.' in form.errors['sku']


@pytest.mark.django_db
def test_sku_mayor_a_50_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, sku='A' * 51))
    assert not form.is_valid()
    assert 'SKU: de 2 a 50 caracteres.' in form.errors['sku']


@pytest.mark.django_db
def test_sku_trim_y_mayusculas(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, sku='  cam-001  '))
    assert form.is_valid()
    assert form.cleaned_data['sku'] == 'CAM-001'


@pytest.mark.django_db
def test_sku_duplicado_invalido(subcategoria_data, producto):
    form = ProductoForm(data=producto_form_data(subcategoria_data, nombre='Camiseta Negra', sku=producto.sku))
    assert not form.is_valid()
    assert 'Ya existe un producto con este código.' in form.errors['sku']


@pytest.mark.django_db
def test_promocion_2x1_sin_stock_suficiente_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(
        subcategoria_data, promocion='2x1', stock='1'
    ))
    assert not form.is_valid()
    assert 'La promoción 2x1 requiere al menos 2 unidades de stock.' in form.errors['promocion']


@pytest.mark.django_db
def test_promocion_2x1_con_stock_suficiente_valido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(
        subcategoria_data, promocion='2x1', stock='2'
    ))
    assert form.is_valid()


@pytest.mark.django_db
def test_promocion_3x2_sin_stock_suficiente_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(
        subcategoria_data, promocion='3x2', stock='2'
    ))
    assert not form.is_valid()
    assert 'La promoción 3x2 requiere al menos 3 unidades de stock.' in form.errors['promocion']


@pytest.mark.django_db
def test_promocion_3x2_con_stock_suficiente_valido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(
        subcategoria_data, promocion='3x2', stock='3'
    ))
    assert form.is_valid()


@pytest.mark.django_db
def test_bajar_stock_con_promocion_existente_guarda_y_elimina_promo(subcategoria_data):
    producto = ProductoModel.objects.create(
        subcategoria=subcategoria_data, nombre='Promo 3x2', descripcion='Test',
        slug='promo-3x2-existente', sku='SKU-P32', precio='300',
        precio_transferencia='270', stock=3,
        promocion=ProductoModel.PromocionChoices.TRES_POR_DOS,
    )
    form = ProductoForm(
        data=producto_form_data(subcategoria_data, sku=producto.sku, stock='2', promocion='3x2'),
        instance=producto,
    )
    assert form.is_valid()
    form.save()
    producto.refresh_from_db()
    assert producto.promocion is None


@pytest.mark.django_db
def test_nombre_duplicado_invalido(subcategoria_data, producto):
    form = ProductoForm(data=producto_form_data(subcategoria_data, sku='CAM-002', nombre=producto.nombre))
    assert not form.is_valid()
    assert 'Ya existe un producto creado con ese nombre.' in form.errors['nombre']


@pytest.mark.django_db
def test_nombre_duplicado_case_insensitive_invalido(subcategoria_data, producto):
    form = ProductoForm(data=producto_form_data(subcategoria_data, sku='CAM-002', nombre=producto.nombre.upper()))
    assert not form.is_valid()
    assert 'Ya existe un producto creado con ese nombre.' in form.errors['nombre']


@pytest.mark.django_db
def test_nombre_mismo_producto_al_editar_valido(subcategoria_data, producto):
    form = ProductoForm(
        data=producto_form_data(producto.subcategoria, sku='CAM-002', nombre=producto.nombre),
        instance=producto,
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_subcategoria_editable_en_formulario_nuevo(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data))
    assert form.fields['subcategoria'].disabled is False


@pytest.mark.django_db
def test_subcategoria_deshabilitada_al_editar(producto):
    form = ProductoForm(instance=producto)
    assert form.fields['subcategoria'].disabled is True


@pytest.mark.django_db
def test_editar_no_cambia_subcategoria(subcategoria_data, producto):
    otra_sub = SubcategoriaModel.objects.create(
        categoria=subcategoria_data.categoria, nombre='Pantalones', slug='pantalones'
    )
    form = ProductoForm(
        data=producto_form_data(otra_sub, nombre='Camiseta modificada', sku='CAM-002'),
        instance=producto,
    )
    assert form.is_valid()
    form.save()
    producto.refresh_from_db()
    assert producto.subcategoria == subcategoria_data


@pytest.mark.django_db
def test_precio_cero_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, precio='0'))
    assert not form.is_valid()
    assert 'El precio debe ser mayor a 0.' in form.errors['precio']


@pytest.mark.django_db
def test_precio_negativo_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, precio='-100'))
    assert not form.is_valid()
    assert 'El precio debe ser mayor a 0.' in form.errors['precio']


@pytest.mark.django_db
def test_precio_supera_maximo_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, precio='100000000'))
    assert not form.is_valid()


@pytest.mark.django_db
def test_precio_transferencia_cero_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, precio_transferencia='0'))
    assert not form.is_valid()
    assert 'El precio de transferencia debe ser mayor a 0.' in form.errors['precio_transferencia']


@pytest.mark.django_db
def test_precio_transferencia_mayor_al_precio_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, precio='100', precio_transferencia='200'))
    assert not form.is_valid()
    assert 'El precio de transferencia no puede ser mayor al precio.' in form.errors['precio_transferencia']


@pytest.mark.django_db
def test_stock_negativo_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, stock='-5'))
    assert not form.is_valid()
    assert 'El stock no puede ser negativo.' in form.errors['stock']


@pytest.mark.django_db
def test_peso_cero_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, peso='0'))
    assert not form.is_valid()
    assert 'El peso debe ser mayor a 0.' in form.errors['peso']


@pytest.mark.django_db
def test_peso_negativo_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, peso='-1'))
    assert not form.is_valid()
    assert 'El peso debe ser mayor a 0.' in form.errors['peso']


@pytest.mark.django_db
def test_peso_supera_maximo_invalido(subcategoria_data):
    form = ProductoForm(data=producto_form_data(subcategoria_data, peso='10000'))
    assert not form.is_valid()


@pytest.mark.django_db
def test_imagen_valida_sin_orden():
    form = ProductoImagenForm({}, {'imagen': imagen_png_valida()})
    assert form.is_valid()


@pytest.mark.django_db
def test_imagen_archivo_invalido():
    form = ProductoImagenForm(
        {},
        {'imagen': SimpleUploadedFile('foto.txt', b'contenido', content_type='text/plain')},
    )
    assert not form.is_valid()


def formset_data(cantidad, deletes=None):
    deletes = deletes or {}
    data = {
        'imagenes-TOTAL_FORMS': str(cantidad),
        'imagenes-INITIAL_FORMS': '0',
        'imagenes-MIN_NUM_FORMS': '0',
        'imagenes-MAX_NUM_FORMS': '1000',
    }
    for i in deletes:
        data[f'imagenes-{i}-DELETE'] = 'on'
    return data


@pytest.mark.django_db
def test_formset_sin_ordenes_valido():
    formset = ProductoImagenFormset(data=formset_data(2))
    assert formset.is_valid()


@pytest.mark.django_db
def test_formset_con_delete_valido():
    formset = ProductoImagenFormset(data=formset_data(2, deletes={0}))
    assert formset.is_valid()


@pytest.mark.django_db
def test_formset_asigna_orden_secuencial(producto):
    data = formset_data(2)
    files = {
        'imagenes-0-imagen': _imagen_png('foto1.png'),
        'imagenes-1-imagen': _imagen_png('foto2.png'),
    }
    formset = ProductoImagenFormset(data=data, files=files, instance=producto)
    assert formset.is_valid()
    formset.save()
    ordenes = list(producto.imagenes.values_list('orden', flat=True))
    assert ordenes == [0, 1]


@pytest.mark.django_db
def test_formset_reordena_al_eliminar(producto):
    img0 = ProductoImagenModel.objects.create(producto=producto, imagen='productos/a.jpg', orden=0)
    img1 = ProductoImagenModel.objects.create(producto=producto, imagen='productos/b.jpg', orden=1)
    img2 = ProductoImagenModel.objects.create(producto=producto, imagen='productos/c.jpg', orden=2)
    data = {
        'imagenes-TOTAL_FORMS': '3',
        'imagenes-INITIAL_FORMS': '3',
        'imagenes-MIN_NUM_FORMS': '0',
        'imagenes-MAX_NUM_FORMS': '1000',
        'imagenes-0-id': str(img0.id),
        'imagenes-1-id': str(img1.id),
        'imagenes-2-id': str(img2.id),
        'imagenes-1-DELETE': 'on',
    }
    formset = ProductoImagenFormset(data=data, instance=producto)
    assert formset.is_valid()
    formset.save()
    ordenes = list(producto.imagenes.values_list('orden', flat=True))
    assert ordenes == [0, 1]


@pytest.mark.django_db
def test_formset_ignora_imagen_duplicada(producto):
    ProductoImagenModel.objects.create(producto=producto, imagen='productos/foto.png', orden=0)
    data = formset_data(1)
    files = {'imagenes-0-imagen': _imagen_png('foto.png')}
    formset = ProductoImagenFormset(data=data, files=files, instance=producto)
    assert formset.is_valid()
    formset.save()
    assert producto.imagenes.count() == 1
