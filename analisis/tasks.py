from celery import shared_task
import math
from datetime import timedelta
from django.db.models import Avg
from .models import Analisis, DatosPreprocesados, Datos
from datetime import timedelta
@shared_task
def procesar_datos_en_segundo_plano(analisis_id, tipos_seleccionados):
    try:
        print("Iniciando tarea...")
        analisis=Analisis.objects.get(id=analisis_id)
        frecuencia=analisis.frecuencia
        datos_coincidentes = Datos.objects.filter(tipo_dato__in=tipos_seleccionados)
        contador=0

        fechas_por_nombre = {}
        datos_por_nombre = {}
        for dato in datos_coincidentes:
            if dato.nombre not in fechas_por_nombre and dato.nombre not in datos_por_nombre:
                fechas_por_nombre[dato.nombre] = []
                datos_por_nombre[dato.nombre] = []
            fechas_por_nombre[dato.nombre].append(dato.fecha)
            datos_por_nombre[dato.nombre].append(dato)

        frecuencias_por_nombre = {}
        for nombre, fechas in fechas_por_nombre.items():
            if len(fechas) >= 2:
                fecha1 = fechas[0]
                fecha2 = fechas[1]
                resta = fecha2 - fecha1
                diferencia_minutos = resta.total_seconds() / 60
                frecuencias_por_nombre[nombre] = round(diferencia_minutos)
                print("FECHA 1: "+ str(fecha1))
                print("FECHA 2: " + str(fecha2))

        print("FRECUENCIAS POR NOMBRE: "+ str(frecuencias_por_nombre))

        veces_a_agregar_por_nombre = {}
        for nombre, frecuencia_datos in frecuencias_por_nombre.items():
            print("FRECUENCIA DE LOS DATOS: "+ str(frecuencia_datos))
            if frecuencia == "10 minutos" and frecuencia_datos != 10:
                veces_a_agregar_por_nombre[nombre] = math.ceil(frecuencia_datos / 10)
            elif frecuencia == "horas" and frecuencia_datos != 60:
                veces_a_agregar_por_nombre[nombre] = math.ceil(frecuencia_datos / 60)
            elif frecuencia == "dias" and frecuencia_datos != 1440:
                veces_a_agregar_por_nombre[nombre] = math.ceil(frecuencia_datos / 1440)
            else:
                veces_a_agregar_por_nombre[nombre] = 1
        print("VECES A AGREGAR POR NOMBRE: " + str(veces_a_agregar_por_nombre))

        datos_por_iteraciones = []

        for nombre, veces_a_agregar in veces_a_agregar_por_nombre.items():
            datos_por_iteraciones.append((veces_a_agregar, datos_por_nombre[nombre]))
            
        for iteraciones, datos in datos_por_iteraciones:
            analisis.tipos_de_dato.add(*datos_coincidentes)
            for i in range(iteraciones):
                for dato in datos:
                    if frecuencia_datos < 10:
                        if frecuencia=="10 minutos":
                            datos_cada_diez_minutos = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day, fecha__hour=dato.fecha.hour, fecha__minute__in=[0, 10, 20, 30, 40, 50])
                            nuevo_precio = datos_cada_diez_minutos.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_cada_diez_minutos.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_cada_diez_minutos.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(minutes=i*10)
                            contador+=1

                        elif frecuencia == "horas": 
                            datos_por_hora = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day, fecha__hour=dato.fecha.hour)
                            nuevo_precio = datos_por_hora.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_hora.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_hora.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(hours=i)
                            contador+=1

                        elif frecuencia == "dias":
                            datos_por_dia = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day)
                            nuevo_precio = datos_por_dia.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_dia.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_dia.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(days=i)
                            contador+=1

                        elif frecuencia == "meses":
                            datos_por_mes = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month)
                            nuevo_precio = datos_por_mes.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_mes.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_mes.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1)
                            contador+=1

                        elif frecuencia == "años":
                            datos_por_año = datos_coincidentes.filter(fecha__year=dato.fecha.year)
                            nuevo_precio = datos_por_año.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_año.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_año.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1, month=1)
                            contador+=1
                        
                        DatosPreprocesados.objects.create(
                            analisis=analisis,
                            fecha=nueva_fecha,
                            precio=nuevo_precio,
                            consumo=nuevo_consumo,
                            porcentaje=nuevo_porcentaje,
                            nombre=dato.nombre,
                            tipo_dato=dato.tipo_dato,
                        )
                        print("AÑADIDAS "+f'{contador}' + "LINEAS")
                        
                    elif frecuencia_datos == 10 or frecuencia_datos < 60:
                        if frecuencia=="10 minutos":
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(minutes=i*10)
                            contador+=1

                        elif frecuencia == "horas": 
                            datos_por_hora = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day, fecha__hour=dato.fecha.hour)
                            nuevo_precio = datos_por_hora.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_hora.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_hora.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(hours=i)
                            contador+=1

                        elif frecuencia == "dias":
                            datos_por_dia = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day)
                            nuevo_precio = datos_por_dia.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_dia.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_dia.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(days=i)
                            contador+=1

                        elif frecuencia == "meses":
                            datos_por_mes = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month)
                            nuevo_precio = datos_por_mes.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_mes.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_mes.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1)
                            contador+=1

                        elif frecuencia == "años":
                            datos_por_año = datos_coincidentes.filter(fecha__year=dato.fecha.year)
                            nuevo_precio = datos_por_año.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_año.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_año.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1, month=1)
                            contador+=1

                        DatosPreprocesados.objects.create(
                            analisis=analisis,
                            fecha=nueva_fecha,
                            precio=nuevo_precio,
                            consumo=nuevo_consumo,
                            porcentaje=nuevo_porcentaje,
                            nombre=dato.nombre,
                            tipo_dato=dato.tipo_dato,
                        )
                        print("AÑADIDAS "+f'{contador}' + "LINEAS")

                    elif frecuencia_datos == 60 or frecuencia_datos < 1440:
                        if frecuencia=="10 minutos":
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(minutes=i*10)
                            contador+=1

                        elif frecuencia == "horas": 
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(hours=i)
                            contador+=1

                        elif frecuencia == "dias":
                            datos_por_dia = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month, fecha__day=dato.fecha.day)
                            nuevo_precio = datos_por_dia.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_dia.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_dia.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha + timedelta(days=i)
                            contador+=1

                        elif frecuencia == "meses":
                            datos_por_mes = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month)
                            nuevo_precio = datos_por_mes.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_mes.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_mes.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1)
                            contador+=1

                        elif frecuencia == "años":
                            datos_por_año = datos_coincidentes.filter(fecha__year=dato.fecha.year)
                            nuevo_precio = datos_por_año.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_año.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_año.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1, month=1)
                            contador+=1

                        DatosPreprocesados.objects.create(
                            analisis=analisis,
                            fecha=nueva_fecha,
                            precio=nuevo_precio,
                            consumo=nuevo_consumo,
                            porcentaje=nuevo_porcentaje,
                            nombre=dato.nombre,
                            tipo_dato=dato.tipo_dato,
                        )
                        print("AÑADIDAS "+f'{contador}' + "LINEAS")
                
                    elif frecuencia_datos == 1440:
                        if frecuencia=="10 minutos":
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(minutes=i*10)
                            contador+=1

                        elif frecuencia == "horas": 
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(hours=i)
                            contador+=1

                        elif frecuencia == "dias":
                            nuevo_precio = dato.precio
                            nuevo_consumo = dato.consumo
                            nuevo_porcentaje = dato.porcentaje
                            nueva_fecha = dato.fecha + timedelta(days=i)
                            contador+=1

                        elif frecuencia == "meses":
                            datos_por_mes = datos_coincidentes.filter(fecha__year=dato.fecha.year, fecha__month=dato.fecha.month)
                            nuevo_precio = datos_por_mes.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_mes.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_mes.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1)
                            contador+=1

                        elif frecuencia == "años":
                            datos_por_año = datos_coincidentes.filter(fecha__year=dato.fecha.year)
                            nuevo_precio = datos_por_año.aggregate(nuevo_precio=Avg('precio'))['nuevo_precio']
                            nuevo_consumo = datos_por_año.aggregate(nuevo_consumo=Avg('consumo'))['nuevo_consumo']
                            nuevo_porcentaje = datos_por_año.aggregate(nuevo_porcentaje=Avg('porcentaje'))['nuevo_porcentaje']
                            nueva_fecha = dato.fecha.replace(day=1, month=1)
                            contador+=1

                        DatosPreprocesados.objects.create(
                            analisis=analisis,
                            fecha=nueva_fecha,
                            precio=nuevo_precio,
                            consumo=nuevo_consumo,
                            porcentaje=nuevo_porcentaje,
                            nombre=dato.nombre,
                            tipo_dato=dato.tipo_dato,
                        )
                        print("AÑADIDAS "+f'{contador}' + "LINEAS")

        analisis.estado = 'Terminado'
        analisis.save()
        print("Tarea completada exitosamente.")
    except Exception as e:
        print(f"Error en la tarea: {e}")
        analisis.delete()