from django.urls import path

from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('envio/', views.envio, name='envio'),
    path('confirmacion/', views.confirmacion, name='confirmacion'),
    path('pago-local/<int:venta_id>/', views.pago_local, name='pago_local'),
    path('pago/<int:venta_id>/', views.pago, name='pago'),
]
