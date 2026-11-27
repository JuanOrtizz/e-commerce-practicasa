import pytest
from django.core import mail
from django.test.utils import override_settings
from project.services import LOGO_EMAIL_CID, enviar_email, get_email_logo_url


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_enviar_email_exitoso():
    result = enviar_email(
        asunto='Test',
        mensaje_texto='Texto plano',
        mensaje_html='<p>HTML</p>',
        destinatarios=['test@example.com'],
    )
    assert result is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == 'Test'
    assert mail.outbox[0].to == ['test@example.com']


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_enviar_email_multiples_destinatarios():
    result = enviar_email('Test', 'Texto', '<p>HTML</p>', ['a@x.com', 'b@x.com'])
    assert result is True
    assert len(mail.outbox) == 1
    assert len(mail.outbox[0].to) == 2


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_enviar_email_incluye_html():
    result = enviar_email('Test', 'Texto', '<p>HTML</p>', ['test@example.com'])
    assert result is True
    assert mail.outbox[0].message().is_multipart()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_enviar_email_incluye_logo_inline():
    result = enviar_email('Test', 'Texto', '<p>HTML</p>', ['test@example.com'])
    assert result is True
    imagenes = [
        parte for parte in mail.outbox[0].message().walk()
        if parte.get_content_type() == 'image/png'
    ]
    assert len(imagenes) == 1
    assert imagenes[0].get('Content-ID') == f'<{LOGO_EMAIL_CID}>'


@override_settings(SITE_URL='https://practicasashop.com.ar')
def test_get_email_logo_url_usa_site_url():
    assert get_email_logo_url() == (
        'https://practicasashop.com.ar/static/img/logo_practicasa.png'
    )
