import pytest
from django.test import override_settings


@pytest.fixture(autouse=True)
def _configuracion_email_tests():
    with override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-responder@example.com',
        EMAIL_COMERCIO='comercio@example.com',
    ):
        yield
