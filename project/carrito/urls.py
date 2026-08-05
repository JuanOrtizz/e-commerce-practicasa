from django.urls import path
from . import views

urlpatterns = [
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/', views.agregar_al_carrito, name='agregar'),
    path('actualizar/', views.actualizar_cantidad, name='actualizar'),
    path('eliminar/', views.eliminar_item, name='eliminar'),
    path('vaciar/', views.vaciar_carrito, name='vaciar'),
]
