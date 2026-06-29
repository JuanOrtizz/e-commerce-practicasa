from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'base/index.html')

def cambios_y_devoluciones(request):
    return render(request, 'base/cambios_y_devoluciones.html')

def nuestra_historia(request):
    return render(request, 'base/nuestra_historia.html')

def politicas_de_privacidad(request):
    return render(request, 'base/politicas_de_privacidad.html')

def terminos_y_condiciones(request):
    return render(request, 'base/terminos_y_condiciones.html')

def cambios_y_devoluciones(request):
    return render(request, 'base/cambios_y_devoluciones.html')