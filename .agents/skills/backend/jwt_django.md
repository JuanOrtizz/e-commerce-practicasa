# JWT Django - Reglas para el agente

## Cuándo usar
- Para autenticación de API REST con tokens
- Cuando se necesita login externo desde apps/clientes

## Reglas

### 1. Configuración en settings.py
```python
SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```
- Agregar apps: `'rest_framework_simplejwt'`, `'rest_framework_simplejwt.token_blacklist'`

### 2. Endpoints JWT con Throttle
- Heredar de `TokenObtainPairView` / `TokenRefreshView`
- `throttle_schema = None` en obtain para que drf-spectacular no genere schema de throttle
- Decorar `post()` con `@extend_schema(summary="...")`

### 3. Autenticación DRF por defecto
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
}
```

### 4. Logout con Blacklist
- En vista: `request.auth.blacklist()` en bloque try/except
- Capturar `AttributeError, TypeError` por si el token no soporta blacklist

## Ejemplo genérico

```python
# api/v1/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema

class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_schema = None

    @extend_schema(summary="Obtener token JWT")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ThrottledTokenRefreshView(TokenRefreshView):
    @extend_schema(summary="Refrescar token JWT")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

urlpatterns = [
    path('token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
]
```
