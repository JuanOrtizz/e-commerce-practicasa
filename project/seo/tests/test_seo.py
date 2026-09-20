import pytest


@pytest.mark.django_db
def test_robots_txt(client):
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')
    assert 'Sitemap:' in response.content.decode()


@pytest.mark.django_db
def test_llms_txt(client):
    response = client.get('/llms.txt')
    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')
    assert 'Practicasa' in response.content.decode()


@pytest.mark.django_db
def test_sitemap_xml(client):
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert '<urlset' in response.content.decode()


@pytest.mark.django_db
def test_paginas_publicas_sin_noindex(client):
    for url in ['/', '/faqs/', '/contacto/']:
        response = client.get(url)
        assert response.status_code == 200
        assert 'X-Robots-Tag' not in response


@pytest.mark.django_db
def test_paginas_internas_con_noindex(client):
    for url in ['/carrito/', '/usuarios/login/', '/productos/search/']:
        response = client.get(url)
        assert response['X-Robots-Tag'] == 'noindex'


@pytest.mark.django_db
def test_home_json_ld_store(client):
    response = client.get('/')
    content = response.content.decode()
    assert '"@type": "Store"' in content
    assert 'https://schema.org' in content