import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime,timedelta,date
import sys



import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.dates import (YEARLY, MONTHLY, DateFormatter, WeekdayLocator, MonthLocator,DayLocator,
                              rrulewrapper, RRuleLocator, drange, num2date, date2num)
import matplotlib.patches as mpatches
import matplotlib.units as munits
from matplotlib.dates import num2date, date2num

import seaborn as sns


import html

sys.path.append("Users\carlo\Desktop\djangoproject\esios") # directorio de acceso a librerías auxiliares

from pass_esios import token_esios #importo mi token de esios, añadan su propia clave en su versión

def catalogo_esios(token):
    """
    Descarga todos los identificadores y su descripcion de esios
    
    Parameters
    ----------
    token : str
        El token de esios necesario para realizar las llamadas al API
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con el catalogo de los id de la API
    
    """
    
    
    headers = {'Accept':'application/json; application/vnd.esios-api-v2+json', 
        'Content-Type':'application/json', 
        'Host':'api.esios.ree.es', 
        'Cookie' : '', 
        'Authorization':f'Token token={token}', 
        'x-api-key': f'{token}',  
        'Cache-Control': 'no-cache', 
        'Pragma': 'no-cache' 
        } 

    end_point = 'https://api.esios.ree.es/indicators'
    response = requests.get(end_point, headers=headers).json()
    
    #del resultado en json bruto se convierte en pandas, y se eliminan los tags del campo description

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

def download_esios(token,indicadores,fecha_inicio,fecha_fin,time_trunc='day'):
    """
    Descarga datos esios desde un determinado identidficador y entre dos fechas
    
    Parameters
    ----------
    token : str
        El token de esios necesario para realizar las llamadas al API
    
    indicadores : list
        Lista con los strings de los indicadores de los que queremos bajar datos
        
    fecha_inicio : str
        Fecha con formato %Y-%M-%d, que indica la fecha desde la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
    
    fecha_fin : str
        Fecha con formato %Y-%M-%d, que indica la fecha hasta la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
        
    time_trunc : str, optional
        Campo adicional que nos permite elegir la granularidad de los datos que queremos bajar.
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con los datos solicitados
    
    """
    
    # preparamos la cabecera a insertar en la llamada. Vease la necesidad de disponer el token de esios
    
    headers = {'Accept':'application/json; application/vnd.esios-api-v2+json', 
            'Content-Type':'application/json', 
            'Host':'api.esios.ree.es', 
            'Cookie' : '', 
            'Authorization':f'Token token={token}', 
            'x-api-key': f'{token}',  
            'Cache-Control': 'no-cache', 
            'Pragma': 'no-cache' 
            }
    
    # preparamos la url básica a la que se le añadiran los campos necesarios 
    
    end_point = 'https://api.esios.ree.es/indicators'
    
    # El procedimiento es sencillo: 
    # a) por cada uno de los indicadores configuraremos la url, según las indicaciones de la documentación.
    # b) Hacemos la llamada y recogemos los datos en formato json.
    # c) Añadimos la información a una lista
    
    lista=[]

    for indicador in indicadores:
        url = f'{end_point}/{indicador}?start_date={fecha_inicio}T00:00&\
        end_date={fecha_fin}T23:59&time_trunc={time_trunc}'
        print (url)
        response = requests.get(url, headers=headers).json()
        lista.append(pd.json_normalize(data=response['indicator'], record_path=['values'], meta=['name','short_name'], errors='ignore'))

    # Devolvemos como salida de la función un df fruto de la concatenación de los elemenos de la lista
    # Este procedimiento, con una sola concatenación al final, es mucho más eficiente que hacer múltiples 
    # concatenaciones.
    
    return pd.concat(lista, ignore_index=True )

def download_ree(indicador,fecha_inicio,fecha_fin,time_trunc='day'):
    """
    Descarga datos desde apidatos.ree.es entre dos fechas determinadas 
    
    Parameters
    ----------
    
    indicador : str
        Texto con el indicador del end point del que queremo bajar la información
        
    fecha_inicio : str
        Fecha con formato %Y-%M-%d, que indica la fecha desde la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
    
    fecha_fin : str
        Fecha con formato %Y-%M-%d, que indica la fecha hasta la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
        
    time_trunc : str, optional
        Campo adicional que nos permite elegir la granularidad de los datos que queremos bajar.
        Hour, Day, Month...dependiendo del end point se aplicará o no esta orden
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con los datos solicitados
    
    """
    
    
    headers = {'Accept': 'application/json',
               'Content-Type': 'applic<ation/json',
               'Host': 'apidatos.ree.es'}
    
    end_point = 'https://apidatos.ree.es/es/datos/'
    
    lista=[]
    url = f'{end_point}{indicador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&\
    time_trunc={time_trunc}'
    print (url)
    
    response = requests.get(url, headers=headers).json()
    
    return pd.json_normalize(data=response['included'], 
                                   record_path=['attributes','values'], 
                                   meta=['type',['attributes','type' ]], 
                                   errors='ignore')

def download_gas(year):
    """
    Descarga datos de precio de gas desde MIBGAS para GDAES
    
    Parameters
    ----------
    year : str
        Indicamos el año del que nos queremos bajar los datos de precio de gas PVB
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con los datos solicitados, columnas Fecha , Producto y Precio
    
    """
    
    path = f'https://www.mibgas.es/en/file-access/MIBGAS_Data_{year}.xlsx?path=AGNO_{year}/XLS'
    return (pd.read_excel(path,sheet_name='Trading Data PVB&VTP',usecols=['Trading day','Product','Daily Reference Price\n[EUR/MWh]']).
       query("Product=='GDAES_D+1'").
       rename(columns={'Trading day':'fecha','Product':'Producto','Daily Reference Price\n[EUR/MWh]':'precio'}).
       sort_values('fecha',ascending=True).
       reset_index(drop=True)
      )

def download_gas_rd(year):
    """
    Descarga datos de precio de gas desde MIBGAS para compensación segñun RD10/2022
    
    Parameters
    ----------
    YEAR : str
        Indicamos el año del que nos queremos bajar los datos de precio de gas de RD10/22
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con los datos solicitados, columnas Fecha , Producto y Precio
    
    """
    
    path = f'https://www.mibgas.es/en/file-access/MIBGAS_Data_{year}.xlsx?path=AGNO_{year}/XLS'
    return (pd.read_excel(path,sheet_name='PGN_RD_10_2022',
                          usecols=['Date','PGN Price\n[EUR/MWh]']).
       rename(columns={'Date':'fecha','PGN Price\n[EUR/MWh]':'precio'}).
       sort_values('fecha',ascending=True).
       reset_index(drop=True)
      )

catalogo = catalogo_esios(token_esios)
catalogo.head()

for i in catalogo.loc[catalogo['name'].str.contains('uclear'),:].index:
       print (f"{catalogo.loc[i,'id']} -> {catalogo.loc[i,'name']}")

identificadores = [544,545,1293]

for id in identificadores:
 print(f"{catalogo.loc[catalogo['id']==id,'id'].values[0]}-->{catalogo.loc[catalogo['id']==id,'name'].values[0]}\
-{catalogo.loc[catalogo['id']==id,'description'].values[0]}"+'\n')
 
fin = datetime.today().strftime('%Y-%m-%d')  # string con la fecha de hoy en el formato requerido por funcion
inicio = (datetime.today()-timedelta(days=2)).strftime('%Y-%m-%d')

datos_raw = download_esios(token_esios, identificadores, inicio, fin, time_trunc='five_minutes' )

print(datos_raw)

datos_raw['short_name'].unique()

datos = (datos_raw
         .assign(fecha=lambda df_: pd #formateamos campo fecha, desde un str con diferencia horaria a un naive
                      .to_datetime(df_['datetime'],utc=True)  # con la fecha local
                      .dt
                      .tz_convert('Europe/Madrid')
                      .dt
                      .tz_localize(None)
                ) 
             .drop(['datetime','datetime_utc','tz_time','geo_id','geo_name','short_name'],
                   axis=1) #eliminamos campos
             .loc[:,['fecha','name','value']]
             )
        
print(datos)

#PRIMERA GRÁFICA

titulo = f'Demanda prevista vs Demanda programada vs Demanda real'
fuente = 'https://www.esios.ree.es'
autor='@walyt'

f, ax = plt.subplots(figsize=(12,6))
sns.set_style(style='white')
paleta = ['violet','green','orange']

sns.lineplot(
     data=datos,
     x='fecha', 
     y='value',
     errorbar=None,
     estimator=sum,
     hue='name',
     ax=ax,
     linewidth=1.5,
     palette=paleta
     )

ax.legend(loc=7,fontsize=18)

ax.xaxis.set_tick_params(labelsize=14,width=0,rotation=0,pad=0)
ax.yaxis.set_tick_params(labelsize=18,width=0,rotation=0,pad=-0)

ax.set_ylim(bottom=9)
ax.set_xlabel('')
ax.set_ylabel('')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,x:f'{v/1000:,.0f} GW')) # los datos están en MW
ax.set_xticks(datos['fecha'].unique()[::72]) #6 horas de espaciado en eje X son 6*12 periodos de 5 min
ax.set_xticklabels([pd.to_datetime(i).strftime('%H:%M\n%d-%b') for i in datos['fecha'].unique()[::72]])
sns.despine(left=True, bottom=True)
ax.grid(True)

#Título
ax.set_title('{}'.format(titulo),fontsize=24,color='black',pad=50,y=1.0)

#Indicaciones inferior
f.text(0.0, 0.0, 'Fuente de datos: {}'.format(fuente), horizontalalignment='left',
             verticalalignment='center', fontsize=20,color='black')
f.text(0.7,0.00,'{}'.format(autor),
                 verticalalignment='center',fontsize=20,horizontalalignment='left',color='black')

#SEGUNDA GRÁFICA

fin = datetime.today().strftime('%Y-%m-%d')  # string con la fecha de hoy en el formato requerido por funcion
inicio = (datetime.today()-timedelta(days=7)).strftime('%Y-%m-%d')
identificador = 'generacion/estructura-generacion'

raw = download_ree(identificador,inicio,fin)

print(raw.sample())

print(raw.dtypes)

generacion = (raw
              .assign(fecha=lambda df_: pd
                      .to_datetime(df_['datetime'],utc=True)
                      .dt
                      .tz_convert('Europe/Madrid')
                      .dt
                      .tz_localize(None)
                      )
              .query('type in ["Nuclear","Solar fotovoltaica","Eólica","Hidráulica"]')
              .drop(['attributes.type','datetime','percentage'],axis=1)
              .rename(columns={'value':'valor','type':'tipo','value':'generacion'})[['fecha','tipo','generacion']]
            )

print(generacion)

titulo = f'Evolucion de diferentes tecnologias de generacion'
fuente = 'https://www.ree.es/es/apidatos'
autor='@walyt'

f, ax = plt.subplots(figsize=(12,6))
sns.set_style(style='white')
paleta = ['blue','violet','green','orange']

sns.barplot(
     data=generacion,
     x='fecha', 
     y='generacion',
     errorbar=None,
     estimator=sum,
     hue='tipo',
     ax=ax,
     palette=paleta
     )

ax.legend(loc='center left',fontsize=18,bbox_to_anchor=(1, 0.5))

ax.xaxis.set_tick_params(labelsize=14,width=0,rotation=0,pad=0)
ax.yaxis.set_tick_params(labelsize=18,width=0,rotation=0,pad=-0)

ax.set_ylim(bottom=0)
ax.set_xlabel('')
ax.set_ylabel('')

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,x:f'{v/1000:,.0f} GW')) # los datos están en MW

ax.set_xticklabels([i.strftime('%d-%b') for i in pd.to_datetime(generacion['fecha'].unique())])

sns.despine(left=True, bottom=True)
ax.grid(True)

#Título
ax.set_title('{}'.format(titulo),fontsize=24,color='black',pad=50,y=1.0)

#Indicaciones inferior
f.text(0.0, 0.0, 'Fuente de datos: {}'.format(fuente), horizontalalignment='left',
             verticalalignment='center', fontsize=20,color='black')
f.text(0.7,0.00,'{}'.format(autor),
                 verticalalignment='center',fontsize=20,horizontalalignment='left',color='black')

gas = download_gas(2022)

print(gas.head())

#TERCERA GRÁFICA

titulo = f'Evolucion precio de gas en Mibgas'
fuente = 'MIBGAS'
autor='@walyt'

f, ax = plt.subplots(figsize=(12,6))
sns.set_style(style='white')
paleta = ['blue','violet','green','orange']

sns.scatterplot(
     data=gas.loc[gas['fecha']>='2022-06-01',:],
     x='fecha', 
     y='precio',
     #ci=None,
     #estimator=sum,
     ax=ax,
     palette=paleta
     )

ax.legend(loc='center left',fontsize=18,bbox_to_anchor=(1, 0.5))

ax.xaxis.set_tick_params(labelsize=14,width=0,rotation=0,pad=0)
ax.yaxis.set_tick_params(labelsize=18,width=0,rotation=0,pad=-0)

ax.set_ylim(bottom=0)
ax.set_xlabel('')
ax.set_ylabel('')

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,x:f'{v:,.1f} €')) # los datos están en MW

#ax.set_xticklabels([i.strftime('%-d-%b') for i in pd.to_datetime(generacion['fecha'].unique())])

sns.despine(left=True, bottom=True)
ax.grid(True)

#Título
ax.set_title('{}'.format(titulo),fontsize=24,color='black',pad=50,y=1.0)

#Indicaciones inferior
f.text(0.0, 0.0, 'Fuente de datos: {}'.format(fuente), horizontalalignment='left',
             verticalalignment='center', fontsize=20,color='black')
f.text(0.7,0.00,'{}'.format(autor),
                 verticalalignment='center',fontsize=20,horizontalalignment='left',color='black')

gas_rd = download_gas_rd(2022)

print(gas_rd)

#CUARTA GRÁFICA

titulo = f'Evolucion precio de compensación de gas según RD10/2022'
fuente = 'MIBGAS'
autor='@walyt'

f, ax = plt.subplots(figsize=(12,6))
sns.set_style(style='white')
paleta = ['blue','violet','green','orange']

sns.scatterplot(
     data=gas_rd,
     x='fecha', 
     y='precio',
     #ci=None,
     #estimator=sum,
     ax=ax,
     palette=paleta
     )

ax.legend(loc='center left',fontsize=18,bbox_to_anchor=(1, 0.5))

ax.xaxis.set_tick_params(labelsize=14,width=0,rotation=0,pad=0)
ax.yaxis.set_tick_params(labelsize=18,width=0,rotation=0,pad=-0)

ax.set_ylim(bottom=0)
ax.set_xlabel('')
ax.set_ylabel('')

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,x:f'{v:,.0f} €')) # los datos están en MW

#ax.set_xticklabels([i.strftime('%-d-%b') for i in pd.to_datetime(generacion['fecha'].unique())])

sns.despine(left=True, bottom=True)
ax.grid(True)

#Título
ax.set_title('{}'.format(titulo),fontsize=24,color='black',pad=50,y=1.0)

#Indicaciones inferior
f.text(0.0, 0.0, 'Fuente de datos: {}'.format(fuente), horizontalalignment='left',
             verticalalignment='center', fontsize=20,color='black')
f.text(0.7,0.00,'{}'.format(autor),
                 verticalalignment='center',fontsize=20,horizontalalignment='left',color='black')

#QUINTA GRÁFICA

titulo = f'Evolucion precio de compensación de gas según RD10/2022'
fuente = 'MIBGAS'
autor='@walyt'

f, ax = plt.subplots(figsize=(12,6))
sns.set_style(style='white')

sns.lineplot(
     data=gas_rd,
     x='fecha', 
     y='precio',
     ci=None,
     estimator=sum,
     ax=ax,
    color='blue',label='RD10/22'
     )

sns.lineplot(
     data=gas.loc[gas['fecha']>='2022-06-14',:],
     x='fecha', 
     y='precio',
     ci=None,
     estimator=sum,
     ax=ax,
    color='red',label='GDAES'
     )

ax.legend(loc='center left',fontsize=18,bbox_to_anchor=(1, 0.5))

ax.xaxis.set_tick_params(labelsize=14,width=0,rotation=0,pad=0)
ax.yaxis.set_tick_params(labelsize=18,width=0,rotation=0,pad=-0)

ax.set_ylim(bottom=0)
ax.set_xlabel('')
ax.set_ylabel('')

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,x:f'{v:,.0f} €')) # los datos están en MW

#ax.set_xticklabels([i.strftime('%-d-%b') for i in pd.to_datetime(generacion['fecha'].unique())])

sns.despine(left=True, bottom=True)
ax.grid(True)

#Título
ax.set_title('{}'.format(titulo),fontsize=24,color='black',pad=50,y=1.0)

#Indicaciones inferior
f.text(0.0, 0.0, 'Fuente de datos: {}'.format(fuente), horizontalalignment='left',
             verticalalignment='center', fontsize=20,color='black')
f.text(0.7,0.00,'{}'.format(autor),
                 verticalalignment='center',fontsize=20,horizontalalignment='left',color='black')

plt.tight_layout()  # Ajusta automáticamente la disposición de las gráficas para que no se superpongan
plt.show()

for i in catalogo.loc[catalogo['name'].str.contains('ecio'),:].index:
       print (f"{catalogo.loc[i,'id']} -> {catalogo.loc[i,'name']}")