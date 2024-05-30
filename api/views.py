from api.serializers import *
from analisis.models import *
from rest_framework import generics
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
import numpy as np

def api_info(request):
    return render(request, 'api_info.html')


class AnalisisListView(generics.ListAPIView):
    queryset = Analisis.objects.all()
    serializer_class = AnalisisSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('uuid', openapi.IN_QUERY, description="UUID del análisis", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('nombre', openapi.IN_QUERY, description="Nombre del análisis", type=openapi.TYPE_STRING),
            openapi.Parameter('frecuencia', openapi.IN_QUERY, description="Frecuencia del análisis", type=openapi.TYPE_STRING, enum=[choice[0] for choice in Analisis.FRECUENCIA_CHOICES]),
        ]
    )
    def get(self, request, *args, **kwargs):
        uuid_str = request.GET.get('uuid')
        if not uuid_str:
            return Response({'error': 'El parámetro uuid es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid_obj = uuid.UUID(uuid_str)
        except ValueError:
            return Response({'error': 'UUID inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(uuid=uuid_obj)

        nombre = request.GET.get('nombre')
        frecuencia = request.GET.get('frecuencia')

        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if frecuencia:
            queryset = queryset.filter(frecuencia=frecuencia)
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AutocorrelacionListView(generics.ListAPIView):
    queryset = Autocorrelacion.objects.all()
    serializer_class = AutocorrelacionSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('analisis_uuid', openapi.IN_QUERY, description="UUID del análisis", type=openapi.TYPE_STRING, required=True),
            
        ]
    )
    def get(self, request, *args, **kwargs):
        analisis_id = request.GET.get('analisis_uuid')
        if not analisis_id:
            return Response({'error': 'El parámetro analisis_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid_obj = uuid.UUID(analisis_id)
        except ValueError:
            return Response({'error': 'UUID inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(analisis__uuid=uuid_obj)


        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DeteccionDeOutliersListView(generics.ListAPIView):
    queryset = DeteccionDeOutliers.objects.all()
    serializer_class = DeteccionDeOutliersSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('analisis_uuid', openapi.IN_QUERY, description="UUID del análisis", type=openapi.TYPE_STRING, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        analisis_id = request.GET.get('analisis_uuid')
        if not analisis_id:
            return Response({'error': 'El parámetro analisis_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid_obj = uuid.UUID(analisis_id)
        except ValueError:
            return Response({'error': 'UUID inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(analisis__uuid=uuid_obj)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DescomposicionDeSeriesTemporalesListView(generics.ListAPIView):
    queryset = DescomposicionDeSeriesTemporales.objects.all()
    serializer_class = DescomposicionDeSeriesTemporalesSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('analisis_uuid', openapi.IN_QUERY, description="UUID del análisis", type=openapi.TYPE_STRING, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        analisis_id = request.GET.get('analisis_uuid')
        if not analisis_id:
            return Response({'error': 'El parámetro analisis_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid_obj = uuid.UUID(analisis_id)
        except ValueError:
            return Response({'error': 'UUID inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(analisis__uuid=uuid_obj)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResultadosAutocorrelacionListView(generics.ListAPIView):
    queryset = ResulatadosAutocorrelacion.objects.all()
    serializer_class = ResultadosAutocorrelacionSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('autocorrelacion_id', openapi.IN_QUERY, description="ID de la autocorrelación", type=openapi.TYPE_INTEGER, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        autocorrelacion_id = request.GET.get('autocorrelacion_id')
        if not autocorrelacion_id:
            return Response({'error': 'El parámetro autocorrelacion_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(autocorrelacion_id=autocorrelacion_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResultadosDeteccionDeOutliersListView(generics.ListAPIView):
    queryset = ResulatadosDeteccionDeOutliers.objects.all()
    serializer_class = ResultadosDeteccionDeOutliersSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('deteccion_de_outliers_id', openapi.IN_QUERY, description="ID de la detección de outliers", type=openapi.TYPE_INTEGER, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        deteccion_de_outlier_id = request.GET.get('deteccion_de_outliers_id')
        if not deteccion_de_outlier_id:
            return Response({'error': 'El parámetro deteccion_de_outliers_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(deteccion_de_outlier_id=deteccion_de_outlier_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class ResultadosDescomposicionDeSeriesTemporalesListView(generics.ListAPIView):
    queryset = ResultadosDescomposicionDeSeriesTemporales.objects.all()
    serializer_class = ResultadosDescomposicionDeSeriesTemporalesSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('descomposicion_id', openapi.IN_QUERY, description="ID de la descomposición de serie temporal", type=openapi.TYPE_INTEGER, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        descomposicion_id = request.GET.get('descomposicion_id')
        if not descomposicion_id:
            return Response({'error': 'El parámetro descomposicion_de_serie_temporal_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(descomposicion_id=descomposicion_id)

        # Filtrar objetos con valores 'nan' en alguno de los campos
        queryset = [obj for obj in queryset if not (
            np.isnan(obj.residuo) or np.isnan(obj.estacionalidad) or np.isnan(obj.tendencia)
        )]

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)