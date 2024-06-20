from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objs as go
from django.http import Http404
from .tasks import procesar_datos_en_segundo_plano
import matplotlib
import plotly.express as px
matplotlib.use('Agg')
from django.http import HttpResponse
import csv
from datetime import datetime
from django.contrib import messages
import numpy as np
from scipy.stats import zscore
from datetime import datetime
from xhtml2pdf import pisa
from django.template.loader import render_to_string
import plotly.io as py
from PIL import Image
import io
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose

@login_required(login_url="accounts/login/")
def terminos_y_condiciones(request):
    return render(request, 'terminos_y_condiciones.html')


@login_required(login_url="accounts/login/")
def analizar(request):
    
    analisis_por_usuario = Analisis.objects.filter(usuario=request.user)
    numero_analisis_por_estado = {}
    for analisis in analisis_por_usuario:
        estado = analisis.estado
        numero_analisis_por_estado[estado] = numero_analisis_por_estado.get(estado, 0) + 1

    if numero_analisis_por_estado.get('En proceso', 0) > 0:
        error_message = 'Ya hay un análisis en proceso. No se puede iniciar otro.'
        return render(request, 'analizar.html', {'error_message': error_message})

    if request.method == 'POST':
        form = AnalisisForm(request.POST, request.FILES)
        if form.is_valid():
            analisis = form.save(commit=False)
            analisis.usuario = request.user
            frecuencia = form.cleaned_data['frecuencia']
            aceptado = form.cleaned_data['terminos_aceptados']
            analisis.frecuencia = frecuencia
            if aceptado == True:
                analisis.save()
                analisis_id=analisis.id
                tipos_seleccionados = form.cleaned_data['tipos_de_dato']
                
                if not isinstance(tipos_seleccionados, list):
                    tipos_seleccionados = [tipos_seleccionados]
                procesar_datos_en_segundo_plano.delay(analisis_id, tipos_seleccionados)
    
                return redirect('mis_analisis')
    else:
        form = AnalisisForm()
    return render(request, 'analizar.html', {'form': form})

@login_required(login_url="accounts/login/")
def mis_analisis(request):
    if request.method == 'POST':
        analisis_uuids = request.POST.getlist('analisis_uuids')
        Analisis.objects.filter(uuid__in=analisis_uuids, usuario=request.user).delete()
        return redirect('mis_analisis')

    analisis_usuario = Analisis.objects.filter(usuario=request.user)
    tipos_dato_por_analisis = {}
    for analisis in analisis_usuario:
        tipos_dato_por_analisis[analisis] = analisis.tipos_de_dato.values_list('tipo_dato', flat=True).distinct()

    return render(request, 'mis_analisis.html', {'tipos_dato_por_analisis': tipos_dato_por_analisis})


@login_required(login_url="accounts/login/")
def resultados(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    if analisis.estado != 'Terminado':
        raise Http404("No se puede acceder a los resultados hasta que el análisis esté terminado.")

    tipos_dato_unicos = set(analisis.tipos_de_dato.values_list('tipo_dato', flat=True))

    return render(request, 'resultados.html', {'analisis': analisis, 'tipos_dato_unicos': tipos_dato_unicos, 'analisis_uuid':analisis_uuid})

@login_required(login_url="accounts/login/")
def descargar_csv(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    datos = DatosPreprocesados.objects.filter(analisis=analisis)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="datos.csv"'

    writer = csv.writer(response)

    writer.writerow(['Tipo Dato', 'Nombre', 'Fecha', 'Precio', 'Consumo', 'Porcentaje', 'Nombre Analisis'])

    for dato in datos:
        writer.writerow([dato.tipo_dato, dato.nombre, dato.fecha, dato.precio, dato.consumo, dato.porcentaje, dato.analisis])
    return response



@login_required(login_url="accounts/login/")
def calcular_autocorrelacion(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    datos = DatosPreprocesados.objects.filter(analisis=analisis).order_by('fecha')
    datos_precio = datos.filter(precio__isnull=False)
    datos_consumo = datos.filter(consumo__isnull=False)
    datos_porcentaje = datos.filter(porcentaje__isnull=False)
    autocorrelaciones = Autocorrelacion.objects.filter(analisis=analisis)
    graficas_autocorrelaciones = Grafica.objects.filter(analisis=analisis, tipo_dato="Autocorrelacion")
    numero_graficas_por_usuario = Grafica.objects.filter(analisis=analisis, tipo_dato="Autocorrelacion").count()

    diccionario_datos = {
        columna: list(datos.values_list(columna, flat=True))
        for columna in [field.name for field in DatosPreprocesados._meta.get_fields()]
    }

    mostrar_datos = [
        columna for columna, datos_columna in diccionario_datos.items()
        if columna in ['precio', 'consumo', 'porcentaje'] and any(dato is not None for dato in datos_columna)
    ]

    frecuencia_analisis = analisis.frecuencia

    def extraer_datos(datos_filtrados, campo):
        datos_por_nombre = {}
        fechas_por_nombre = {}
        for dato in datos_filtrados:
            if dato.nombre not in datos_por_nombre:
                datos_por_nombre[dato.nombre] = []
                fechas_por_nombre[dato.nombre] = []
            fechas_por_nombre[dato.nombre].append(dato.fecha)
            datos_por_nombre[dato.nombre].append(getattr(dato, campo))
        return datos_por_nombre, fechas_por_nombre

    precios_por_nombre, fechas_precio_por_nombre = extraer_datos(datos_precio, 'precio')
    consumos_por_nombre, fechas_consumo_por_nombre = extraer_datos(datos_consumo, 'consumo')
    porcentajes_por_nombre, fechas_porcentaje_por_nombre = extraer_datos(datos_porcentaje, 'porcentaje')

    if request.method == 'POST':
        form = AutocorrelacionForm(frecuencia=frecuencia_analisis, mostrar_opciones=mostrar_datos, data=request.POST, analisis_uuid=analisis_uuid)
        if form.is_valid():
            lag = form.cleaned_data['lag']
            tipo = form.cleaned_data['tipo']
            metodo = form.cleaned_data['metodo']
            visualizacion = form.cleaned_data['visualizacion']
            mostrar_datos = form.cleaned_data['mostrar_datos']
            titulo = form.cleaned_data['titulo']

            def create_autocorrelation_fig(datos_por_nombre, fechas_por_nombre, campo):
                datos_fig = go.Figure()
                autocorrelation_fig = go.Figure()
                autocorrelaciones_por_nombre = {}

                def pearson_autocorr(x, lag):
                    x = np.array(x)
                    n = len(x)
                    x_mean = np.mean(x)
                    c0 = np.sum((x - x_mean) ** 2) / n
                    return np.array([1 if l == 0 else np.sum((x[:n-l] - x_mean) * (x[l:] - x_mean)) / (n * c0) for l in range(lag + 1)])

                def spearman_autocorr(x, lag):
                    ranks = pd.Series(x).rank().values
                    return pearson_autocorr(ranks, lag)

                def spearman_partial_autocorr(x, lag):
                    ranks = pd.Series(x).rank().values
                    pacf_values = pacf(ranks, nlags=lag, method='ols')
                    return pacf_values

                for nombre, valores in datos_por_nombre.items():
                    fechas = fechas_por_nombre[nombre]
                    color_datos = px.colors.qualitative.Plotly[len(datos_fig.data) % len(px.colors.qualitative.Plotly)]
                    color_autocorrelacion = px.colors.qualitative.Plotly[len(autocorrelation_fig.data) % len(px.colors.qualitative.Plotly)]

                    datos_fig.add_trace(go.Scatter(x=fechas, y=valores, mode='lines', name=nombre, line=dict(color=color_datos)))

                    df = pd.DataFrame({'Fecha': fechas, campo.capitalize(): valores})
                    df['Fecha'] = pd.to_datetime(df['Fecha'])
                    df.set_index('Fecha', inplace=True)

                    if tipo == 'simple':
                        if metodo == 'Pearson':
                            autocorr = acf(df[campo.capitalize()], nlags=lag, fft=True)
                        elif metodo == 'Spearman':
                            autocorr = spearman_autocorr(df[campo.capitalize()].values, lag)
                    elif tipo == 'parcial':
                        if metodo == 'Pearson':
                            autocorr = pacf(df[campo.capitalize()], nlags=lag, method='ols')
                        elif metodo == 'Spearman':
                            autocorr = spearman_partial_autocorr(df[campo.capitalize()].values, lag)

                    autocorrelation_fig.add_trace(go.Scatter(
                        x=list(range(lag + 1)), y=autocorr, mode='markers+lines' if visualizacion == 'lineas' else 'markers',
                        name=f'Autocorrelación {nombre}', line=dict(color=color_autocorrelacion),
                        marker=dict(color=color_autocorrelacion, size=8 if visualizacion == 'puntos' else None))
                    )

                    if nombre not in autocorrelaciones_por_nombre:
                        autocorrelaciones_por_nombre[nombre] = []
                    autocorrelaciones_por_nombre[nombre].append(autocorr)

                datos_fig.update_layout(title='Datos', xaxis_title='Fecha', yaxis_title=campo.capitalize())
                autocorrelation_fig.update_layout(title='Autocorrelación', xaxis_title='Lag', yaxis_title='Autocorrelación')

                return datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre

            if mostrar_datos == 'precio':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_tipo_dato = create_autocorrelation_fig(precios_por_nombre, fechas_precio_por_nombre, 'precio')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)
            elif mostrar_datos == 'consumo':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_tipo_dato = create_autocorrelation_fig(consumos_por_nombre, fechas_consumo_por_nombre, 'consumo')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)
            elif mostrar_datos == 'porcentaje':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_tipo_dato = create_autocorrelation_fig(porcentajes_por_nombre, fechas_porcentaje_por_nombre, 'porcentaje')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)

            def adjuntar_grafica(grafica):
                if not Grafica.objects.filter(analisis=analisis, tipo_dato="Autocorrelacion", imagen_html=grafica):
                    Grafica.objects.create(
                        analisis=analisis,
                        fecha_creacion=datetime.now(),
                        titulo=f"Figura {numero_graficas_por_usuario+1} de Autocorrelación ",
                        tipo_dato="Autocorrelacion",
                        imagen_html=grafica
                    )
                    messages.success(request, "Gráfica añadida correctamente")
                else:
                    messages.warning(request, "Hay una grafica igual adjuntada")
            action = request.POST.get('action')
            if action == 'adjuntar_plot_div':
                adjuntar_grafica(plot_div)
            elif action == 'adjuntar_autocorrelacion_plot_div':
                adjuntar_grafica(autocorrelation_plot_div)
            elif action == 'guardar':
                if Autocorrelacion.objects.filter(titulo=titulo, analisis=analisis).exists():
                    messages.warning(request, "Ya tiene una autocorrelación con el mismo título.")
                elif not Autocorrelacion.objects.filter(
                    analisis=analisis, lag=lag, metodo_calculo=metodo, tipo=tipo,
                    estilo=visualizacion, nombre=mostrar_datos
                ).exists():
                    autocorrelacion = Autocorrelacion.objects.create(
                        analisis=analisis, fecha=datetime.now(), lag=lag,
                        metodo_calculo=metodo, tipo=tipo, estilo=visualizacion,
                        titulo=titulo, nombre=mostrar_datos
                    )
                    messages.success(request, "Autocorrelación añadida correctamente")
                    for nombre_dato, autocorr in autocorrelaciones_por_nombre_tipo_dato.items():
                        for i in range(1, lag + 1):
                            valor_autocorr = autocorr[0][i]
                            ResulatadosAutocorrelacion.objects.create(
                                autocorrelacion=autocorrelacion, lag=i,
                                valor=valor_autocorr, nombre_dato=nombre_dato
                            )
                else:
                    messages.warning(request, "Ya existe una autocorrelación con los mismos datos.")
            return render(request, 'autocorrelacion.html', {
                'form': form, 'plot_div': plot_div,
                'autocorrelation_plot_div': autocorrelation_plot_div,
                'analisis': analisis, 'autocorrelaciones': autocorrelaciones,
                'analisis_uuid': analisis_uuid,
                'graficas': graficas_autocorrelaciones
            })

    else:
        form = AutocorrelacionForm(frecuencia=frecuencia_analisis, mostrar_opciones=mostrar_datos, analisis_uuid=analisis_uuid)
        form.fields['mostrar_datos'].choices = [(c, c.capitalize()) for c in mostrar_datos]

    return render(request, 'autocorrelacion.html', {'form': form, 'analisis': analisis, 'autocorrelaciones': autocorrelaciones, 'analisis_uuid': analisis_uuid, 'graficas': graficas_autocorrelaciones})


@login_required(login_url="accounts/login/")
def resultados_autocorrelacion(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    graficas_autocorrelacion = Grafica.objects.filter(analisis=analisis, tipo_dato="Autocorrelacion")
    autocorrelaciones = Autocorrelacion.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_autocorrelacion = ResulatadosAutocorrelacion.objects.filter(autocorrelacion__in=autocorrelaciones)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_grafica':
            grafica_id = request.POST.get('grafica_id')
            grafica = get_object_or_404(Grafica, id=grafica_id)
            grafica.delete()
        form = DeleteResultsForm(request.POST)
        if form.is_valid():
            titulo_autocorrelacion = form.cleaned_data['titulo']
            try:
                autocorrelacion = Autocorrelacion.objects.get(titulo=titulo_autocorrelacion, analisis=analisis)
                autocorrelacion.delete()
                messages.success(request, f"La autocorrelación '{titulo_autocorrelacion}' y sus resultados han sido eliminados.")
            except Autocorrelacion.DoesNotExist:
                messages.error(request, f"No se encontró ninguna autocorrelación con el título '{titulo_autocorrelacion}'.")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = DeleteResultsForm()

    return render(request, 'resultados_autocorrelacion.html', {
        'analisis': analisis,
        'datos': datos_resultados_autocorrelacion,
        'analisis_uuid': analisis_uuid,
        'graficas': graficas_autocorrelacion,
        'form': form
    })


@login_required(login_url="accounts/login/")
def deteccion_de_outliers(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    datos = list(DatosPreprocesados.objects.filter(analisis=analisis).order_by('fecha'))
    deteccion_de_outlierss = DeteccionDeOutliers.objects.filter(analisis=analisis)
    graficas_detecciones = Grafica.objects.filter(analisis=analisis, tipo_dato="Deteccion de Outliers")
    numero_graficas_por_usuario = Grafica.objects.filter(analisis=analisis, tipo_dato="Deteccion de Outliers").count()
    
    diccionario_datos = {field.name: [] for field in DatosPreprocesados._meta.get_fields()}
    for dato in datos:
        for field in diccionario_datos.keys():
            diccionario_datos[field].append(getattr(dato, field))

    mostrar_datos = [col for col in ['precio', 'consumo', 'porcentaje'] if any(diccionario_datos[col])]

    datos_por_nombre = {col: {} for col in mostrar_datos}
    fechas_por_nombre = {col: {} for col in mostrar_datos}
    
    for dato in datos:
        for col in mostrar_datos:
            if getattr(dato, col) is not None:
                if dato.nombre not in datos_por_nombre[col]:
                    datos_por_nombre[col][dato.nombre] = []
                    fechas_por_nombre[col][dato.nombre] = []
                datos_por_nombre[col][dato.nombre].append(getattr(dato, col))
                fechas_por_nombre[col][dato.nombre].append(dato.fecha)

    def detectar_outliers(data, umbral, metodo):
        if metodo == 'Desviacion estandar':
            z_scores = np.abs(zscore(data))
            return np.where(z_scores > umbral)[0]
        elif metodo == 'Rango intercuartilico':
            Q1, Q3 = np.percentile(data, [25, 75])
            IQR = Q3 - Q1
            lower_bound, upper_bound = Q1 - umbral * IQR, Q3 + umbral * IQR
            return np.where((data < lower_bound) | (data > upper_bound))[0]
        return []

    def crear_figura(data_dict, fecha_dict, col_name, umbral, metodo, visualizacion, titulo):
        fig = go.Figure()
        outliers_por_nombre = {}

        for nombre, valores in data_dict.items():
            valores_array = np.array(valores)
            outliers = detectar_outliers(valores_array, umbral, metodo)

            fechas = fecha_dict[nombre]
            fechas_outliers = [fechas[i] for i in outliers]
            valores_outliers = [valores[i] for i in outliers]

            color_datos = px.colors.qualitative.Plotly[list(data_dict.keys()).index(nombre) % len(px.colors.qualitative.Plotly)]
            if visualizacion == 'Simple':
                fig.add_trace(go.Scatter(x=fechas, y=valores, mode='lines', name=nombre, line=dict(color=color_datos)))
                fig.add_trace(go.Scatter(x=fechas_outliers, y=valores_outliers, mode='markers', name=f'Outliers ({nombre})', marker=dict(color=color_datos, size=10)))
            elif visualizacion == 'Histograma':
                fig.add_trace(go.Histogram(x=valores, name=f'{nombre}', marker=dict(color=color_datos)))
                fig.add_trace(go.Histogram(x=valores_outliers, name=f'Outliers ({nombre})', marker=dict(color='red')))
            else:
                fig.add_trace(go.Box(y=valores, name=f'{nombre}', boxpoints='all', jitter=0.3, pointpos=-1.8, marker=dict(color=color_datos)))

            outliers_por_nombre[nombre] = {
                'fechas_outliers': fechas_outliers,
                'valores_outliers': valores_outliers,
            }

        fig.update_layout(title=titulo, xaxis_title='Fecha', yaxis_title=col_name.capitalize(), showlegend=True)
        plot_div=fig.to_html()
        return plot_div, outliers_por_nombre

    datos_fig_html = None
    titulo = None

    if request.method == 'POST':
        form = DeteccionDeOutliersForm(frecuencia=analisis.frecuencia, mostrar_opciones=mostrar_datos, data=request.POST, analisis_uuid=analisis_uuid)
        if form.is_valid():
            umbral = form.cleaned_data['umbral']
            metodo = form.cleaned_data['metodo']
            visualizacion = form.cleaned_data['visualizacion']
            mostrar_datos = form.cleaned_data['mostrar_datos']
            titulo = form.cleaned_data['titulo']

            datos_fig_html, outliers_por_nombre = crear_figura(
                datos_por_nombre[mostrar_datos],
                fechas_por_nombre[mostrar_datos],
                mostrar_datos,
                umbral,
                metodo,
                visualizacion,
                titulo
            )
            all_outliers_empty = all(
                not valores['fechas_outliers'] and not valores['valores_outliers']
                for valores in outliers_por_nombre.values()
            )
            def adjuntar_grafica(grafica):
                if not Grafica.objects.filter(analisis=analisis, tipo_dato="Deteccion de Outliers",imagen_html=grafica):
                    Grafica.objects.create(
                        analisis=analisis,
                        fecha_creacion=datetime.now(),
                        titulo=f"Figura {numero_graficas_por_usuario+1} de Detección de Outliers",
                        tipo_dato="Deteccion de Outliers",
                        imagen_html=grafica
                    )
                    messages.success(request, "Gráfica añadida correctamente")
                else:
                    messages.warning(request, "Hay una grafica igual adjuntada")
            action = request.POST.get('action')
            if action == 'adjuntar_datos_fig':
                adjuntar_grafica(datos_fig_html)
            elif action == 'guardar':
                if DeteccionDeOutliers.objects.filter(titulo=titulo, analisis_id=analisis.pk).exists():
                    messages.warning(request, "Ya existe un estudio con el mismo título.")
                elif all_outliers_empty:
                    messages.warning(request, "No hay ningun outlier para este guardado.")
                elif not DeteccionDeOutliers.objects.filter(analisis=analisis, umbral=umbral, metodo_calculo=metodo, estilo=visualizacion, nombre=mostrar_datos).exists():
                    deteccion_de_outlier = DeteccionDeOutliers.objects.create(
                        analisis=analisis,
                        fecha=datetime.now(),
                        umbral=umbral,
                        metodo_calculo=metodo,
                        estilo=visualizacion,
                        titulo=titulo,
                        nombre=mostrar_datos
                    )
                    messages.success(request, "Detección de outlier añadida correctamente")
                    for nombre, valores in outliers_por_nombre.items():
                        for fecha, valor in zip(valores['fechas_outliers'], valores['valores_outliers']):
                            ResulatadosDeteccionDeOutliers.objects.create(
                                deteccion_de_outlier=deteccion_de_outlier,
                                fecha_dato=fecha,
                                valor=valor,
                                nombre_dato=nombre
                            )
                else:
                    messages.warning(request, "Ya existe un estudio con los mismos datos.")

            return render(request, 'deteccion_de_outliers.html', {
                'form': form,
                'datos_fig': datos_fig_html,
                'titulo': titulo,
                'deteccion_de_outliers_por_nombre': outliers_por_nombre,
                'deteccion_de_outlier': deteccion_de_outlierss,
                'analisis_uuid': analisis_uuid,
                'graficas':graficas_detecciones
            })
    else:
        form = DeteccionDeOutliersForm(frecuencia=analisis.frecuencia, mostrar_opciones=mostrar_datos, analisis_uuid=analisis_uuid)  

    return render(request, 'deteccion_de_outliers.html', {
        'form': form,
        'datos_fig': datos_fig_html,
        'titulo': titulo,
        'deteccion_de_outlier': deteccion_de_outlierss,
        'analisis_uuid': analisis_uuid,
        'graficas':graficas_detecciones
    })

@login_required(login_url="accounts/login/")
def resultados_deteccion_de_outliers(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    graficas_outliers = Grafica.objects.filter(analisis=analisis, tipo_dato="Deteccion de Outliers")
    deteccion_de_outlier = DeteccionDeOutliers.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_detecciones = ResulatadosDeteccionDeOutliers.objects.filter(deteccion_de_outlier__in=deteccion_de_outlier)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_grafica':
            grafica_id = request.POST.get('grafica_id')
            grafica = get_object_or_404(Grafica, id=grafica_id)
            grafica.delete()
        form = DeleteResultsForm(request.POST)
        if form.is_valid():
            titulo_deteccion = form.cleaned_data['titulo']
            try:
                detecciones = DeteccionDeOutliers.objects.get(titulo=titulo_deteccion, analisis=analisis)
                detecciones.delete()
                messages.success(request, f"La detección de outlier '{titulo_deteccion}' y sus resultados han sido eliminados.")
            except DeteccionDeOutliers.DoesNotExist:
                messages.error(request, f"No se encontró ninguna detección de outlier con el título '{titulo_deteccion}'.")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = DeleteResultsForm()

    return render(request, 'resultados_deteccion_de_outliers.html', {
        'analisis': analisis,
        'datos': datos_resultados_detecciones,
        'analisis_uuid': analisis_uuid,
        'graficas': graficas_outliers,
        'form':form
    })

@login_required(login_url="accounts/login/")
def descomposicion_de_series_temporales(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    descomposicion_de_series_temporaless = DescomposicionDeSeriesTemporales.objects.filter(analisis=analisis)
    graficas_descomposiciones = Grafica.objects.filter(analisis=analisis, tipo_dato="Descomposicion de Series Temporales")
    numero_graficas_por_usuario = Grafica.objects.filter(analisis=analisis, tipo_dato="Descomposicion de Series Temporales").count()
    
    datos = DatosPreprocesados.objects.filter(analisis=analisis).order_by('fecha')
    datos_tipo = {
        'precio': datos.filter(precio__isnull=False),
        'consumo': datos.filter(consumo__isnull=False),
        'porcentaje': datos.filter(porcentaje__isnull=False)
    }

    nombres_columnas = [field.name for field in DatosPreprocesados._meta.get_fields()]
    diccionario_datos = {columna: list(datos.values_list(columna, flat=True)) for columna in nombres_columnas}
    mostrar_datos = [columna for columna in ['precio', 'consumo', 'porcentaje'] if any(diccionario_datos[columna])]

    def procesar_datos_por_tipo(datos, tipo):
        resultado_por_nombre = {}
        fechas_por_nombre = {}
        for dato in datos:
            if dato.nombre not in resultado_por_nombre:
                resultado_por_nombre[dato.nombre] = []
                fechas_por_nombre[dato.nombre] = []
            fechas_por_nombre[dato.nombre].append(dato.fecha)
            resultado_por_nombre[dato.nombre].append(getattr(dato, tipo))
        return resultado_por_nombre, fechas_por_nombre

    datos_por_tipo = {tipo: procesar_datos_por_tipo(datos_tipo[tipo], tipo) for tipo in ['precio', 'consumo', 'porcentaje']}
    
    fechas_planas = [fecha for sublist in [fechas for _, fechas in datos_por_tipo['consumo'][1].items() or datos_por_tipo['precio'][1].items() or datos_por_tipo['porcentaje'][1].items()] for fecha in sublist]

    fecha_inicio_por_defecto = min(fechas_planas).date()
    fecha_fin_por_defecto = max(fechas_planas).date()

    form = DescomposicionDeSeriesTemporalesForm(
        mostrar_opciones=mostrar_datos,
        analisis_uuid=analisis_uuid,
        fecha_inicio_por_defecto=fecha_inicio_por_defecto,
        fecha_fin_por_defecto=fecha_fin_por_defecto
    )

    if request.method == 'POST':
        form = DescomposicionDeSeriesTemporalesForm(
            mostrar_opciones=mostrar_datos,
            data=request.POST,
            analisis_uuid=analisis_uuid,
            fecha_inicio_por_defecto=fecha_inicio_por_defecto,
            fecha_fin_por_defecto=fecha_fin_por_defecto
        )
        if form.is_valid():
            titulo = form.cleaned_data['titulo']
            metodo = form.cleaned_data['metodo']
            visualizacion = form.cleaned_data['visualizacion']
            mostrar_datos = form.cleaned_data['mostrar_datos']
            ventana_tendencia = form.cleaned_data['ventana_tendencia']
            ventana_estacionalidad = form.cleaned_data['ventana_estacionalidad']
            suavizado_exponencial = form.cleaned_data['suavizado_exponencial']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']

            datos_filtrados = datos_tipo[mostrar_datos].filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            datos_por_nombre, fechas_por_nombre = procesar_datos_por_tipo(datos_filtrados, mostrar_datos)

            def agregar_traza(fig, x, y, nombre, color, tipo_visualizacion):
                if tipo_visualizacion == 'Simple':
                    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=nombre, line=dict(color=color)))
                elif tipo_visualizacion == 'Grafico de area':
                    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=nombre, fill='tozeroy', line=dict(color=color)))
                elif tipo_visualizacion == 'Grafico de barras':
                    fig.add_trace(go.Bar(x=x, y=y, name=nombre, marker=dict(color=color)))

            def suavizar_serie(serie, factor_suavizado):
                return serie.ewm(alpha=factor_suavizado).mean()

            def descomposicion_serie(datos, fechas, ventana_tendencia, ventana_estacionalidad, suavizado, metodo, color):
                df = pd.DataFrame({'fecha': fechas, mostrar_datos: datos}).set_index('fecha')
                df[mostrar_datos] = suavizar_serie(df[mostrar_datos], suavizado)
                
                if metodo == 'Aditiva':
                    descomposicion = seasonal_decompose(df[mostrar_datos], model='additive', period=ventana_estacionalidad)
                    tendencia = descomposicion.trend.rolling(window=ventana_tendencia, min_periods=1, center=True).mean()
                    estacionalidad = descomposicion.seasonal
                    residuo = descomposicion.resid
                elif metodo == 'Multiplicativa':
                    descomposicion = seasonal_decompose(df[mostrar_datos], model='multiplicative', period=ventana_estacionalidad)
                    tendencia = descomposicion.trend.rolling(window=ventana_tendencia, min_periods=1, center=True).mean()
                    estacionalidad = descomposicion.seasonal
                    residuo = descomposicion.resid

                agregar_traza(fig_datos, fechas, datos, nombre, color, visualizacion)
                agregar_traza(fig_tendencia, fechas, tendencia, f'Tendencia ({nombre})', color, visualizacion)
                agregar_traza(fig_estacionalidad, fechas, estacionalidad, f'Estacionalidad ({nombre})', color, visualizacion)
                agregar_traza(fig_residuo, fechas, residuo, f'Residuo ({nombre})', color, visualizacion)
                
                return tendencia, estacionalidad, residuo

            fig_datos, fig_tendencia, fig_estacionalidad, fig_residuo = go.Figure(), go.Figure(), go.Figure(), go.Figure()
            colores = px.colors.qualitative.Plotly
            descomposicion_resultados = []

            for idx, (nombre, datos) in enumerate(datos_por_nombre.items()):
                fechas = fechas_por_nombre[nombre]
                color = colores[idx % len(colores)]
                tendencia, estacionalidad, residuo = descomposicion_serie(np.array(datos), fechas, ventana_tendencia, ventana_estacionalidad, suavizado_exponencial, metodo, color)
                descomposicion_resultados.append((nombre, fechas, datos, tendencia, estacionalidad, residuo))

            fig_datos.update_layout(title='Datos', xaxis_title='Fecha', yaxis_title=mostrar_datos.capitalize(), showlegend=True)
            fig_tendencia.update_layout(title='Tendencia', xaxis_title='Fecha', yaxis_title=mostrar_datos.capitalize(), showlegend=True)
            fig_estacionalidad.update_layout(title='Estacionalidad', xaxis_title='Fecha', yaxis_title=mostrar_datos.capitalize(), showlegend=True)
            fig_residuo.update_layout(title='Residuo', xaxis_title='Fecha', yaxis_title=mostrar_datos.capitalize(), showlegend=True)
            datos_fig_html, tendencia_fig_html, estacionalidad_fig_html, residuo_fig_html = fig_datos.to_html(), fig_tendencia.to_html(), fig_estacionalidad.to_html(), fig_residuo.to_html()

            def adjuntar_grafica(grafica):
                if not Grafica.objects.filter(analisis=analisis, tipo_dato="Descomposicion de Series Temporales", imagen_html=grafica).exists():
                    Grafica.objects.create(
                        analisis=analisis,
                        fecha_creacion=datetime.now(),
                        titulo=f"Figura {numero_graficas_por_usuario+1} de Descomposición de Series Temporales",
                        tipo_dato="Descomposicion de Series Temporales",
                        imagen_html=grafica
                    )
                    messages.success(request, "Gráfica añadida correctamente")
                else:
                    messages.warning(request, "Hay una gráfica igual adjuntada")

            action = request.POST.get('action')
            if action == 'adjuntar_datos_fig':
                adjuntar_grafica(datos_fig_html)
            elif action == 'adjuntar_tendencia_fig':
                adjuntar_grafica(tendencia_fig_html)
            elif action == 'adjuntar_estacionalidad_fig':
                adjuntar_grafica(estacionalidad_fig_html)
            elif action == 'adjuntar_residuo_fig':
                adjuntar_grafica(residuo_fig_html)
            elif action == 'guardar':
                if DescomposicionDeSeriesTemporales.objects.filter(titulo=titulo, analisis_id=analisis.pk).exists():
                    messages.warning(request, "Ya existe un estudio con el mismo título.")
                elif not DescomposicionDeSeriesTemporales.objects.filter(analisis=analisis, metodo_calculo=metodo, estilo=visualizacion, nombre=mostrar_datos, ventana_tendencia=ventana_tendencia, ventana_estacionalidad=ventana_estacionalidad, suavizado_exponencial=suavizado_exponencial, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin).exists():
                    descomposicion_de_serie_temporal = DescomposicionDeSeriesTemporales.objects.create(
                        analisis=analisis,
                        fecha=datetime.now(),
                        metodo_calculo=metodo,
                        estilo=visualizacion,
                        titulo=titulo,
                        nombre=mostrar_datos,
                        ventana_tendencia=ventana_tendencia,
                        ventana_estacionalidad=ventana_estacionalidad,
                        suavizado_exponencial=suavizado_exponencial,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin
                    )
                    for nombre, fechas, datos, tendencia, estacionalidad, residuo in descomposicion_resultados:
                        for fecha, dato, tend, estac, resid in zip(fechas, datos, tendencia, estacionalidad, residuo):
                            ResultadosDescomposicionDeSeriesTemporales.objects.create(
                                descomposicion=descomposicion_de_serie_temporal,
                                fecha_dato=fecha,
                                nombre_dato=nombre,
                                valor_dato=dato,
                                tendencia=tend,
                                estacionalidad=estac,
                                residuo=resid
                            )
                    messages.success(request, "Se ha guardado exitosamente la descomposición de la serie temporal.")
                else:
                    messages.warning(request, "Ya existe un estudio con los mismos parámetros.")
                
                return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid, 'descomposicion_de_serie_temporal': descomposicion_de_series_temporaless, 'graficas': graficas_descomposiciones})

            return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid, 'datos_fig': datos_fig_html, 'tendencia_fig': tendencia_fig_html, 'estacionalidad_fig': estacionalidad_fig_html, 'residuos_fig': residuo_fig_html, 'descomposicion_de_serie_temporal': descomposicion_de_series_temporaless, 'graficas': graficas_descomposiciones})
    
    return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid, 'descomposicion_de_serie_temporal': descomposicion_de_series_temporaless, 'graficas': graficas_descomposiciones})

@login_required(login_url="accounts/login/")
def resultados_descomposicion_de_series_temporales(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    graficas_descomposiciones = Grafica.objects.filter(analisis=analisis, tipo_dato="Descomposicion de Series Temporales")
    descomposicion = DescomposicionDeSeriesTemporales.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_descomposiciones = ResultadosDescomposicionDeSeriesTemporales.objects.filter(descomposicion__in=descomposicion)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_grafica':
            grafica_id = request.POST.get('grafica_id')
            grafica = get_object_or_404(Grafica, id=grafica_id)
            grafica.delete()
        form = DeleteResultsForm(request.POST)
        if form.is_valid():
            titulo_descomposicion = form.cleaned_data['titulo']
            try:
                series_temporales = DescomposicionDeSeriesTemporales.objects.get(titulo=titulo_descomposicion, analisis=analisis)
                series_temporales.delete()
                messages.success(request, f"La serie temporal '{titulo_descomposicion}' y sus resultados han sido eliminados.")
            except DescomposicionDeSeriesTemporales.DoesNotExist:
                messages.error(request, f"No se encontró ninguna serie temporal con el título '{titulo_descomposicion}'.")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = DeleteResultsForm()

    return render(request, 'resultados_descomposicion_de_series_temporales.html', {
        'analisis': analisis,
        'datos': datos_resultados_descomposiciones,
        'analisis_uuid': analisis_uuid,
        'graficas': graficas_descomposiciones,
        'form':form
    })

def previsualizacion_pdf(request, analisis_uuid):
    analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    datos_autocorrelaciones = ResulatadosAutocorrelacion.objects.select_related('autocorrelacion').filter(autocorrelacion__analisis=analisis)
    datos_outliers = ResulatadosDeteccionDeOutliers.objects.select_related('deteccion_de_outlier').filter(deteccion_de_outlier__analisis=analisis)
    datos_descomposiciones = ResultadosDescomposicionDeSeriesTemporales.objects.select_related('descomposicion').filter(descomposicion__analisis=analisis)
    graficas_autocorrelacion=Grafica.objects.filter(analisis=analisis,tipo_dato="Autocorrelacion")
    graficas_outliers=Grafica.objects.filter(analisis=analisis,tipo_dato="Deteccion de Outliers")
    graficas_descomposiciones=Grafica.objects.filter(analisis=analisis,tipo_dato="Descomposicion de Series Temporales")
    return render(request, 'previsualizacion_pdf.html', {'analisis': analisis, 'datos_autocorrelaciones': datos_autocorrelaciones, 'datos_outliers': datos_outliers, 'datos_descomposiciones': datos_descomposiciones,'graficas_autocorrelacion':graficas_autocorrelacion,'graficas_outliers':graficas_outliers,'graficas_descomposiciones':graficas_descomposiciones})

def descargar_pdf(request, analisis_uuid):
    analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    datos_autocorrelaciones = ResulatadosAutocorrelacion.objects.select_related('autocorrelacion').filter(autocorrelacion__analisis=analisis)
    datos_outliers = ResulatadosDeteccionDeOutliers.objects.select_related('deteccion_de_outlier').filter(deteccion_de_outlier__analisis=analisis)
    datos_descomposiciones = ResultadosDescomposicionDeSeriesTemporales.objects.select_related('descomposicion').filter(descomposicion__analisis=analisis)
    graficas_autocorrelacion=Grafica.objects.filter(analisis=analisis,tipo_dato="Autocorrelacion")
    graficas_outliers=Grafica.objects.filter(analisis=analisis,tipo_dato="Deteccion de Outliers")
    graficas_descomposiciones=Grafica.objects.filter(analisis=analisis,tipo_dato="Descomposicion de Series Temporales")
    
    html_content = render_to_string('pdf.html', {
        'analisis': analisis,
        'datos_autocorrelaciones': datos_autocorrelaciones,
        'datos_outliers': datos_outliers,
        'datos_descomposiciones': datos_descomposiciones,
        'graficas_autocorrelacion':graficas_autocorrelacion,
        'graficas_outliers':graficas_outliers,
        'graficas_descomposiciones':graficas_descomposiciones
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="resultados.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    
    return response