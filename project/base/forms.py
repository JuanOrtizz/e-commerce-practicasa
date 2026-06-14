import re
from django import forms
from .models import ConsultaModel

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = ConsultaModel
        fields = ['nombre', 'email', 'telefono', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control border-2 border-white', 'id': 'id_nombre', 'placeholder': ''}),
            'email': forms.EmailInput(attrs={'class': 'form-control border-2 border-white', 'id': 'id_email', 'placeholder': ''}),
            'telefono': forms.TextInput(attrs={'class': 'form-control border-2 border-white', 'id': 'id_telefono','placeholder': ''}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control border-2 border-white', 'id': 'id_mensaje', 'placeholder': '', 'style' : 'resize: none;'}),
        }


    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) >= 2 and len(nombre) <= 100:
            if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', nombre, re.IGNORECASE):
                raise forms.ValidationError("El nombre no es válido (solo letras y espacios).")
        else:
            raise forms.ValidationError("Nombre: de 2 a 100 caracteres")
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

    # Validacion de mensaje
    def clean_mensaje(self):
        mensaje = self.cleaned_data.get('mensaje', '').strip()
        if len(mensaje) < 2 or len(mensaje) > 1000:
            raise forms.ValidationError("Mensaje: de 2 a 1000 caracteres.")
        return mensaje