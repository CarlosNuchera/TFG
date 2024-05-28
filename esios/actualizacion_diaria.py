import os
import json
import pandas as pd
import datetime
import requests
import pandas as pd
import numpy as np
import requests
import sys
import os
import html

sys.path.append(r"Users\carlo\Desktop\djangoproject\esios")  # Usando raw string para evitar escape de caracteres

from pass_esios import token_esios

# Directorio para guardar los archivos CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, '..')  # Carpeta paralela a tu aplicación

def download_and_process_demand_data():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.datetime.now().strftime("%Y")
    current_url = f"https://apidatos.ree.es/es/datos/demanda/demanda-tiempo-real?start_date={today_date}T00:00&end_date={today_date}T23:59&time_trunc=hour"
    response = requests.get(current_url)
    data = response.json()

    types = []
    dates = []
    percentages = []
    values = []

    for item in data["included"]:
        if "values" in item["attributes"] and item["type"] != "Demanda peninsular en tiempo real":
            for value_item in item["attributes"]["values"]:
                types.append(item["type"])
                dates.append(value_item["datetime"])
                percentages.append(value_item["percentage"])
                values.append(value_item["value"])

    df = pd.DataFrame({"Nombre": types, "Fecha": dates, "Porcentaje": percentages, "Consumo": values})
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    # Guardar el archivo CSV en la carpeta del año correspondiente
    output_folder = os.path.join(data_folder,"demanda", current_year)
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, f"demand_{today_date}.csv")
    df.to_csv(output_csv, index=False)

    print(f"Datos Demanda procesados y guardados para la fecha de hoy: {today_date}")

# Ejecutar la función para descargar y procesar los datos del día de hoy
download_and_process_demand_data()



def download_gas(year):
    path = f'https://www.mibgas.es/en/file-access/MIBGAS_Data_{year}.xlsx?path=AGNO_{year}/XLS'
    gas_data = (pd.read_excel(path, sheet_name='Trading Data PVB&VTP', usecols=['Trading day', 'Product', 'Reference Price\n[EUR/MWh]']). #Debemos cambiar Daily Reference Price -> Reference Price para los datos a partir de 2022
       query("Product=='GDAES_D+1'").
       rename(columns={'Trading day':'Fecha', 'Product':'Nombre', 'Reference Price\n[EUR/MWh]':'Precio'}).
       sort_values('Fecha', ascending=True).
       reset_index(drop=True)
    )
    
    # Eliminar filas con valores nulos en cualquier columna
    gas_data = gas_data.dropna()
    
    output_folder = os.path.join(data_folder, 'gas')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    csv_filename = os.path.join(output_folder, f'{year}_gas_data.csv')
    gas_data.to_csv(csv_filename, index=False)
    print(f"Datos Gas procesados y guardados para el año {datetime.datetime.now().year}")
    return gas_data
gas = download_gas(datetime.datetime.now().year)


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

hoy = datetime.datetime.today()

# Obtener la fecha de inicio y fin para los últimos tres años
start_date = datetime.datetime(datetime.datetime.now().year, 1, 1).strftime('%Y-%m-%d')
fin = datetime.datetime.today().strftime('%Y-%m-%d')

fecha_inicio = datetime.datetime.strptime(start_date, '%Y-%m-%d')
fecha_fin = datetime.datetime.strptime(fin, '%Y-%m-%d')

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
for date in datos['Fecha'].dt.year.unique():
    subcarpeta_anio = os.path.join(data_folder, 'indicadores', str(date))
    if not os.path.exists(subcarpeta_anio):
        os.makedirs(subcarpeta_anio)

    datos_indicador = datos[datos['Fecha'].dt.year == date]
    file_path = os.path.join(subcarpeta_anio, f'datos_precio_{date}.csv')
    datos_indicador.to_csv(file_path, index=False)
    print(f"Datos Precio procesados y guardados para el año: {date}")



def download_ree(indicador, fecha_inicio, fecha_fin, time_trunc='day'):
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Host': 'apidatos.ree.es'}
    
    end_point = 'https://apidatos.ree.es/es/datos/'
    lista = []
    
    # Construir la URL para la solicitud
    url = f'{end_point}{indicador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&time_trunc={time_trunc}'
        
    # Realizar la solicitud y agregar los datos a la lista
    response = requests.get(url, headers=headers).json()
    lista.append(response)
    
    # Combinar los resultados de todas las solicitudes en un solo DataFrame
    combined_data = []
    for response in lista:
        if 'included' in response:
            combined_data.extend(response['included'])
    
    return pd.json_normalize(data=combined_data, 
                             record_path=['attributes','values'], 
                             meta=['type',['attributes','type' ]], 
                             errors='ignore')

fin = datetime.datetime.today().strftime("%Y-%m-%d")
inicio = datetime.datetime(datetime.datetime.now().year, 1, 1).strftime('%Y-%m-%d')
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
    print(f"Datos Generaciones procesados y guardados para el año {datetime.datetime.now().year}")

