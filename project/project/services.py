import logging
from email.message import MIMEPart
from functools import lru_cache
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.templatetags.static import static

logger = logging.getLogger(__name__)

LOGO_EMAIL_CID = 'logo-practicasa'


@lru_cache(maxsize=1)
def _logo_email_bytes():
    ruta = finders.find('img/logo_practicasa.png')
    if not ruta:
        return None
    with open(ruta, 'rb') as archivo:
        return archivo.read()


def get_email_logo_url():
    return urljoin(settings.SITE_URL, static('img/logo_practicasa.png'))


def enviar_email(asunto, mensaje_texto, mensaje_html, destinatarios):
    try:
        mensaje = EmailMultiAlternatives(
            subject=asunto,
            body=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        mensaje.attach_alternative(mensaje_html, 'text/html')

        logo = _logo_email_bytes()
        if logo:
            imagen = MIMEPart()
            imagen.set_content(
                logo,
                maintype='image',
                subtype='png',
                disposition='inline',
                filename='logo_practicasa.png',
                cid=f'<{LOGO_EMAIL_CID}>',
            )
            mensaje.attach(imagen)

        mensaje.send()
        return True
    except Exception:
        logger.exception("Error enviando email a %s", destinatarios)
        return False
