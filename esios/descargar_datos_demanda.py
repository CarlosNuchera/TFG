import os
import json
import pandas as pd
import datetime
import time
import requests
import concurrent.futures

# Directorio para guardar los archivos CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, '..')  # Carpeta paralela a tu aplicación

start_date = "2021-01-01"
end_date = datetime.datetime.now().strftime("%Y-%m-%d")

# Convertir fechas a objetos datetime
start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")

# Definir la plantilla de URL
url_template = "https://apidatos.ree.es/es/datos/demanda/demanda-tiempo-real?start_date={date}T00:00&end_date={date}T23:59&time_trunc=hour"

def download_and_process_demand_data(date):
    current_url = url_template.format(date=date)
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

    # Organizar por año
    year = date.split("-")[0]
    output_folder = os.path.join(data_folder, "demanda", year)
    os.makedirs(output_folder, exist_ok=True)

    # Guardar el archivo CSV
    output_csv = os.path.join(output_folder, f"demand_{date}.csv")
    df.to_csv(output_csv, index=False)

    print(f"Datos procesados y guardados para la fecha: {date}")

# Utilizar ThreadPoolExecutor para descargar y procesar datos en paralelo
with concurrent.futures.ThreadPoolExecutor() as executor:
    date_range = [start_datetime + datetime.timedelta(days=x) for x in range((end_datetime - start_datetime).days + 1)]
    executor.map(download_and_process_demand_data, (date.strftime("%Y-%m-%d") for date in date_range))

print("Proceso completado. Todos los datos descargados y procesados.")
