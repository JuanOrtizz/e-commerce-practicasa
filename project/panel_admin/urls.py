from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='panel_inicio'),
    path('productos/', views.lista_productos, name='panel_productos'),
    path('productos/nuevo/', views.producto_nuevo, name='panel_producto_nuevo'),
    path('productos/modificar/<int:id>/', views.producto_modificar, name='panel_producto_modificar'),
    path('productos/eliminar/<int:id>/', views.producto_eliminar, name='panel_producto_eliminar'),
    path('productos/<int:id>/', views.producto_detalle, name='panel_producto_detalle'),
    path('consultas/', views.lista_consultas, name='panel_consultas'),
    path('consultas/modificar/<int:id>/', views.consulta_modificar, name='panel_consulta_modificar'),
    path('consultas/eliminar/<int:id>/', views.consulta_eliminar, name='panel_consulta_eliminar'),
    path('consultas/<int:id>/', views.consulta_detalle, name='panel_consulta_detalle'),
    path('pagos/', views.pagos, name='panel_pagos'),
    path('referencias/', views.referencias, name='panel_referencias'),
    path('colores/nuevo/', views.color_nuevo, name='panel_color_nuevo'),
    path('colores/eliminar/<int:id>/', views.color_eliminar, name='panel_color_eliminar'),
    path('medidas/nuevo/', views.medida_nuevo, name='panel_medida_nuevo'),
    path('medidas/eliminar/<int:id>/', views.medida_eliminar, name='panel_medida_eliminar'),
    path('categorias/nuevo/', views.categoria_nuevo, name='panel_categoria_nuevo'),
    path('categorias/eliminar/<int:id>/', views.categoria_eliminar, name='panel_categoria_eliminar'),
    path('subcategorias/nuevo/', views.subcategoria_nuevo, name='panel_subcategoria_nuevo'),
    path('subcategorias/eliminar/<int:id>/', views.subcategoria_eliminar, name='panel_subcategoria_eliminar'),
]
