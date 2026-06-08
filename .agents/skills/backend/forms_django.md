# Forms Django - Reglas para el agente

## Cuándo crear
- Para formularios de ingreso de datos en el dashboard web
- Separar del modelo: usar `forms.Form`, no `ModelForm`

## Reglas

### 1. Estructura base
- Heredar de `forms.Form` (no ModelForm)
- Cada campo se define explícitamente con su tipo y widget
- Campos opcionales: `required=False`

### 2. Widgets con Bootstrap
- Inputs de texto: `widget=forms.TextInput(attrs={'class': 'form-control'})`
- Selects: `widget=Select(attrs={'class': 'form-control'})`
- DateField: `widget=forms.TextInput(attrs={'type': 'date'})`
- TimeField: `widget=forms.TextInput(attrs={'type': 'time'})`
- Readonly: agregar `'readonly': 'readonly'` en attrs
- Campos con múltiples clases: `'class': 'form-control otra-clase'`

### 3. ChoiceField
- `choices` como lista de tuplas: `[('valor_db', 'Texto UI'), ...]`
- Incluir opción vacía al inicio: `('', 'Selecciona...')`
- El valor se guarda como string, no como índice

### 4. Validaciones con clean_<campo>()
- Cada campo con validación extra tiene su método `clean_<campo>()`
- Obtener valor: `self.cleaned_data.get('campo', '')`
- Sanitizar con `.strip()`, `.title()`, `.lower()` según el campo
- Lanzar error: `raise forms.ValidationError("Mensaje de error")`
- El método debe retornar el valor limpio
- Regex: `re.fullmatch(r'^patron$', valor)` para validación de formato

### 5. Para formularios basados en UserCreationForm (registro)
- Heredar de `UserCreationForm`
- `Meta.model = User`, `Meta.fields = ('username', 'email', 'password1', 'password2')`
- Validar email en `clean_email()` contra whitelist

## Ejemplo genérico

```python
from django import forms
from django.forms import Select

class EntidadForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        max_length=100
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Selecciona...'), ('tipo1', 'Tipo 1'), ('tipo2', 'Tipo 2')],
        widget=Select(attrs={'class': 'form-control'}),
    )
    fecha = forms.DateField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    hora = forms.TimeField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    telefono = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=25
    )

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2:
            raise forms.ValidationError("Mínimo 2 caracteres")
        if not re.fullmatch(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ]+(?:\s[a-zA-ZáéíóúñÁÉÍÓÚÑ]+)*$', nombre):
            raise forms.ValidationError("Solo letras y espacios")
        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not re.fullmatch(r'^\+?[0-9\s-]{6,25}$', telefono):
            raise forms.ValidationError("Teléfono inválido")
        return telefono
```
