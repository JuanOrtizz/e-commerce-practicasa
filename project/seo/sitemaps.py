from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from productos.models import CategoriaModel, SubcategoriaModel, ProductoModel

PRIORIDADES_ESTATICAS = {
    'index': '1.0',
    'productos': '0.8',
    'faqs': '0.5',
    'contacto': '0.5',
    'nuestra_historia': '0.5',
    'cambios_y_devoluciones': '0.5',
    'terminos_y_condiciones': '0.3',
    'politicas_de_privacidad': '0.3',
}

FRECUENCIA_ESTATICAS = {
    'index': 'weekly',
    'productos': 'daily',
    'faqs': 'monthly',
    'contacto': 'yearly',
    'nuestra_historia': 'yearly',
    'cambios_y_devoluciones': 'monthly',
    'terminos_y_condiciones': 'yearly',
    'politicas_de_privacidad': 'yearly',
}


class StaticViewSitemap(Sitemap):
    def items(self):
        return list(PRIORIDADES_ESTATICAS.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return PRIORIDADES_ESTATICAS[item]

    def changefreq(self, item):
        return FRECUENCIA_ESTATICAS[item]


class CategoriaSitemap(Sitemap):
    changefreq = 'daily'
    priority = '0.8'

    def items(self):
        return CategoriaModel.objects.all()

    def location(self, obj):
        return reverse('productos_por_categoria', args=[obj.slug])


class SubcategoriaSitemap(Sitemap):
    changefreq = 'daily'
    priority = '0.8'

    def items(self):
        return SubcategoriaModel.objects.select_related('categoria').all()

    def location(self, obj):
        return reverse(
            'productos_por_subcategoria',
            args=[obj.categoria.slug, obj.slug],
        )


class ProductoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = '0.8'
    lastmod = 'updated_at'

    def items(self):
        return (
            ProductoModel.objects.filter(activo=True)
            .select_related('subcategoria__categoria')
        )

    def location(self, obj):
        return reverse(
            'detalle_producto',
            args=[
                obj.subcategoria.categoria.slug,
                obj.subcategoria.slug,
                obj.slug,
            ],
        )