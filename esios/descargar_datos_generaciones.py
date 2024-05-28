import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from pytz import timezone

# Directorio para guardar los archivos CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, '..')  # Carpeta paralela a tu aplicación


def download_ree(indicador, fecha_inicio, fecha_fin, time_trunc='day'):
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Host': 'apidatos.ree.es'}
    
    end_point = 'https://apidatos.ree.es/es/datos/'
    lista = []
    
    # Dividir el rango de fechas en segmentos de máximo 366 días
    delta = timedelta(days=366)
    start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    end_date = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    while start_date <= end_date:
        # Definir las fechas límite para esta solicitud
        chunk_end_date = min(start_date + delta, end_date)
        
        # Convertir fechas a la zona horaria adecuada
        start_date_str = start_date.astimezone(timezone('Europe/Madrid')).strftime("%Y-%m-%d")
        chunk_end_date_str = chunk_end_date.astimezone(timezone('Europe/Madrid')).strftime("%Y-%m-%d")
        
        # Construir la URL para esta solicitud
        url = f'{end_point}{indicador}?start_date={start_date_str}T00:00&end_date={chunk_end_date_str}T23:59&time_trunc={time_trunc}'
        print(url)
        
        # Realizar la solicitud y agregar los datos a la lista
        response = requests.get(url, headers=headers).json()
        lista.append(response)
        
        # Actualizar la fecha de inicio para la próxima solicitud
        start_date = chunk_end_date + timedelta(days=1)
    
    # Combinar los resultados de todas las solicitudes en un solo DataFrame
    combined_data = []
    for response in lista:
        if 'included' in response:
            combined_data.extend(response['included'])
    
    return pd.json_normalize(data=combined_data, 
                             record_path=['attributes','values'], 
                             meta=['type',['attributes','type' ]], 
                             errors='ignore')

fin = datetime.today().strftime('%Y-%m-%d')
inicio = "2021-01-01"
identificador = 'generacion/estructura-generacion'

raw = download_ree(identificador, inicio, fin)
datos = (raw
              .assign(fecha=lambda df_: pd
                      .to_datetime(df_['datetime'], utc=True)
                      .dt
                      .tz_convert('Europe/Madrid')
                      .dt
                      .tz_localize(None)
                      )
              .query('type in ["Nuclear","Solar fotovoltaica","Eólica","Hidráulica"]')
              .drop(['attributes.type', 'datetime', 'percentage'],
                     axis=1).loc[:,['fecha', 'type', 'value']]
              .rename(columns={'fecha': 'Fecha', 'type': 'Nombre', 'value': 'Consumo'})
              )

for year, datos_year in datos.groupby(datos['Fecha'].dt.year):
    folder_path = os.path.join(data_folder,'generaciones', str(year))
    os.makedirs(folder_path, exist_ok=True)
    file_name = f'generacion_{year}.csv'
    datos_year.to_csv(os.path.join(folder_path, file_name), index=False)

print(datos)
