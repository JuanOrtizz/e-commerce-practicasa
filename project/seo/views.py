from django.shortcuts import render

from productos.models import CategoriaModel


def robots_txt(request):
    return render(request, 'seo/robots.txt', content_type='text/plain')


def llms_txt(request):
    categorias = CategoriaModel.objects.prefetch_related('subcategorias').all()
    return render(
        request,
        'seo/llms.txt',
        {'categorias': categorias},
        content_type='text/plain',
    )