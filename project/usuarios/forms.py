import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm, PasswordResetForm
from .models import UsuarioModel
from .services import es_administrador


class RegistroForm(UserCreationForm):
    class Meta:
        model = UsuarioModel
        fields = ["email", "nombre_completo"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
            "nombre_completo": forms.TextInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
        }

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )

    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get("nombre_completo", "").strip()
        if 2 <= len(nombre) <= 150:
            if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', nombre, re.IGNORECASE):
                raise forms.ValidationError("El nombre no es válido (solo letras y espacios).")
        else:
            raise forms.ValidationError("Nombre: de 2 a 150 caracteres")
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if 6 <= len(email) <= 254:
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email, re.IGNORECASE):
                raise forms.ValidationError("El email no es válido.")
        else:
            raise forms.ValidationError("Email: de 6 a 254 caracteres.")
        if UsuarioModel.objects.filter(email=email).exists():
            raise forms.ValidationError("No se pudo crear la cuenta. Verificá los datos e intentá nuevamente.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )


class LoginAdminTiendaForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )

    def confirm_login_allowed(self, user):
        if not es_administrador(user):
            raise self.get_invalid_login_error()

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )
    new_password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control border-2 border-white", "placeholder": ""}),
    )