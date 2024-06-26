from django.urls import path
from .views import analizar, resultados, mis_analisis, descargar_csv, calcular_autocorrelacion, resultados_autocorrelacion, deteccion_de_outliers, resultados_deteccion_de_outliers, descomposicion_de_series_temporales, resultados_descomposicion_de_series_temporales, previsualizacion_pdf, descargar_pdf,terminos_y_condiciones

urlpatterns = [
    path('', analizar, name='analizar'),
    path('mis_analisis/', mis_analisis, name='mis_analisis'),
    path('terminos_y_condiciones/', terminos_y_condiciones, name='terminos_y_condiciones'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/', resultados, name='resultados'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/descargar_csv/', descargar_csv, name='descargar_csv'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/autocorrelacion/', calcular_autocorrelacion, name='autocorrelacion'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/deteccion_de_outliers/', deteccion_de_outliers, name='deteccion_de_outliers'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/descomposicion_de_series_temporales/', descomposicion_de_series_temporales, name='descomposicion_de_series_temporales'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/autocorrelacion/resultados_autocorrelacion/', resultados_autocorrelacion, name='resultados_autocorrelacion'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/deteccion_de_outliers/resultados_deteccion_de_outliers/', resultados_deteccion_de_outliers, name='resultados_deteccion_de_outliers'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/descomposicion_de_series_temporales/resultados_descomposicion_de_series_temporales/', resultados_descomposicion_de_series_temporales, name='resultados_descomposicion_de_series_temporales'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/previsualizacion_pdf', previsualizacion_pdf, name='previsualizacion_pdf'),
    path('mis_analisis/<uuid:analisis_uuid>/resultados/previsualizacion_pdf/descargar-pdf/', descargar_pdf, name='descargar_pdf'),
]
