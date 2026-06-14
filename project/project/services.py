import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

def enviar_email(asunto, mensaje_texto, mensaje_html, destinatarios):
    try:
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            html_message=mensaje_html,
        )
        return True
    except Exception:
        logger.exception("Error enviando email a %s", destinatarios)
        return False