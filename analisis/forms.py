from django import forms
from .models import Analisis, Autocorrelacion, DeteccionDeOutliers, DescomposicionDeSeriesTemporales
from esios.models import Datos

class DeleteResultsForm(forms.Form):
    titulo = forms.CharField(label="Título", max_length=100)

class AnalisisForm(forms.ModelForm):
    terminos_aceptados = forms.BooleanField(label="Acepto los términos y condiciones", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        tipos_dato_disponibles = Datos.objects.values_list('tipo_dato', flat=True).distinct()
        self.fields['tipos_de_dato'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            choices=[(tipo, tipo) for tipo in tipos_dato_disponibles]
        )

    class Meta:
        model = Analisis
        fields = ['nombre', 'descripcion', 'tipos_de_dato', 'frecuencia', 'terminos_aceptados']

        widgets = {
            'frecuencia': forms.Select(choices=Analisis.FRECUENCIA_CHOICES),
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if Analisis.objects.filter(nombre=nombre).exists():
            raise forms.ValidationError('Ya existe un análisis con este nombre.')
        return nombre

    def clean_tipos_de_dato(self):
        tipos_de_dato = self.cleaned_data['tipos_de_dato']
        if not tipos_de_dato:
            raise forms.ValidationError('Debe seleccionar al menos un tipo de dato.')
        return tipos_de_dato


class AutocorrelacionForm(forms.Form):
    titulo = forms.CharField(
        label="Título",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=50
    )
    lag = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    tipo = forms.ChoiceField(
        choices=Autocorrelacion.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    metodo = forms.ChoiceField(
        choices=Autocorrelacion.METODO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    visualizacion = forms.ChoiceField(
        choices=Autocorrelacion.ESTILOS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mostrar_datos = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=[],
        required=False
    )
    def __init__(self, frecuencia, mostrar_opciones, analisis_uuid, *args, **kwargs):
        super(AutocorrelacionForm, self).__init__(*args, **kwargs)

        max_values = {
            'dias': 100,
            'horas': 2400,
            '10 minutos': 14400,
            'meses': 10,
            'años': 5
        }

        if frecuencia in max_values:
            self.fields['lag'].widget.attrs['max'] = max_values[frecuencia]
            self.fields['lag'].max_value = max_values[frecuencia]
        else:
            self.fields['lag'].widget.attrs.pop('max', None)
            self.fields['lag'].max_value = None

        if mostrar_opciones:
            self.fields['mostrar_datos'].choices = [(op, op.capitalize()) for op in mostrar_opciones]


class DeteccionDeOutliersForm(forms.Form):
    titulo = forms.CharField(
        label="Título",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=50,
        required=True
    )
    umbral = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    metodo = forms.ChoiceField(
        choices=DeteccionDeOutliers.METODO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    visualizacion = forms.ChoiceField(
        choices=DeteccionDeOutliers.ESTILOS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mostrar_datos = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=[],
        required=False
    )
    def __init__(self, frecuencia, mostrar_opciones, analisis_uuid, *args, **kwargs):
        super(DeteccionDeOutliersForm, self).__init__(*args, **kwargs)
        max_values = {
            'dias': 10,
            'horas': 60,
            '10 minutos': 360,
            'meses': 2,
            'años': 1
        }

        if frecuencia in max_values:
            self.fields['umbral'].widget.attrs['max'] = max_values[frecuencia]
            self.fields['umbral'].max_value = max_values[frecuencia]
        else:
            self.fields['umbral'].widget.attrs.pop('max', None)
            self.fields['umbral'].max_value = None

        if mostrar_opciones:
            self.fields['mostrar_datos'].choices = [(op, op.capitalize()) for op in mostrar_opciones]

class DescomposicionDeSeriesTemporalesForm(forms.Form):
    titulo = forms.CharField(
        label="Título",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=50
    )
    metodo = forms.ChoiceField(
        label="Método",
        choices=DescomposicionDeSeriesTemporales.METODO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    visualizacion = forms.ChoiceField(
        label="Visualización",
        choices=DescomposicionDeSeriesTemporales.ESTILOS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mostrar_datos = forms.ChoiceField(
        label="Datos a Mostrar",
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=[],
        required=False
    )
    ventana_tendencia = forms.IntegerField(
        label="Ventana de Suavizado de Tendencia",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        min_value=1
    )
    ventana_estacionalidad = forms.IntegerField(
        label="Ventana de Suavizado de Estacionalidad",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        min_value=1,
        max_value=14
    )
    suavizado_exponencial = forms.FloatField(
        label="Factor de Suavizado Exponencial",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        min_value=0.01,
        max_value=1.0
    )
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    fecha_fin = forms.DateField(
        label="Fecha de Fin",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )

    def __init__(self, mostrar_opciones,fecha_inicio_por_defecto, fecha_fin_por_defecto,analisis_uuid, *args, **kwargs):
        super(DescomposicionDeSeriesTemporalesForm, self).__init__(*args, **kwargs)
        if mostrar_opciones:
            self.fields['mostrar_datos'].choices = [(op, op.capitalize()) for op in mostrar_opciones]

        self.fields['fecha_inicio'].initial = fecha_inicio_por_defecto
        
        self.fields['fecha_fin'].initial = fecha_fin_por_defecto