import pytest
from django.core import mail
from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse
from usuarios.models import UsuarioModel


@pytest.fixture
def limpiar_ratelimit():
    cache.clear()
    yield
    cache.clear()


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
def test_login_admin_tienda_post_exitoso_redirige_panel(client, user_data):
    UsuarioModel.objects.create_user(
        **user_data, tipo=UsuarioModel.Tipos.ADMINISTRADOR_TIENDA
    )
    response = client.post(reverse("login_admin_tienda"), {
        "username": user_data["email"],
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert data["redirect"] == reverse("panel_inicio")


@pytest.mark.django_db
def test_login_admin_tienda_post_rechaza_cliente(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    response = client.post(reverse("login_admin_tienda"), {
        "username": user_data["email"],
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is False
    assert "_auth_user_id" not in client.session
    msj = data["errors"]["__all__"][0]
    assert "administrador" not in msj.lower()


@pytest.mark.django_db
def test_login_admin_tienda_post_superuser_redirige_panel(client, user_data):
    UsuarioModel.objects.create_user(
        **user_data, tipo=UsuarioModel.Tipos.SUPERUSER
    )
    response = client.post(reverse("login_admin_tienda"), {
        "username": user_data["email"],
        "password": user_data["password"],
    }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert data["success"] is True
    assert data["redirect"] == reverse("panel_inicio")


@pytest.mark.django_db
def test_login_admin_tienda_get_cliente_autenticado_redirige_home(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    client.login(username=user_data["email"], password=user_data["password"])
    response = client.get(reverse("login_admin_tienda"))
    assert response.status_code == 302
    assert response.url == "/"


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


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["login", "login_admin_tienda"])
def test_login_bloquea_tras_cinco_intentos(
    client, limpiar_ratelimit, url_name, monkeypatch
):
    monkeypatch.setattr("django_ratelimit.core.time.time", lambda: 1700000000.0)
    datos = {"username": "no@existe.com", "password": "wrong"}
    for _ in range(5):
        client.post(
            reverse(url_name), datos, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
    response = client.post(
        reverse(url_name), datos, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert response.status_code == 429
    assert "Demasiados intentos" in response.json()["errors"]["__all__"][0]


@pytest.mark.django_db
def test_logout_admin_tienda_redirige_login_admin(client, user_data):
    UsuarioModel.objects.create_user(**user_data)
    client.login(username=user_data["email"], password=user_data["password"])
    response = client.post(reverse("logout_admin_tienda"))
    assert response.status_code == 302
    assert response.url == reverse("login_admin_tienda")


@pytest.mark.django_db
def test_login_muestra_toggle_password(client):
    response = client.get(reverse("login"))
    contenido = response.content.decode()
    assert 'data-password-toggle' in contenido
    assert 'aria-controls="id_password"' in contenido
    assert 'autocomplete="current-password"' in contenido


@pytest.mark.django_db
def test_registro_muestra_toggle_en_ambas_passwords(client):
    response = client.get(reverse("registro"))
    contenido = response.content.decode()
    assert contenido.count('data-password-toggle') == 2
    assert 'aria-controls="id_password1"' in contenido
    assert 'aria-controls="id_password2"' in contenido
    assert contenido.count('autocomplete="new-password"') == 2

