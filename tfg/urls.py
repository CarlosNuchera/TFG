from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('accounts/',include('django.contrib.auth.urls')),
    path('analizar/', include('analisis.urls')),
    path('api/', include('api.urls'))
]

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)


handler404 = custom_404
handler500 = custom_500