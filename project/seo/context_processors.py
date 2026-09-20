from django.conf import settings


def seo_info(request):
    base_url = f'{request.scheme}://{request.get_host()}'
    return {
        'canonical_url': f'{base_url}{request.path}',
        'SITE_URL': settings.SITE_URL,
        'SITE_NOMBRE': 'Practicasa',
        'SITE_EMPRESA': (
            'Tienda online de artículos para el hogar con envíos a todo el país '
            'y retiro local en Nogoyá, Entre Ríos.'
        ),
        'SITE_LOGO': f'{base_url}{settings.STATIC_URL}img/logo_practicasa.png',
        'SITE_TELEFONO': '+54 3543 468162',
        'SITE_TELEFONO_INTL': '+54-3543-468162',
        'SITE_REDES': {
            'tiktok': 'https://www.tiktok.com/@practicasa.arg',
            'facebook': 'https://www.facebook.com/practicasa.nogoya#',
            'instagram': 'https://www.instagram.com/practicasa.nogoya',
        },
    }