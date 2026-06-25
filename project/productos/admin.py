from django.contrib import admin
from .models import (
    CategoriaModel, SubcategoriaModel, ColorModel, MedidaModel,
    TagModel, ProductoModel, ProductoImagenModel
)


@admin.register(CategoriaModel)
class CategoriaModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'slug']
    search_fields = ['nombre']
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(SubcategoriaModel)
class SubcategoriaModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'categoria', 'slug']
    search_fields = ['nombre']
    list_filter = ['categoria']
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(ColorModel)
class ColorModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'codigo_hex']
    search_fields = ['nombre']


@admin.register(MedidaModel)
class MedidaModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    search_fields = ['nombre']


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagenModel
    extra = 1


@admin.register(ProductoModel)
class ProductoModelAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'nombre', 'sku', 'precio', 'stock',
        'subcategoria', 'promocion', 'destacado', 'activo'
    ]
    list_filter = ['activo', 'subcategoria', 'promocion', 'destacado', 'tags']
    search_fields = ['nombre', 'sku', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ProductoImagenInline]
    filter_horizontal = ['colores', 'medidas']
    readonly_fields = ('tags',)