# Changelog
---
## [v0.8.0] - 2026-06-18
### Rama: feature/faqs-locales
#### Features
- Creación de página de FAQs con acordeón de preguntas organizadas por categorías (Envíos, Pago, Devoluciones)
- Estilos personalizados para el acordeón de FAQs (faqs.css)
- Vinculación del enlace "FAQs" en el footer a la vista correspondiente
---

## [v0.7.0] - 2026-06-18
### Rama: feature/modelos-productos
#### Features
- Agrego modelos para app Productos, migracion y registro de modelos en Admin
- Agrego configuracion de Media en settings y urls del proyecto
- Agrego Pillow para las imagenes
- Agrego .gitattributes para forzar LF en archivos .sh
- Agrego boton flotante de WhatsApp
- Agrego boton para scrollear al inicio
- Agrego email en footer
- Agrego context processor para categorias en el menu
- Agrego menu dinamico de categorias, barra de busqueda condicional y bullets en subcategorias
---

## [v0.6.0] - 2026-06-17
### Rama: feature/usuarios
#### Features
- Agrego modelo UsuarioModel con UsuarioManager y save() para normalizar email
- Creo migracion inicial de UsuarioModel
- Registro UsuarioModel en admin.py
- Agrego formularios de autenticacion: RegistroForm, LoginForm, LoginAdminTiendaForm, CustomPasswordResetForm, CustomSetPasswordForm
- Agrego vistas de autenticacion con respuestas JSON para AJAX
- Agrego URLs de autenticacion (/login/, /registro/, /login-admin-tienda/, /logout/, /password-reset/)
- Agrego templates de autenticacion (login, registro, login_admin_tienda, password_reset y derivados)
- Agrego estilos y scripts de autenticacion (auth.css, authForms.js, validacionesAuth.js)
- Agrego templates de email para password reset
- Configuro AUTH_USER_MODEL, LOGIN_* / LOGOUT_* y EmailBackend en settings
- Integro URLs de usuarios en project/urls.py
- Agrego SweetAlert2 global en base.html
- Agrego login/logout con POST en header.html
- Agrego estilos globales .btn-enviar para button y a en globalStyles.css
- Agrego tests con pytest para app usuarios (modelos, formularios, vistas - 38 tests)
- Agrego script create_superuser.py para entrypoint
- Registro ConsultaModel (app base) en admin.py
#### Fixes
- Muevo alertas.js de base/static/base/js/ a static/js/ (ruta compartida)
- Corrijo selector CSRF y limpio estilos en contacto
#### Chore
- Actualizo .env.example y docker-compose.yml
---

## [v0.5.0] - 2026-06-14
### Rama: feature/contacto
#### Features
- Agrego formulario de Consulta
- Agrego modelo Consulta y migraciones
- Agrego estilos de contacto
- Agrego alertas.js (SweetAlert2)
- Agrego envio de formulario, manejo de errores y validaciones de contacto
- Agrego template, view y url para Contacto
- Agrego Test con Pytest para app base (Iniciales)
- Agrego pipeline de CI con GitHub Actions para ejecutar Test y Template de PR
- Agrego django-ratelimit al proyecto
- Agrego configuraciones de email en settings.py
- Agrego template email_consulta
- Agrego variables de ejemplo para email y pgadmin (docker-compose)
- Agrego servicio enviar_email con logs
- Agrego ratelimit de 5 post por minuto y envio de email en view contacto
- Agrego test de ratelimit, servicio enviar_email y actualizo test_flujo_contacto_valido
- Agrego estilos generales de inputs, estilos de footer/header y enlace activo en globalStyles.css
- Modifico animaciones con ScrollTrigger y nuevas transiciones en animaciones.js
- Agrego import de GSAP (ScrollTrigger) y actualizo etiqueta main con estilos Bootstrap
- Agrego enlace activo en enlaces de footer
- Agrego resize de barra de busqueda y enlace activo en header
- Agrego servicio pgAdmin a docker-compose
#### Fixes
- Arreglo bug de urls de apps no utilizadas en urls.py del proyecto
- Actualizo servicio pgadmin en docker-compose.yml
- Arreglo bug de btn-enviar disabled en css y js en Contacto
- Arreglo bug de credenciales email para test en CI
- Arreglo bug de credencial Email_Port para test en CI
#### Style
- Cambio de color spinner de boton disabled en contacto
#### Docs
- Actualizo error de nomenclatura en Changelog.md
---

## [v0.4.0] - 2026-06-11
### Rama: feature/setup-apps
#### Features
- Agregado de aplicaciones: base, usuarios, productos, carrito, ventas
- Configuración de apps en settings.py y enrutado en urls.py general
- Agregado de templates base: base.html, header.html, footer.html
- Agregado de estilos globales (globalStyles.css)
- Agregado de animaciones iniciales (animaciones.js)
- Agregado de imágenes para Header, Footer y favicon
#### Fixes
- Arreglado de paleta de colores y globalStyles.css
---

## [v0.3.0] - 2026-06-09
### Rama: develop
#### Features
- Agregado de conexión a base de datos PostgreSQL
- Actualización de requirements.txt
- Agregado de requirements.txt
- Agregado de variables de entorno de ejemplo (PostgreSQL)
- Agregado de AGENTS.md y skills personales para el proyecto
- Agregado de README.md con instrucciones de instalación y uso
- Agregado de directorio docs/ con DER
#### Fixes
- Arreglo de bug de CMD y actualización de versión de Python en Dockerfile
- Arreglo de bugs en docker-compose

#### Refactor
- Actualización de AGENTS.md
---

## [v0.2.0] - 2026-06-03
### Rama: feature/setup
#### Features
- Agregado de CHANGELOG vacío
- Agregado de docker-compose file
- Agregado de proyecto Django inicializado
- Agregado de Dockerfile para producción
- Agregado de .env.example

#### Docs
- Actualización de .gitignore

#### Refactor
- Actualización de ubicación de Dockerfile
---

## [v0.1.0] - 2026-06-03
### Rama: main
#### Features
- Agregado de README.md
- Agregado de .gitignore
---
