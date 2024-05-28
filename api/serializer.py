from rest_framework import serializers
from esios.models import Datos
from analisis.models import Analisis

class AnalisisSerializer(serializers.ModelSerializer):
    class Meta:
        model=Analisis
        fields = '__all__'