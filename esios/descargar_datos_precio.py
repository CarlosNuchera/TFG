import time
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import sys
import os
import html

# Añade el directorio de acceso a las librerías auxiliares
sys.path.append("Users/carlo/Desktop/djangoproject/esios")  # Corregir la ruta del directorio

# Importa el token de Esios
from pass_esios import token_esios
def catalogo_esios(token):

    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v2+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Cookie': '',
        'Authorization': f'Token token={token}',
        'x-api-key': f'{token}',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    end_point = 'https://api.esios.ree.es/indicators'
    response = requests.get(end_point, headers=headers).json()
    
    # Del resultado en JSON bruto se convierte en pandas, y se eliminan los tags del campo description
    return (pd
            .json_normalize(data=response['indicators'], errors='ignore')
            .assign(description = lambda df_: df_.apply(lambda df__: html.unescape(df__['description']
                                                            .replace('<p>','')
                                                            .replace('</p>','')
                                                            .replace('<b>','')
                                                            .replace('</b>','')), 
                                                  axis=1)
                   )
           )
def download_esios2(token, identificador, fecha_inicio, fecha_fin, time_trunc='day'):

    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v2+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Cookie': '',
        'Authorization': f'Token token={token}',
        'x-api-key': f'{token}',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    end_point = 'https://api.esios.ree.es/indicators'
    url = f'{end_point}/{identificador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&time_trunc={time_trunc}'
    response = requests.get(url, headers=headers).json()
    data = pd.json_normalize(data=response['indicator'], record_path=['values'], meta=['name', 'short_name'], errors='ignore')
    
    return data

# Definir las fechas de inicio y fin
fin = datetime.today().strftime('%Y-%m-%d')
inicio = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')  # 3 años = 1095 días

fecha_inicio = datetime.strptime(inicio, '%Y-%m-%d')
fecha_fin = datetime.strptime(fin, '%Y-%m-%d')

# Obtener el catálogo de Esios
catalogo = catalogo_esios(token_esios)

# Crear la carpeta "generacion_solar" si no existe
carpeta_precio = 'precio'
if not os.path.exists(carpeta_precio):
    os.makedirs(carpeta_precio)

# Descargar datos y guardar en archivos CSV para cada día dentro del rango
for i in catalogo.loc[catalogo['name'].str.contains('ecio'), :].index:
    print(f"{catalogo.loc[i, 'id']} -> {catalogo.loc[i, 'name']}")
    
    # Crear la subcarpeta para el indicador actual
    subcarpeta_nombre = f"{catalogo.loc[i, 'id']}_{catalogo.loc[i, 'name'].replace(' ', '_').replace('/', '').lower()[:75]}"
    ruta_subcarpeta = os.path.join(carpeta_precio, subcarpeta_nombre)
    if not os.path.exists(ruta_subcarpeta):
        os.makedirs(ruta_subcarpeta)
        
    # Iterar sobre cada día dentro del rango
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fecha_actual_str = fecha_actual.strftime('%Y-%m-%d')
        
        # Descargar datos para el día actual
        datos_raw_temp = download_esios2(token_esios, f"{catalogo.loc[i, 'id']}", fecha_actual_str, fecha_actual_str, time_trunc='five_minutes')
        
        # Crear el archivo CSV para guardar los datos
        año_actual = fecha_actual.year
        nombre_archivo = f"{subcarpeta_nombre}_{fecha_actual_str}.csv"
        ruta_archivo = os.path.join(ruta_subcarpeta, str(año_actual), nombre_archivo)
        
        # Crear la carpeta del año si no existe
        if not os.path.exists(os.path.join(ruta_subcarpeta, str(año_actual))):
            os.makedirs(os.path.join(ruta_subcarpeta, str(año_actual)))
        
        # Guardar los datos en el archivo CSV
        datos_raw_temp.to_csv(ruta_archivo, index=False)
        
        # Avanzar al siguiente día
        fecha_actual += timedelta(days=1)
        
