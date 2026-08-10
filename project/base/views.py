from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from .forms import ConsultaForm
from project.services import enviar_email
from .services import obtener_productos_destacados, obtener_productos_en_oferta, obtener_productos_ultima_unidad


# Create your views here.
def index(request):
    destacados = obtener_productos_destacados()
    oferta = obtener_productos_en_oferta()
    ultima_unidad = obtener_productos_ultima_unidad()
    return render(request, 'base/index.html', {
        'destacados': destacados,
        'oferta': oferta,
        'ultima_unidad': ultima_unidad,
    })

def cambios_y_devoluciones(request):
    return render(request, 'base/cambios_y_devoluciones.html')

def nuestra_historia(request):
    return render(request, 'base/nuestra_historia.html')

def politicas_de_privacidad(request):
    return render(request, 'base/politicas_de_privacidad.html')

def terminos_y_condiciones(request):
    return render(request, 'base/terminos_y_condiciones.html')
  
# View para FAQs
def faqs(request):
    return render(request, 'base/faqs.html')

#View Contacto
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def contacto(request):
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save()
            context = {
                'nombre': consulta.nombre,
                'email': consulta.email,
                'asunto': 'Consulta en la web | Practicasa',
                'mensaje': consulta.mensaje,
                'fecha': timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M'),
                'logo_url': request.build_absolute_uri('/static/img/logo_practicasa.png'),
            }
            html = render_to_string('email/email_consulta.html', context)
            enviar_email(
                asunto=context['asunto'],
                mensaje_texto=f"Consulta de {consulta.nombre} ({consulta.email}): {consulta.mensaje}",
                mensaje_html=html,
                destinatarios=[consulta.email],
            )
            return JsonResponse({"success": True, "message": "Recibimos tu consulta, nos pondremos en contacto con vos lo mas rápido posible."})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    else:
        form = ConsultaForm()

    return render(request, 'base/contacto.html', {'form': form})
