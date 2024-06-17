from django.test import TestCase
from django.contrib.auth.models import User
from esios.models import Datos
from .models import *
from django.utils import timezone


class AnalisisModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.datos = Datos.objects.create(
            nombre='Datos Test',
            fecha=timezone.now(),
        )
        self.analisis = Analisis.objects.create(
            nombre='Analisis Test',
            descripcion='Descripcion Test',
            usuario=self.user,
            frecuencia='dias',
            estado='en proceso',
            terminos_y_condiciones=True
        )
        self.analisis.tipos_de_dato.add(self.datos)

    def test_analisis_creation(self):
        self.assertEqual(self.analisis.nombre, 'Analisis Test')
        self.assertEqual(self.analisis.descripcion, 'Descripcion Test')
        self.assertEqual(self.analisis.usuario.username, 'testuser')
        self.assertTrue(self.analisis.terminos_y_condiciones)

    def test_analisis_string_representation(self):
        self.assertEqual(str(self.analisis), 'Analisis Test')


class AutocorrelacionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.analisis = Analisis.objects.create(
            nombre='Analisis Test',
            descripcion='Descripcion Test',
            usuario=self.user
        )
        self.autocorrelacion = Autocorrelacion.objects.create(
            analisis=self.analisis,
            fecha=timezone.now(),
            lag=5,
            metodo_calculo='Spearman',
            tipo='simple',
            estilo='lineas',
            titulo='Autocorrelacion Test',
            nombre='Autocorrelacion Nombre'
        )

    def test_autocorrelacion_creation(self):
        self.assertEqual(self.autocorrelacion.titulo, 'Autocorrelacion Test')
        self.assertEqual(self.autocorrelacion.metodo_calculo, 'Spearman')

    def test_autocorrelacion_string_representation(self):
        self.assertEqual(str(self.autocorrelacion), 'Autocorrelacion Test')

class DeteccionDeOutliersModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.analisis = Analisis.objects.create(
            nombre='Analisis Test',
            descripcion='Descripcion Test',
            usuario=self.user
        )
        self.outlier = DeteccionDeOutliers.objects.create(
            analisis=self.analisis,
            fecha=timezone.now(),
            umbral=3,
            metodo_calculo='Desviacion estandar',
            estilo='Simple',
            titulo='Deteccion Outlier Test',
            nombre='Outlier Nombre'
        )

    def test_outlier_creation(self):
        self.assertEqual(self.outlier.titulo, 'Deteccion Outlier Test')
        self.assertEqual(self.outlier.umbral, 3)

    def test_outlier_string_representation(self):
        self.assertEqual(str(self.outlier), 'Deteccion Outlier Test')

class DescomposicionDeSeriesTemporalesModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.analisis = Analisis.objects.create(
            nombre='Analisis Test',
            descripcion='Descripcion Test',
            usuario=self.user
        )
        self.descomposicion = DescomposicionDeSeriesTemporales.objects.create(
            analisis=self.analisis,
            fecha=timezone.now(),
            metodo_calculo='Aditiva',
            estilo='Simple',
            titulo='Descomposicion Test',
            nombre='Descomposicion Nombre',
            fecha_inicio='2023-01-01',
            fecha_fin='2023-12-31'
        )

    def test_descomposicion_creation(self):
        self.assertEqual(self.descomposicion.titulo, 'Descomposicion Test')
        self.assertEqual(self.descomposicion.metodo_calculo, 'Aditiva')

    def test_descomposicion_string_representation(self):
        self.assertEqual(str(self.descomposicion), 'Descomposicion Test')

class GraficaModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.analisis = Analisis.objects.create(
            nombre='Analisis Test',
            descripcion='Descripcion Test',
            usuario=self.user
        )
        self.grafica = Grafica.objects.create(
            analisis=self.analisis,
            titulo='Grafica Test',
            tipo_dato='Tipo Test',
            imagen_html='<p>Imagen Test</p>'
        )

    def test_grafica_creation(self):
        self.assertEqual(self.grafica.titulo, 'Grafica Test')
        self.assertEqual(self.grafica.tipo_dato, 'Tipo Test')

    def test_grafica_string_representation(self):
        self.assertEqual(str(self.grafica), f'Grafica para {self.analisis}')
