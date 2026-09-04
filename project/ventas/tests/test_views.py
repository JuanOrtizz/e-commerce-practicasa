import pytest

from ventas.models import VentaModel


@pytest.fixture
def client_logueado(client, usuario, item):
    client.force_login(usuario)
    return client


def test_checkout_requiere_login(client):
    response = client.get('/ventas/checkout/')
    assert response.status_code == 302
    assert '/usuarios/login/' in response.headers.get('Location', '')


def test_checkout_get(client_logueado):
    response = client_logueado.get('/ventas/checkout/')
    assert response.status_code == 200
    assert b'Datos de facturaci' in response.content


def test_checkout_carrito_vacio_redirige(client_logueado, carrito):
    response = client_logueado.get('/ventas/checkout/')
    assert response.status_code == 200


def test_checkout_post_valido_redirige_envio(client_logueado, datos_checkout):
    response = client_logueado.post('/ventas/checkout/', datos_checkout)
    assert response.status_code == 302
    assert response.url == '/ventas/envio/'


def test_checkout_post_invalido_muestra_errores(client_logueado):
    response = client_logueado.post('/ventas/checkout/', {
        'nombre': 'X',
        'email': 'mal',
        'telefono': '123',
    })
    assert response.status_code == 200


def test_envio_requiere_datos_previos(client_logueado):
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 302
    assert response.url == '/ventas/checkout/'


def _set_session_datos(client, **kwargs):
    session = client.session
    session['datos_venta'] = {
        'nombre': 'Cliente Test',
        'email': 'cliente@example.com',
        'telefono': '3434567890',
        'direccion': 'Calle 1 123',
        'ciudad': 'Nogoyá',
        'provincia': 'Entre Ríos',
        'codigo_postal': '3150',
        'notas': '',
    }
    session['datos_venta'].update(kwargs)
    session.save()


def test_envio_get_muestra_retiro_y_sucursal_deshabilitada(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'Retiro en el local' in response.content
    assert b'Retiro desde sucursal' in response.content


def test_envio_get_envio_domicilio_con_cp_3150(client_logueado):
    _set_session_datos(client_logueado, codigo_postal='3150', metodo_envio='envio_domicilio')
    response = client_logueado.get('/ventas/envio/')
    assert response.status_code == 200
    assert b'Env' in response.content and b'domicilio' in response.content


def test_confirmacion_get_retiro_local_muestra_efectivo(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='retiro_local')
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 200
    assert b'Efectivo (local)' in response.content
    assert b'Forma de pago' in response.content


def test_confirmacion_get_domicilio_no_muestra_efectivo(client_logueado):
    _set_session_datos(client_logueado, metodo_envio='envio_domicilio')
    response = client_logueado.get('/ventas/confirmacion/')
    assert response.status_code == 200
    assert b'Efectivo (local)' not in response.content
    assert b'Mercado Pago' in response.content


def test_flujo_completo_efectivo(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    response = client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    assert response.status_code == 302
    assert response.url == '/ventas/confirmacion/'

    response = client_logueado.post('/ventas/confirmacion/', {'metodo_pago': 'efectivo'})
    assert response.status_code == 302
    assert response.url.startswith('/ventas/pago-local/')

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'efectivo'
    assert venta.estado == VentaModel.EstadoChoices.PENDIENTE


def test_flujo_completo_mercado_pago(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'envio_domicilio'})
    response = client_logueado.post('/ventas/confirmacion/', {'metodo_pago': 'mercado_pago'})
    assert response.status_code == 302
    assert response.url.startswith('/ventas/pago/')

    venta = VentaModel.objects.get()
    assert venta.metodo_pago == 'mercado_pago'


def test_confirmacion_sin_metodo_pago_muestra_error(client_logueado, datos_checkout):
    client_logueado.post('/ventas/checkout/', datos_checkout)
    client_logueado.post('/ventas/envio/', {'metodo_envio': 'retiro_local'})
    response = client_logueado.post('/ventas/confirmacion/', {})
    assert response.status_code == 200
    assert b'forma de pago' in response.content
    assert VentaModel.objects.count() == 0


def test_pago_local_muestra_datos(client_logueado, usuario, datos_checkout):
    from ventas.services import crear_venta_confirmada_service
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'efectivo'
    )
    response = client_logueado.get(f'/ventas/pago-local/{venta.id}/')
    assert response.status_code == 200
    assert b'efectivo' in response.content
    assert b'ventas-resumen-mapa-wrap' in response.content


def test_pago_placeholder(client_logueado, usuario, datos_checkout):
    from ventas.services import crear_venta_confirmada_service
    venta = crear_venta_confirmada_service(
        usuario, datos_checkout, 'retiro_local', 'mercado_pago'
    )
    response = client_logueado.get(f'/ventas/pago/{venta.id}/')
    assert response.status_code == 200
    assert b'Mercado Pago' in response.content
