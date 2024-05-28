from rest_framework import serializers
from .models import Esios

class EsisosSeriealizers(serializers.ModelSerializer):
    class Meta:
        model = Esios
        fields = ('id', 'title', 'description', 'technology', 'created_at')
        read_only_fields = ('created_at',)