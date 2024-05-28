from django.shortcuts import render, redirect, get_object_or_404

from .forms import AnalisisForm, AutocorrelacionForm, DeteccionDeOutliersForm, DescomposicionDeSeriesTemporalesForm
from .models import Analisis, Autocorrelacion, DatosPreprocesados, ResulatadosAutocorrelacion, DeteccionDeOutliers, ResulatadosDeteccionDeOutliers, DescomposicionDeSeriesTemporales, ResultadosDescomposicionDeSeriesTemporales
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
            analisis.frecuencia = frecuencia
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

    if request.method == 'GET':
        form = AutocorrelacionForm(frecuencia=frecuencia_analisis, mostrar_opciones=mostrar_datos, data=request.GET, analisis_uuid=analisis_uuid)
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

                for nombre, valores in datos_por_nombre.items():
                    fechas = fechas_por_nombre[nombre]
                    color_datos = px.colors.qualitative.Plotly[len(datos_fig.data) % len(px.colors.qualitative.Plotly)]
                    color_autocorrelacion = px.colors.qualitative.Plotly[len(autocorrelation_fig.data) % len(px.colors.qualitative.Plotly)]

                    datos_fig.add_trace(go.Scatter(x=fechas, y=valores, mode='lines', name=nombre, line=dict(color=color_datos)))

                    df = pd.DataFrame({'Fecha': fechas, campo.capitalize(): valores})
                    df['Fecha'] = pd.to_datetime(df['Fecha'])
                    df.set_index('Fecha', inplace=True)

                    if tipo == 'simple':
                        autocorr = sm.tsa.acf(df[campo.capitalize()], nlags=lag, fft=True)
                    elif tipo == 'parcial':
                        metodo_mapping = {'Pearson': 'ols', 'Spearman': 'yw'}
                        autocorr = sm.tsa.pacf(df[campo.capitalize()], nlags=lag, method=metodo_mapping.get(metodo, 'ols'))

                    autocorrelation_fig.add_trace(go.Scatter(
                        x=list(range(lag + 1)), y=autocorr, mode='markers+lines',
                        name=f'Autocorrelación {nombre}', line=dict(color=color_autocorrelacion))
                    )
                    
                    if nombre not in autocorrelaciones_por_nombre:
                        autocorrelaciones_por_nombre[nombre] = []
                    autocorrelaciones_por_nombre[nombre].append(autocorr)

                datos_fig.update_layout(title='Datos', xaxis_title='Fecha', yaxis_title=campo.capitalize())
                autocorrelation_fig.update_layout(title='Autocorrelación', xaxis_title='Lag', yaxis_title='Autocorrelación')

                if visualizacion == 'puntos':
                    autocorrelation_fig.update_traces(mode='markers', marker=dict(color='rgba(255, 0, 0, 0.7)', size=8))

                return datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre

            if mostrar_datos == 'precio':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_precio = create_autocorrelation_fig(precios_por_nombre, fechas_precio_por_nombre, 'precio')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)
            elif mostrar_datos == 'consumo':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_consumo = create_autocorrelation_fig(consumos_por_nombre, fechas_consumo_por_nombre, 'consumo')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)
            elif mostrar_datos == 'porcentaje':
                datos_fig, autocorrelation_fig, autocorrelaciones_por_nombre_porcentaje = create_autocorrelation_fig(porcentajes_por_nombre, fechas_porcentaje_por_nombre, 'porcentaje')
                plot_div = datos_fig.to_html(full_html=False)
                autocorrelation_plot_div = autocorrelation_fig.to_html(full_html=False)

            action = request.GET.get('action')
            if action == 'guardar':
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
                    for nombre_dato, autocorr in autocorrelaciones_por_nombre_precio.items():
                        for i in range(lag):
                            valor_autocorr = autocorr[0][i + 1]
                            ResulatadosAutocorrelacion.objects.create(
                                autocorrelacion=autocorrelacion, lag=i + 1,
                                valor=valor_autocorr, nombre_dato=nombre_dato
                            )
                else:
                    messages.warning(request, "Ya existe una autocorrelación con los mismos datos.")

            return render(request, 'autocorrelacion.html', {
                'form': form, 'plot_div': plot_div,
                'autocorrelation_plot_div': autocorrelation_plot_div,
                'analisis': analisis, 'autocorrelaciones': autocorrelaciones,
                'analisis_uuid': analisis_uuid
            })

    else:
        form = AutocorrelacionForm(frecuencia=frecuencia_analisis, mostrar_opciones=mostrar_datos, analisis_uuid=analisis_uuid)
        form.fields['mostrar_datos'].choices = [(c, c.capitalize()) for c in mostrar_datos]

    return render(request, 'autocorrelacion.html', {'form': form, 'analisis': analisis, 'autocorrelaciones': autocorrelaciones, 'analisis_uuid':analisis_uuid})


@login_required(login_url="accounts/login/")
def resultados_autocorrelacion(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    autocorrelaciones = Autocorrelacion.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_autocorrelacion = ResulatadosAutocorrelacion.objects.filter(autocorrelacion__in=autocorrelaciones)

    if request.method == 'POST':
        dato_ids = request.POST.getlist('dato_ids')
        Autocorrelacion.objects.filter(id__in=dato_ids).delete()
        return redirect('resultados_autocorrelacion', analisis_uuid=analisis_uuid)

    return render(request, 'resultados_autocorrelacion.html', {'analisis': analisis, 'datos': datos_resultados_autocorrelacion, 'analisis_uuid': analisis_uuid})


@login_required(login_url="accounts/login/")
def deteccion_de_outliers(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    datos = list(DatosPreprocesados.objects.filter(analisis=analisis).order_by('fecha'))
    deteccion_de_outlierss = DeteccionDeOutliers.objects.filter(analisis=analisis)
    
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
        return fig.to_html(), outliers_por_nombre

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

            if request.POST.get('action') == 'guardar':
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
            })
    else:
        form = DeteccionDeOutliersForm(frecuencia=analisis.frecuencia, mostrar_opciones=mostrar_datos, analisis_uuid=analisis_uuid)

    return render(request, 'deteccion_de_outliers.html', {
        'form': form,
        'datos_fig': datos_fig_html,
        'titulo': titulo,
        'deteccion_de_outlier': deteccion_de_outlierss,
        'analisis_uuid': analisis_uuid,
    })

@login_required(login_url="accounts/login/")
def resultados_deteccion_de_outliers(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    deteccion_de_outliers = DeteccionDeOutliers.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_deteccion_de_outliers = ResulatadosDeteccionDeOutliers.objects.filter(deteccion_de_outlier__in=deteccion_de_outliers)

    if request.method == 'POST':
        dato_ids = request.POST.getlist('dato_ids')
        DeteccionDeOutliers.objects.filter(id__in=dato_ids).delete()
        return redirect('resultados_deteccion_de_outliers', analisis_uuid=analisis_uuid)

    return render(request, 'resultados_deteccion_de_outliers.html', {'analisis': analisis, 'datos': datos_resultados_deteccion_de_outliers, 'analisis_uuid': analisis_uuid})


@login_required(login_url="accounts/login/")
def descomposicion_de_series_temporales(request, analisis_uuid):
    analisis = get_object_or_404(Analisis, uuid=analisis_uuid, usuario=request.user)
    descomposicion_de_series_temporaless = DescomposicionDeSeriesTemporales.objects.filter(analisis=analisis)
    
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
                descomposicion = sm.tsa.seasonal_decompose(df[mostrar_datos], model=metodo.lower(), period=ventana_estacionalidad)
                tendencia, estacionalidad, residuo = descomposicion.trend, descomposicion.seasonal, descomposicion.resid
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

            if request.POST.get('action') == 'guardar':
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
                
                return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid})

            return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid, 'datos_fig': datos_fig_html, 'tendencia_fig': tendencia_fig_html, 'estacionalidad_fig': estacionalidad_fig_html, 'residuos_fig': residuo_fig_html, 'descomposicion_de_serie_temporal':descomposicion_de_series_temporaless})

    return render(request, 'descomposicion_de_series_temporales.html', {'form': form, 'analisis_uuid': analisis_uuid})



@login_required(login_url="accounts/login/")
def resultados_descomposicion_de_series_temporales(request, analisis_uuid):
    try:
        analisis = Analisis.objects.get(uuid=analisis_uuid, usuario=request.user)
    except Analisis.DoesNotExist:
        raise Http404("El análisis no existe o no tienes permiso para acceder a él.")
    
    descomposicion = DescomposicionDeSeriesTemporales.objects.filter(analisis=analisis).order_by('-fecha')
    datos_resultados_descomposicion_de_series_temporales = ResultadosDescomposicionDeSeriesTemporales.objects.filter(descomposicion__in=descomposicion)

    if request.method == 'POST':
        dato_ids = request.POST.getlist('dato_ids')
        DescomposicionDeSeriesTemporales.objects.filter(id__in=dato_ids).delete()
        return redirect('resultados_descomposicion_de_series_temporales', analisis_uuid=analisis_uuid)

    return render(request, 'resultados_descomposicion_de_series_temporales.html', {'analisis': analisis, 'datos': datos_resultados_descomposicion_de_series_temporales, 'analisis_uuid': analisis_uuid})
