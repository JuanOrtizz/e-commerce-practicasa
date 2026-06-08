# Autenticación Django - Reglas para el agente

## Cuándo crear
- Para sistema de login/registro web (Django Auth)
- Para sistema dual: web (sesiones) + API (JWT)

## Reglas

### 1. Sistema Dual
- **Web**: Django Auth con sesiones
- **API**: JWT con tokens Bearer
- Ambos coexisten sin interferencia

### 2. Configuración en settings.py
```python
LOGIN_URL = '/app/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/app/login/'
```

### 3. Vistas de autenticación web
- Login: `LoginView.as_view(template_name='app/login.html')`
- Logout: `LogoutView.as_view()`
- Registro: CBV `CreateView` con formulario personalizado

### 4. Protección de vistas
- Decorador: `@login_required` en todas las vistas del dashboard
- Importar: `from django.contrib.auth.decorators import login_required`

### 5. Formulario de registro
- Heredar de `UserCreationForm`
- Validar email en `clean_email()` (whitelist o validación personalizada)
- `success_url = reverse_lazy('login')`

### 6. Templates de autenticación
- `login.html`: Form POST con username/password, mostrar `form.errors`
- `registro.html`: Iterar `{% for field in form %}`, mostrar `field.label`, `field`, `field.errors`
- Actions con `{% url 'login' %}` y `{% url 'registro' %}`

## Ejemplo genérico

```python
# settings.py
LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/cuentas/login/'

# app/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import RegistroForm

class SignUpView(CreateView):
    form_class = RegistroForm
    template_name = 'app/registro.html'
    success_url = reverse_lazy('login')

# app/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import SignUpView

urlpatterns = [
    path('login/', LoginView.as_view(template_name='app/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', SignUpView.as_view(), name='registro'),
]
```
