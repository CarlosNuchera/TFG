import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import sys
import os
import html

sys.path.append(r"Users\carlo\Desktop\djangoproject\esios")  # Usando raw string para evitar escape de caracteres

from pass_esios import token_esios

# Directorio para guardar los archivos CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, '..')  # Carpeta paralela a tu aplicación


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

    return (pd.json_normalize(data=response['indicators'], errors='ignore')
            .assign(description=lambda df_: df_.apply(lambda df__: html.unescape(df__['description']
                                                                                 .replace('<p>', '')
                                                                                 .replace('</p>', '')
                                                                                 .replace('<b>', '')
                                                                                 .replace('</b>', '')),
                                                       axis=1)))

def download_esios(token, indicadores, fecha_inicio, fecha_fin, time_trunc='day'):
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

    lista = []

    for indicador in indicadores:
        url = f'{end_point}/{indicador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&time_trunc={time_trunc}'
        response = requests.get(url, headers=headers).json()
        lista.append(pd.json_normalize(data=response['indicator'], record_path=['values'], meta=['name', 'short_name'], errors='ignore'))

    return pd.concat(lista, ignore_index=True)


catalogo = catalogo_esios(token_esios)

identificadores = [600, 612, 613, 614, 615, 616, 617, 618]

hoy = datetime.today()

# Obtener la fecha de inicio y fin para los últimos tres años
start_date = "2021-01-01"
fin = datetime.today().strftime('%Y-%m-%d')

fecha_inicio = datetime.strptime(start_date, '%Y-%m-%d')
fecha_fin = datetime.strptime(fin, '%Y-%m-%d')

datos_raw = download_esios(token_esios, identificadores, start_date, fin, time_trunc='day')

datos_raw_espana = datos_raw[datos_raw['geo_name'] == 'España']
datos = (datos_raw_espana
         .assign(fecha=lambda df_: pd 
                      .to_datetime(df_['datetime'],utc=True)  
                      .dt
                      .tz_convert('Europe/Madrid')
                      .dt
                      .tz_localize(None)
                ) 
             .drop(['datetime','datetime_utc','tz_time','geo_id','geo_name','short_name'],
                   axis=1)
             .loc[:,['fecha','name','value']]
             .rename(columns={'fecha': 'Fecha', 'name': 'Nombre', 'value': 'Precio'})
             )
print(datos.head())
for date in datos['Fecha'].dt.year.unique():
    subcarpeta_anio = os.path.join(data_folder, 'indicadores', str(date))
    if not os.path.exists(subcarpeta_anio):
        os.makedirs(subcarpeta_anio)

    datos_indicador = datos[datos['Fecha'].dt.year == date]
    file_path = os.path.join(subcarpeta_anio, f'datos_precio_{date}.csv')
    datos_indicador.to_csv(file_path, index=False)
    print(f"Los datos del año {date} se han guardado correctamente en: {file_path}")
