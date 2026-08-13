import os
import re
from django import forms
from django.core.validators import MaxLengthValidator
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import (
    CategoriaModel,
    ColorModel,
    MedidaModel,
    ProductoModel,
    ProductoImagenModel,
    SubcategoriaModel,
)

#Maximo de imágenes permitidas por producto
MAX_IMAGENES_PRODUCTO = 3

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaModel
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2 or len(nombre) > 100:
            raise forms.ValidationError('Nombre: de 2 a 100 caracteres.')
        if CategoriaModel.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre


class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = SubcategoriaModel
        fields = ['categoria', 'nombre']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select', 'placeholder': ''}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }

    def clean_nombre(self):
        categoria = self.cleaned_data.get('categoria')
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2 or len(nombre) > 100:
            raise forms.ValidationError('Nombre: de 2 a 100 caracteres.')
        qs = SubcategoriaModel.objects.filter(nombre__iexact=nombre)
        if categoria:
            qs = qs.filter(categoria=categoria)
        if qs.exists():
            raise forms.ValidationError('Ya existe una subcategoría con ese nombre en esta categoría.')
        return nombre


class ColorForm(forms.ModelForm):
    class Meta:
        model = ColorModel
        fields = ['nombre', 'codigo_hex']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'codigo_hex': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#FF0000'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2 or len(nombre) > 50:
            raise forms.ValidationError('Nombre: de 2 a 50 caracteres.')
        if ColorModel.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe un color con ese nombre.')
        return nombre

    def clean_codigo_hex(self):
        codigo_hex = self.cleaned_data.get('codigo_hex', '').strip().upper()
        if not re.fullmatch(r'#[0-9A-F]{6}', codigo_hex):
            raise forms.ValidationError('Código inválido. Usá el formato #RRGGBB.')
        return codigo_hex


class MedidaForm(forms.ModelForm):
    class Meta:
        model = MedidaModel
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2 or len(nombre) > 50:
            raise forms.ValidationError('Nombre: de 2 a 50 caracteres.')
        if MedidaModel.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe una medida con ese nombre.')
        return nombre


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('nombre', 'sku'):
            self.fields[campo].validators = [
                v for v in self.fields[campo].validators
                if not isinstance(v, MaxLengthValidator)
            ]
            self.fields[campo].max_length = None
        if self.instance.pk:
            self.fields['subcategoria'].disabled = True

    class Meta:
        model = ProductoModel
        fields = [
            'subcategoria', 'nombre', 'descripcion', 'sku',
            'precio', 'precio_transferencia', 'stock', 'peso',
            'colores', 'medidas', 'promocion',
            'destacado', 'activo',
        ]
        widgets = {
            'subcategoria': forms.Select(attrs={'class': 'form-select', 'id': 'id_subcategoria', 'placeholder': ''}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre', 'placeholder': '' }),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,  'id': 'id_descripcion', 'placeholder': ''}),
            'sku': forms.TextInput(attrs={'class': 'form-control',  'id': 'id_sku', 'placeholder': ''}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0',  'id': 'id_precio', 'placeholder': ''}),
            'precio_transferencia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0',  'id': 'id_precio_transferencia', 'placeholder': ''}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0',  'id': 'id_stock', 'placeholder': ''}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0',  'id': 'id_peso', 'placeholder': ''}),
            'colores': forms.CheckboxSelectMultiple(),
            'medidas': forms.CheckboxSelectMultiple(),
            'promocion': forms.Select(attrs={'class': 'form-select',  'id': 'id_promocion', 'placeholder': ''}),
            'destacado': forms.CheckboxInput(attrs={'class': 'form-check-input',  'id': 'id_destacado'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input',  'id': 'id_activo'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2 or len(nombre) > 200:
            raise forms.ValidationError('Nombre: de 2 a 200 caracteres.')
        qs = ProductoModel.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un producto creado con ese nombre.')
        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '').strip()
        if len(descripcion) < 2 or len(descripcion) > 1000:
            raise forms.ValidationError('Descripción: de 2 a 1000 caracteres.')
        return descripcion

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').strip().upper()
        if len(sku) < 2 or len(sku) > 50:
            raise forms.ValidationError('SKU: de 2 a 50 caracteres.')
        qs = ProductoModel.objects.filter(sku=sku)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un producto con este código.')
        return sku

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None:
            if precio <= 0:
                raise forms.ValidationError('El precio debe ser mayor a 0.')
            if precio > 99999999.99:
                raise forms.ValidationError('El precio no puede superar 99999999.99.')
        return precio

    def clean_precio_transferencia(self):
        precio_transferencia = self.cleaned_data.get('precio_transferencia')
        precio = self.cleaned_data.get('precio')
        if precio_transferencia is not None:
            if precio_transferencia <= 0:
                raise forms.ValidationError('El precio de transferencia debe ser mayor a 0.')
            if precio_transferencia > 99999999.99:
                raise forms.ValidationError('El precio de transferencia no puede superar 99999999.99.')
            if precio is not None and precio_transferencia > precio:
                raise forms.ValidationError('El precio de transferencia no puede ser mayor al precio.')
        return precio_transferencia

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            if peso <= 0:
                raise forms.ValidationError('El peso debe ser mayor a 0.')
            if peso > 9999.99:
                raise forms.ValidationError('El peso no puede superar 9999.99 kg.')
        return peso

    def clean(self):
        cleaned_data = super().clean()
        if 'promocion' not in self.changed_data:
            return cleaned_data
        promocion = cleaned_data.get('promocion')
        stock = cleaned_data.get('stock')
        stock_minimo = self.instance.stock_minimo_para_promocion(promocion)
        if stock_minimo is not None and stock is not None and stock < stock_minimo:
            self.add_error(
                'promocion',
                f'La promoción {promocion} requiere al menos {stock_minimo} unidades de stock.',
            )
        return cleaned_data


class ProductoImagenForm(forms.ModelForm):
    class Meta:
        model = ProductoImagenModel
        fields = ['imagen']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagen'].required = False


class ProductoImagenFormsetBase(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        if extra is not None:
            self.extra = extra
        super().__init__(*args, **kwargs)

    def _imagenes_duplicadas(self):
        nombres = set()
        if self.instance.pk:
            nombres = {
                os.path.basename(ruta)
                for ruta in self.instance.imagenes.values_list('imagen', flat=True)
            }
        duplicadas = set()
        for form in self.forms:
            if form.instance.pk or not form.cleaned_data:
                continue
            imagen = form.cleaned_data.get('imagen')
            if not imagen:
                continue
            nombre = os.path.basename(imagen.name)
            if nombre in nombres:
                duplicadas.add(form)
            else:
                nombres.add(nombre)
        return duplicadas

    def save(self, commit=True):
        duplicadas = self._imagenes_duplicadas()
        for form in duplicadas:
            self.forms.remove(form)
        indice = 0
        reordenadas = []
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue
            form.instance.orden = indice
            if form.instance.pk:
                reordenadas.append(form.instance)
            indice += 1
        resultado = super().save(commit=commit)
        if commit and reordenadas:
            ProductoImagenModel.objects.bulk_update(reordenadas, ['orden'])
        return resultado


ProductoImagenFormset = inlineformset_factory(
    ProductoModel,
    ProductoImagenModel,
    form=ProductoImagenForm,
    formset=ProductoImagenFormsetBase,
    extra=MAX_IMAGENES_PRODUCTO,
    max_num=MAX_IMAGENES_PRODUCTO,
    can_delete=True,
)
