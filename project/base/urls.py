from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('faqs/', views.faqs, name='faqs'),
    path('contacto/', views.contacto, name='contacto')
]