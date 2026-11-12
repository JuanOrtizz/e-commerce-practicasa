from django import forms


class PasswordToggleInput(forms.PasswordInput):
    template_name = 'usuarios/widgets/password_toggle.html'
