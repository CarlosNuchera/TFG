import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta, date
import sys
import os

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.dates import (YEARLY, MONTHLY, DateFormatter, WeekdayLocator, MonthLocator, DayLocator,
                              rrulewrapper, RRuleLocator, drange, num2date, date2num)
import matplotlib.patches as mpatches
import matplotlib.units as munits
from matplotlib.dates import num2date, date2num

import seaborn as sns

import html

sys.path.append("Users/carlo/Desktop/djangoproject/esios")

from pass_esios import token_esios

año=2022

def todos_los_datos_gas_rd(year):
    path = f'https://www.mibgas.es/en/file-access/MIBGAS_Data_{year}.xlsx?path=AGNO_{year}/XLS'
    excel_file = pd.ExcelFile(path)  # Abrir el archivo Excel
    sheet_names = excel_file.sheet_names  # Obtener todos los nombres de las hojas

    # Mostrar todos los nombres de las hojas disponibles
    print("Nombres de las hojas disponibles:")
    for sheet_name in sheet_names:
        print(sheet_name)

todos_los_datos_gas_rd(año)
