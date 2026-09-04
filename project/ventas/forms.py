import re

from django import forms

from .models import VentaModel


class CheckoutForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'id_email',
            'placeholder': '',
        }),
    )
    nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_nombre',
            'placeholder': '',
        }),
    )
    telefono = forms.CharField(
        max_length=25,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_telefono',
            'placeholder': '',
        }),
    )
    provincia = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_provincia',
            'placeholder': '',
        }),
    )
    ciudad = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_ciudad',
            'placeholder': '',
        }),
    )
    direccion = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_direccion',
            'placeholder': '',
        }),
    )
    codigo_postal = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_codigo_postal',
            'placeholder': '',
        }),
    )
    notas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'id_notas',
            'placeholder': '',
            'rows': '2',
        }),
    )

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) >= 2 and len(nombre) <= 150:
            if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', nombre, re.IGNORECASE):
                raise forms.ValidationError("El nombre no es válido (solo letras y espacios).")
        else:
            raise forms.ValidationError("Nombre: de 2 a 150 caracteres")
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if len(email) >= 6 and len(email) <= 254:
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email, re.IGNORECASE):
                raise forms.ValidationError("El email no es válido.")
        else:
            raise forms.ValidationError("Email: de 6 a 254 caracteres.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if len(telefono) >= 6 and len(telefono) <= 25:
            if not re.fullmatch(r'^\+?[0-9\s-]{6,25}$', telefono):
                raise forms.ValidationError("El teléfono no es válido.")
        else:
            raise forms.ValidationError("Teléfono: de 6 a 25 caracteres.")
        return telefono


class EnvioForm(forms.Form):
    metodo_envio = forms.ChoiceField(
        choices=VentaModel.MetodoEnvioChoices.choices,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input', 'id': 'id_metodo_envio'}),
    )


class VentaAdminForm(forms.ModelForm):
    class Meta:
        model = VentaModel
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'}),
        }
