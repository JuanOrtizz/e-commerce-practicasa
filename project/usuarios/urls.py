from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomRegisterView, CustomLoginView, CustomLoginAdminTiendaView, CustomPasswordResetView, \
    CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

urlpatterns = [
    path("registro/", CustomRegisterView.as_view(), name="registro"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("login-admin-tienda/", CustomLoginAdminTiendaView.as_view(), name="login_admin_tienda"),
    path("logout-admin-tienda/", LogoutView.as_view(next_page="login_admin_tienda"), name="logout_admin_tienda"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
