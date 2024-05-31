from django.db import models
from esios.models import Datos
from django.contrib.auth.models import User
import uuid

class Analisis(models.Model):
    FRECUENCIA_CHOICES = [
        ('10 minutos', '10 minutos'),
        ('horas', 'Horas'),
        ('dias', 'Dias'),
        ('meses', 'Meses'),
        ('años', 'Años'),
    ]
    ESTADO = [
        ('en proceso', 'En proceso'),
        ('terminado', 'Terminado'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion=models.TextField()
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='dias')
    fecha_creacion=models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, default=None, on_delete=models.CASCADE)
    tipos_de_dato = models.ManyToManyField(Datos, through='AnalisisDatos', related_name='analisis')
    estado=models.CharField(max_length=30, choices=ESTADO,default='En proceso')

    def __str__(self):
        return self.nombre
    
class AnalisisDatos(models.Model):
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    datos = models.ForeignKey(Datos, on_delete=models.CASCADE)

class DatosPreprocesados(models.Model):
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    tipo_dato = models.CharField(max_length=50,null=True, blank=True)
    nombre = models.CharField(max_length=100,null=True, blank=True)
    fecha = models.DateTimeField(unique=False)
    precio = models.FloatField(null=True, blank=True)
    consumo = models.FloatField(null=True, blank=True)
    porcentaje = models.FloatField(null=True, blank=True)

class Autocorrelacion(models.Model):
    METODO_CHOICES = [
        ('Spearman', 'Spearman'),
        ('Pearson', 'Pearson'),
    ]

    TIPO_CHOICES = [
        ('simple', 'Simple'),
        ('parcial', 'Parcial'),
    ]
    ESTILOS_CHOICES = [
        ('lineas', 'Lineas'),
        ('puntos', 'Puntos'),

    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    fecha = models.DateTimeField(unique=False)
    lag = models.IntegerField(default=1)
    metodo_calculo = models.CharField(max_length=20, choices=METODO_CHOICES, default='Spearman')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='parcial')
    estilo = models.CharField(max_length=20, choices=ESTILOS_CHOICES, default='lineas')
    titulo = models.CharField(max_length=50, default='')
    nombre=models.CharField(max_length=50, default='')
    def __str__(self):
        return self.titulo
    
class ResulatadosAutocorrelacion(models.Model):
    autocorrelacion = models.ForeignKey(Autocorrelacion, on_delete=models.CASCADE)
    lag = models.IntegerField(default=1)
    valor=models.FloatField(default=0.0)
    nombre_dato=models.CharField(max_length=100, default='')

class DeteccionDeOutliers(models.Model):
    METODO_CHOICES = [
        ('Desviacion estandar', 'Desviacion estandar'),
        ('Rango intercuartilico', 'Rango intercuartilico'),
    ]
    ESTILOS_CHOICES = [
        ('Simple', 'Simple'),
        ('Histograma', 'Histograma'),
        ('Box_Plot', 'Box_Plot'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    fecha = models.DateTimeField(unique=False)
    umbral = models.IntegerField(default=1)
    metodo_calculo = models.CharField(max_length=30, choices=METODO_CHOICES, default='Desviacion estandar')
    estilo = models.CharField(max_length=20, choices=ESTILOS_CHOICES, default='Simple')
    titulo = models.CharField(max_length=50, default='')
    nombre=models.CharField(max_length=50, default='')
    def __str__(self):
        return self.titulo

class ResulatadosDeteccionDeOutliers(models.Model):
    deteccion_de_outlier = models.ForeignKey(DeteccionDeOutliers, on_delete=models.CASCADE)
    nombre_dato=models.CharField(max_length=100, default='')
    fecha_dato=models.DateTimeField(unique=False)
    valor=models.FloatField(default=0.0)

class DescomposicionDeSeriesTemporales(models.Model):
    METODO_CHOICES = [
        ('Aditiva', 'Aditiva'),
        ('Multiplicativa', 'Multiplicativa'),
    ]
    ESTILOS_CHOICES = [
        ('Simple', 'Simple'),
        ('Grafico de area', 'Grafico de area'),
        ('Grafico de barras', 'Grafico de barras'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    fecha = models.DateTimeField(unique=False)
    metodo_calculo = models.CharField(max_length=30, choices=METODO_CHOICES, default='Desviacion estandar')
    estilo = models.CharField(max_length=20, choices=ESTILOS_CHOICES, default='Simple')
    titulo = models.CharField(max_length=50, default='')
    nombre=models.CharField(max_length=50, default='')
    ventana_tendencia = models.IntegerField(null=True, blank=True)
    ventana_estacionalidad = models.IntegerField(null=True, blank=True)
    suavizado_exponencial = models.FloatField(null=True, blank=True)
    fecha_inicio = models.DateField(unique=False)
    fecha_fin = models.DateField(unique=False)

    def __str__(self):
        return self.titulo
    
class ResultadosDescomposicionDeSeriesTemporales(models.Model):
    descomposicion = models.ForeignKey(DescomposicionDeSeriesTemporales, on_delete=models.CASCADE)
    nombre_dato=models.CharField(max_length=100, default='')
    fecha_dato = models.DateTimeField(unique=False)
    valor_dato = models.FloatField(null=True, blank=True)
    tendencia = models.FloatField(null=True, blank=True)
    estacionalidad = models.FloatField(null=True, blank=True)
    residuo = models.FloatField(null=True, blank=True)


class Grafica(models.Model):
    analisis = models.ForeignKey(Analisis, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    titulo = models.CharField(max_length=100)
    tipo_dato = models.CharField(max_length=50)
    imagen_html = models.TextField()

    def __str__(self):
        return f"Grafica para {self.analisis}"
    