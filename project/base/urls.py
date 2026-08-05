from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cambios_y_devoluciones/', views.cambios_y_devoluciones, name='cambios_y_devoluciones'),
    path('nuestra_historia/', views.nuestra_historia, name='nuestra_historia'),
    path('politicas_de_privacidad/', views.politicas_de_privacidad, name='politicas_de_privacidad'),
    path('terminos_y_condiciones/', views.terminos_y_condiciones, name='terminos_y_condiciones'),
    path('faqs/', views.faqs, name='faqs'),
    path('contacto/', views.contacto, name='contacto')
]