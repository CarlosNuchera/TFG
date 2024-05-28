from rest_framework import viewsets
from .serializer import AnalisisSerializer
from esios.models import Datos
from analisis.models import Analisis

class AnalisisViewSet(viewsets.ModelViewSet):

    queryset= Analisis.objects.all()
    serializer_class = AnalisisSerializer
