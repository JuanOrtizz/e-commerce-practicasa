from django.urls import path
from . import views

urlpatterns = [
    path('', views.productos, name='productos'),
    path('<slug:categoria_slug>/', views.productos_por_categoria, name='productos_por_categoria'),
    path('<slug:categoria_slug>/<slug:subcategoria_slug>/', views.productos_por_subcategoria, name='productos_por_subcategoria'),
    path('<slug:categoria_slug>/<slug:subcategoria_slug>/<slug:slug>/', views.detalle_producto, name='detalle_producto'),
]
