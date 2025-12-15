from django import forms
from .models import Producto, Venta


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'descripcion',
            'precio',
            'imagen',         # Imagen principal
            'imagen_1',       # Imagen adicional 1
            'imagen_2',       # Imagen adicional 2
            'imagen_3',       # Imagen adicional 3
            'imagen_4',       # Imagen adicional 4
            'imagen_5',       # Imagen adicional 5
            'destacado',
            'categoria'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'select'}),
        }


from django import forms
from .models import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = '__all__'
        widgets = {
            'fecha_venta': forms.DateInput(attrs={'type': 'date'}),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),  # ✅ NUEVO
        }


from django import forms
from .models import DatosContacto

class DatosContactoForm(forms.ModelForm):
    class Meta:
        model = DatosContacto
        fields = ['nombre', 'direccion', 'correo_electronico', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'direccion': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dirección de envío'}),
            'correo_electronico': forms.EmailInput(attrs={'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono'}),
        }

