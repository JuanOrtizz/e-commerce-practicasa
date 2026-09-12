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
    numero = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_numero',
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

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '').strip()
        if len(direccion) >= 2 and len(direccion) <= 100:
            if not re.fullmatch(r"^[a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ .\-'º#]+$", direccion, re.IGNORECASE):
                raise forms.ValidationError("La dirección no es válida.")
        else:
            raise forms.ValidationError("Dirección: de 2 a 100 caracteres")
        return direccion

    def clean_numero(self):
        numero = self.cleaned_data.get('numero', '').strip()
        if len(numero) >= 1 and len(numero) <= 6:
            if not re.fullmatch(r'^\d+$', numero):
                raise forms.ValidationError("El número no es válido (solo dígitos).")
        else:
            raise forms.ValidationError("Número: de 1 a 6 dígitos.")
        return numero

    def clean_ciudad(self):
        ciudad = self.cleaned_data.get('ciudad', '').strip()
        if len(ciudad) >= 2 and len(ciudad) <= 100:
            if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', ciudad, re.IGNORECASE):
                raise forms.ValidationError("La ciudad no es válida (solo letras y espacios).")
        else:
            raise forms.ValidationError("Ciudad: de 2 a 100 caracteres")
        return ciudad

    def clean_provincia(self):
        provincia = self.cleaned_data.get('provincia', '').strip()
        if len(provincia) >= 2 and len(provincia) <= 100:
            if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', provincia, re.IGNORECASE):
                raise forms.ValidationError("La provincia no es válida (solo letras y espacios).")
        else:
            raise forms.ValidationError("Provincia: de 2 a 100 caracteres")
        return provincia

    def clean_codigo_postal(self):
        codigo_postal = self.cleaned_data.get('codigo_postal', '').strip()
        if not re.fullmatch(r'^\d{4}$', codigo_postal):
            raise forms.ValidationError("El CP debe tener 4 dígitos.")
        return codigo_postal


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
