from django.http import JsonResponse
from django.shortcuts import render

from .forms import ConsultaForm


# Create your views here.
def index(request):
    return render(request, 'base/index.html')

#View Contacto
def contacto(request):
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Recibimos tu consulta, nos pondremos en contacto con vos lo mas rápido posible."})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = ConsultaForm()

    return render(request, 'base/contacto.html', {'form': form})