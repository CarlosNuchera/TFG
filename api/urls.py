from django.urls import path,include
from rest_framework import routers
from api import views
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import *

schema_view = get_schema_view(
    openapi.Info(
        title="ESIOS API",
        default_version='v1',
        description="Aquí podremos realizar todo tipo de consultas, pudiendo visualizar todos los datos de la base de datos para este proyecto",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="carnucbol@alum.us.es"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns=[
    path('',api_info,name='api_info'),
    path('analisis/',AnalisisListView.as_view(),name='analisis-list'),
    path('analisis/autocorrelacion/',AutocorrelacionListView.as_view(),name='autocorrelacion-list'),
    path('analisis/deteccion_de_outliers/',DeteccionDeOutliersListView.as_view(),name='deteccion_de_outliers-list'),
    path('analisis/descomposicion_de_series_temporales/',DescomposicionDeSeriesTemporalesListView.as_view(),name='descomposicion_de_series_temporales-list'),
    path('analisis/autocorrelacion/resultados_autocorrelacion',ResultadosAutocorrelacionListView.as_view(),name='resultados_autocorrelacion-list'),
    path('analisis/deteccion_de_outliers/resultados_deteccion_de_outliers',ResultadosDeteccionDeOutliersListView.as_view(),name='resultados_deteccion_de_outliers-list'),
    path('analisis/descomposicion_de_series_temporales/resultados_descomposicion_de_series_temporales',ResultadosDescomposicionDeSeriesTemporalesListView.as_view(),name='resultados_descomposicion_de_series_temporales-list'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]