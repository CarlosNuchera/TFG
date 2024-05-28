import pandas as pd
import sys
import os


sys.path.append("Users/carlo/Desktop/djangoproject/esios")

from pass_esios import token_esios

script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, '..')

def download_gas(year):
    path = f'https://www.mibgas.es/en/file-access/MIBGAS_Data_{year}.xlsx?path=AGNO_{year}/XLS'
    gas_data = (pd.read_excel(path, sheet_name='Trading Data PVB&VTP', usecols=['Trading day', 'Product', 'Reference Price\n[EUR/MWh]']).
       query("Product=='GDAES_D+1'").
       rename(columns={'Trading day':'Fecha', 'Product':'Nombre', 'Reference Price\n[EUR/MWh]':'Precio'}).
       sort_values('Fecha', ascending=True).
       reset_index(drop=True)
    )

    gas_data = gas_data.dropna()

    output_folder = os.path.join(data_folder, 'gas')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    csv_filename = os.path.join(output_folder, f'{year}_gas_data.csv')
    gas_data.to_csv(csv_filename, index=False)
    print(f"Datos Gas procesados y guardados para el año {año}")
    return gas_data
año=2024
gas = download_gas(año)
