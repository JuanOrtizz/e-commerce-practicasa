from decimal import Decimal
from datetime import timedelta
import os
from django.db import models
from django.utils.text import slugify
from django.utils import timezone

class CategoriaModel(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class SubcategoriaModel(models.Model):
    categoria = models.ForeignKey(
        CategoriaModel, on_delete=models.CASCADE, related_name='subcategorias'
    )
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = 'subcategorias'
        verbose_name = 'Subcategoría'
        verbose_name_plural = 'Subcategorías'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.categoria.nombre})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class ColorModel(models.Model):
    nombre = models.CharField(max_length=50)
    codigo_hex = models.CharField(max_length=7, help_text='Ej: #FF0000')

    class Meta:
        db_table = 'colores'
        verbose_name = 'Color'
        verbose_name_plural = 'Colores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MedidaModel(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'medidas'
        verbose_name = 'Medida'
        verbose_name_plural = 'Medidas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TagModel(models.Model):
    class TagChoices(models.TextChoices):
        ULTIMA_UNIDAD = 'ultima_unidad', 'Última unidad'
        NUEVO = 'nuevo', 'Nuevo'
        OFERTA = 'oferta', 'Oferta'
        SIN_STOCK = 'sin_stock', 'Sin Stock'
        DESTACADO = 'destacado', 'Destacado'

    nombre = models.CharField(
        max_length=30, choices=TagChoices.choices, unique=True
    )

    class Meta:
        db_table = 'tags'
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'

    def __str__(self):
        return self.get_nombre_display()


class ProductoModel(models.Model):
    class PromocionChoices(models.TextChoices):
        DOS_POR_UNO = '2x1', '2x1'
        TRES_POR_DOS = '3x2', '3x2'
        CINCO = '5%', '5%'
        DIEZ = '10%', '10%'
        VEINTE = '20%', '20%'
        VEINTICINCO = '25%', '25%'
        TREINTA = '30%', '30%'

    subcategoria = models.ForeignKey(
        SubcategoriaModel, on_delete=models.CASCADE, related_name='productos'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    slug = models.SlugField(unique=True)
    sku = models.CharField(max_length=50, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_transferencia = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Precio con descuento por transferencia bancaria'
    )
    stock = models.IntegerField()
    peso = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Peso en kg'
    )
    colores = models.ManyToManyField(ColorModel, blank=True)
    medidas = models.ManyToManyField(MedidaModel, blank=True)
    promocion = models.CharField(
        max_length=5, choices=PromocionChoices.choices,
        null=True, blank=True
    )
    tags = models.ManyToManyField(TagModel, blank=True)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
        self._asignar_tags_automaticos()

    def _asignar_tags_automaticos(self):
        tags = set()

        if self.stock == 0:
            tags.add(TagModel.TagChoices.SIN_STOCK)
        else:
            if self.destacado:
                tags.add(TagModel.TagChoices.DESTACADO)

            if self.stock == 1:
                tags.add(TagModel.TagChoices.ULTIMA_UNIDAD)

            if self.promocion:
                tags.add(TagModel.TagChoices.OFERTA)

            if self.created_at and self.created_at >= timezone.now() - timedelta(days=30):
                tags.add(TagModel.TagChoices.NUEVO)

        self.tags.set(TagModel.objects.filter(nombre__in=tags))

    @property
    def primera_imagen_valida(self):
        primera = self.imagenes.first()
        if primera and primera.imagen and os.path.exists(primera.imagen.path):
            return primera
        return None

    @property
    def tiene_promocion_porcentaje(self):
        return self.promocion in ('5%', '10%', '20%', '25%', '30%')

    @property
    def porcentaje_descuento(self):
        return Decimal(self.promocion.replace('%', '')) if self.tiene_promocion_porcentaje else Decimal('0')

    @property
    def precio_con_promocion(self):
        if self.tiene_promocion_porcentaje and self.precio:
            return (self.precio * (Decimal('100') - self.porcentaje_descuento) / Decimal('100')).quantize(Decimal('0.01'))
        return self.precio

    @property
    def precio_transferencia_con_promocion(self):
        if self.tiene_promocion_porcentaje and self.precio_transferencia:
            return (self.precio_transferencia * (Decimal('100') - self.porcentaje_descuento) / Decimal('100')).quantize(Decimal('0.01'))
        return self.precio_transferencia


class ProductoImagenModel(models.Model):
    producto = models.ForeignKey(
        ProductoModel, on_delete=models.CASCADE, related_name='imagenes'
    )
    imagen = models.ImageField(upload_to='productos/')
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = 'productos_imagenes'
        verbose_name = 'Imagen del producto'
        verbose_name_plural = 'Imágenes del producto'
        ordering = ['orden']

    def __str__(self):
        return f'{self.producto.nombre} - Imagen {self.orden}'