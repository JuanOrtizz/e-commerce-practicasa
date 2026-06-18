from django.db import models
from django.utils.text import slugify


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

    def _asignar_tags_automaticos(self):
        tags_asignar = set(self.tags.values_list('nombre', flat=True))

        if self.promocion:
            tags_asignar.add(TagModel.TagChoices.OFERTA)
        else:
            tags_asignar.discard(TagModel.TagChoices.OFERTA)

        if self.stock == 0:
            tags_asignar.add(TagModel.TagChoices.SIN_STOCK)
        else:
            tags_asignar.discard(TagModel.TagChoices.SIN_STOCK)

        self.tags.set(
            TagModel.objects.filter(nombre__in=tags_asignar)
        )


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