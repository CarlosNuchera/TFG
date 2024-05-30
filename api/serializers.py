from rest_framework import serializers
from analisis.models import Analisis

class AnalisisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisis
        fields = '__all__'