# Changelog
---
## [v0.14.0] - 2026-08-13
### Rama: feature/panel-admin
#### Features
- Agrego módulo de administración de la tienda (app panel_admin): base.html con sidebar responsive (offcanvas en móviles), header con logout y gestión de productos (lista, detalle, creación, modificación y eliminación), consultas, referencias y pagos
- Agrego formulario de productos con imágenes en el panel (carga múltiple de imágenes, colores, medidas y tags) y sus tests
- Agrego columna Precio Transferencia en la tabla de productos del panel
- Agrego logout de panel-admin
- Agrego campo estado al modelo Consulta (pendiente/resuelta)
- Agrego consultas al panel admin: listado con filtro por estado y orden por fecha, detalle, modificación y eliminación con confirmación, con tests
- Agrego sección de referencias al panel admin (colores, medidas, categorías y subcategorías) con listados y formularios, con tests
- Agrego filtros y ordenamiento en tiempo real a las listas del panel admin (búsqueda por nombre, filtro por stock/estado/promoción y orden A-Z/Z-A)
- Agrego filtro "Con promoción" y badge de promoción en la lista de productos del panel
- Rediseño el dashboard del panel admin: KPIs (productos activos, stock bajo, consultas y placeholder de ventas), gráficos Chart.js (consultas por estado, productos por categoría y tags, promociones activas), tabla de productos con menos stock y sparklines
- Agrego scroll al primer error en los formularios de producto del panel
- Agrego alerta de éxito con redirección al cerrar
- Formateo de precios en tienda y panel: separador de miles con punto y decimal con coma (1.234.567,89) en lista y detalle de productos, carrito (incluidas las actualizaciones AJAX) y tabla/detalle del panel
- Agrego test de regresión: el tag nuevo persiste al editar un producto
#### Fixes
- Elimino del carrito los productos desactivados por el admin
- Ajusto el carrito al stock real: limito la cantidad al stock disponible por variante y elimino los items sin stock
- Elimino automáticamente las promociones 2x1/3x2 cuando el stock no alcanza para aplicarlas y notifico al admin al asignarlas sin stock suficiente
- Hago el login del panel silencioso: solo usuarios admin y sin flujo de recuperación de contraseña
- Re-habilito el botón de eliminar tras un error de red en el panel admin
- Evito desbordes por nombres largos en la card del carrito, en detalle/lista/breadcrumb de productos y del path del archivo en el formulario (FileInput)
- Corrijo bugs de selector en los estilos de formularios globales
- Corrijo el desacople visual del ícono del menú hamburguesa en celulares
- Corrijo el desborde horizontal de las tablas del panel en pantallas chicas: scroll interno en el eje X (min-width: 0 en el layout)
#### Style
- Ajusto el diseño del logout de panel admin
#### Refactor
- Organizo el código de views del panel y lo divido en decorators y services
- Elimino redirect innecesario en producto_eliminar
- Elimino 3 tests redundantes en carrito y productos: test duplicado de la señal del carrito, test tautológico del related_name y test de búsqueda sin search sin aporte de cobertura (318 tests)
---
## [v0.11.0] - 2026-08-05
### Rama: feature/carrito-model
#### Features
- Agrego campos precio_final y precio_transferencia_final a ProductoModel
- Actualizo servicios y filtros para usar precio_transferencia_final
- Actualizo vistas y templates para usar precios finales y ordenar productos sin stock al fondo
- Agrego modelos CarritoModel y CarritoItemModel (OneToOne a usuario, snapshot de color/medida, unique_together, cantidad positiva) y migración inicial
- Agrego señal post_save que crea el carrito automáticamente al registrar un usuario
- Agrego services.py del carrito: get_o_crear_carrito_service, agregar_item_service, actualizar_cantidad_service, eliminar_item_service, vaciar_carrito_service, calcular_precios_item_service (2x1, 3x2, % OFF) y get_carrito_context_service
- Agrego views del carrito con respuestas JSON: ver_carrito, agregar_al_carrito, actualizar_cantidad, eliminar_item y vaciar_carrito
- Agrego urls.py de carrito y enrutado en urls del proyecto
- Agrego template carrito.html responsive con resumen, promociones y controles de cantidad
- Agrego estáticos del carrito: carrito.js (fetch con CSRF, spinners, actualización en el lugar) y carrito.css
- Agrego tests con pytest para carrito (57 tests): modelos, señal, servicios y vistas
- Integro carrito en frontend: forms de lista/detalle apuntan a /carrito/agregar/ con color y medida, icono de carrito siempre visible en header, alerta infoLoginAlertRedirect para no autenticados
- Agrego login case-insensitive: get_by_natural_key normaliza email a minúsculas
- Agrego redirect con ?next en login para volver a la página de origen
- Agrego mensaje genérico de email duplicado en registro (evita enumeración de cuentas)
- Agrego superuser solo local con variable CREATE_SUPERUSER en entrypoint.sh
- Agrego validación de cantidad inválida en el carrito (400 sin filtrar errores de Python)
- Agrego SRI (integrity + crossorigin) a los scripts CDN en base.html
- Corrijo XSS en buscador reemplazando innerHTML por textContent
#### Style
- Aumento padding de secciones de páginas legales (p-2 a p-3)
#### Fixes
- Arreglo errores de sintaxis en buscador.js (punto y coma y llave faltante)
- Actualizo tests para usar Decimal y get_or_create en cálculos de precios finales
- Arreglo warnings de GSAP por targets ausentes
- Elimino ruta y vista duplicada cambios_y_devoluciones en app base
- Agrego año dinámico en footer con {% now %} y abro links de redes sociales en nueva pestaña (target=_blank)
- Valido stock global por producto sumando todas las variantes al agregar o actualizar items del carrito
- Muestro stock restante (stock - carrito del usuario) en lista y detalle de productos, con botón deshabilitado cuando no queda
- Bloqueo el botón de aumentar del carrito según el stock disponible por item (stock - otras variantes) y recalculo los botones de todas las variantes al actualizar o eliminar un item
- Actualizo el botón a "Sin stock" en lista y detalle al agregar al carrito sin necesidad de recargar la página
#### Chore
- Limpio .gitattributes para solo manejar archivos .sh
#### Docs
- Agrego docs/manejo-de-stock-futuro.md con diseño a futuro para app ventas (modelo tipo MercadoLibre)
---
## [v0.10.0] - 2026-06-29
### Rama: feature/views-productos
#### Features
- Agrego modelos ProductoModel y ProductoImagenModel con auto-asignación de tags (sin_stock, destacado, oferta, ultima_unidad, nuevo)
- Agrego services.py con get_productos_activos, aplicar_filtros (categoria, color, precio, orden), get_producto_por_slug y get_contexto_filtros
- Agrego vistas de lista con paginación y detalle de producto
- Agrego urls.py con rutas para lista, detalle, filtros por categoría y subcategoría
- Agrego enrutado de urls de productos en urls del proyecto
- Agrego templates lista.html (221 líneas) y detalle.html (114 líneas) con Bootstrap 5
- Agrego estáticos: productos.css (59 líneas), detalle.js, filtros.js, lista.js (44 líneas total), logo_default img
- Agrego migraciones para campo destacado y precio_transferencia
- Agrego tests con pytest (39 tests): 17 modelos, 11 servicios, 10 vistas, 1 context processor
- Agrego 7 tests para vistas de búsqueda (resultados_busqueda y buscar_productos_json)
- Agrego 5 tests para vistas del footer en base (faqs, terminos_y_condiciones, politicas_de_privacidad, cambios_y_devoluciones, nuestra_historia)
- Agrego conftest.py con fixtures reutilizables para categoria, subcategoria, color, medida, tag y producto
- Registro modelos en admin.py
- Agrego constante PRODUCTOS_POR_PAGINA para paginator
- Actualizo enlaces de productos en header.html dinámicamente
- Actualizo número de teléfono de botón flotante WhatsApp
- Agrego funciones successToast y errorToast en alertas.js
- Agrego estilos para form-check con color terciario en globalStyles.css
- Agrego botón agregar al carrito con spinner en listado y detalle de productos
- Agrego visualización de promociones (porcentaje OFF, precio tachado) en listado y detalle
- Agrego script agregarCarritoForm.js para manejo del formulario del carrito
- Agrego vistas de búsqueda: endpoint JSON con top 4 resultados y página de resultados paginada
- Agrego barra de búsqueda con autocompletado: JS debounce 300ms, dropdown con imagen y precio, navegación por teclado
#### Style
- Oculto spiners numéricos en inputs
#### Fixes
- Corrijo fixture subcategoria_data para crear SubcategoriaModel en DB (evita IntegrityError en 26 tests)
- Corrijo producto_data_completa para usar subcategoria_data como FK directo
- Corrijo FakeRequest en test_services.py: uso QueryDict en vez de dict (soporta .getlist())
- Corrijo URLs con namespace 'productos:' inexistente en detalle.html
- Corrijo test de orden inválido usando .update() para sortear auto_now_add
- Corrijo visibilidad de la barra de búsqueda en páginas de productos: reemplazo namespace por nombres de vista
- Corrijo ancho del dropdown de búsqueda en pantallas LG+: envuelvo input-group en contenedor position-relative
- Limpio imports no usados en conftest.py (timedelta, timezone, ProductoImagenModel)
#### Chore
- Reemplazo productos/tests.py por paquete productos/tests/ con __init__.py
--- 

## [v0.9.0] - 2026-06-29
### Rama: feature/legales-e-historia
#### Features
- Creación de páginas Cambios y Devoluciones, Políticas de privacidad, Términos y Condiciones y nuestra historia
- Estilos personalizados para los templates
- Vinculación de enlace en el footer a la vista correspondiente
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
