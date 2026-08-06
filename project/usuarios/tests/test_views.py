import pytest
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse
from usuarios.models import UsuarioModel


@pytest.mark.django_db
def test_registro_get_200(client):
    response = client.get(reverse("registro"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_registro_post_valido(client, form_data):
    response = client.post(reverse("registro"), form_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert data["redirect"] == "/"
    assert UsuarioModel.objects.count() == 1


@pytest.mark.django_db
def test_registro_post_invalido(client, form_data):
    data = {**form_data, "email": "invalido"}
    response = client.post(reverse("registro"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is False
    assert "email" in data["errors"]
    assert UsuarioModel.objects.count() == 0


@pytest.mark.django_db
def test_login_get_200(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_post_valido(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    response = client.post(reverse("login"), {
        "username": user_data["email"],
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert data["redirect"] == "/"


@pytest.mark.django_db
def test_login_post_email_mayuscula(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    response = client.post(reverse("login"), {
        "username": user_data["email"].upper(),
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert data["redirect"] == "/"


@pytest.mark.django_db
def test_login_post_invalido(client):
    response = client.post(reverse("login"), {
        "username": "no@existe.com",
        "password": "wrong",
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is False
    assert "__all__" in data["errors"]


@pytest.mark.django_db
def test_login_admin_tienda_get_200(client):
    response = client.get(reverse("login_admin_tienda"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_admin_tienda_post_rechaza_cliente(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    response = client.post(reverse("login_admin_tienda"), {
        "username": user_data["email"],
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is False


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_password_reset_post_envia_email(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    response = client.post(reverse("password_reset"), {
        "email": user_data["email"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert len(mail.outbox) == 1
    assert "Restablecé tu contraseña" in mail.outbox[0].subject


@pytest.mark.django_db
def test_logout_post_redirect(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    client.login(username=user_data["email"], password=user_data["password"])
    response = client.post(reverse("logout"))
    assert response.status_code == 302
