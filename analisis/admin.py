from django.contrib import admin
from.models import  Analisis, Autocorrelacion,DatosPreprocesados, DeteccionDeOutliers, DescomposicionDeSeriesTemporales

admin.site.register(Analisis)
admin.site.register(Autocorrelacion)
admin.site.register(DeteccionDeOutliers)
admin.site.register(DatosPreprocesados)
admin.site.register(DescomposicionDeSeriesTemporales)

