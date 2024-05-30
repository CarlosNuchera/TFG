from rest_framework import serializers
from analisis.models import *

class AnalisisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisis
        fields = '__all__'

class AutocorrelacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autocorrelacion
        fields = '__all__'

class DeteccionDeOutliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeteccionDeOutliers
        fields = '__all__'

class DescomposicionDeSeriesTemporalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescomposicionDeSeriesTemporales
        fields = '__all__'

class ResultadosAutocorrelacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResulatadosAutocorrelacion
        fields = '__all__'

class ResultadosDeteccionDeOutliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResulatadosDeteccionDeOutliers
        fields = '__all__'

class ResultadosDescomposicionDeSeriesTemporalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadosDescomposicionDeSeriesTemporales
        fields = '__all__'