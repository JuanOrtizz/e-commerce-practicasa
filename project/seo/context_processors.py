import re

from django.conf import settings


def _telefono_intl(telefono):
    return '+' + re.sub(r'\D', '', telefono)


def seo_info(request):
    base_url = f'{request.scheme}://{request.get_host()}'
    datos_local = getattr(settings, 'DATOS_LOCAL', {})
    telefono = datos_local.get('whatsapp') or '+54 9 3435 46-8162'
    return {
        'canonical_url': f'{base_url}{request.path}',
        'SITE_URL': settings.SITE_URL,
        'SITE_NOMBRE': 'Practicasa',
        'SITE_EMPRESA': (
            'Practicasa, tienda online de artículos para el hogar en Nogoyá, '
            'Entre Ríos. Envíos a todo el país y retiro local.'
        ),
        'SITE_LOGO': f'{base_url}{settings.STATIC_URL}img/logo_practicasa.png',
        'SITE_TELEFONO': telefono,
        'SITE_TELEFONO_INTL': _telefono_intl(telefono),
        'SITE_REDES': {
            'tiktok': 'https://www.tiktok.com/@practicasa.arg',
            'facebook': 'https://www.facebook.com/practicasa.nogoya#',
            'instagram': 'https://www.instagram.com/practicasa.nogoya',
        },
        'es_noindex': getattr(request, 'es_noindex', False),
    }