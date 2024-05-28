from celery import shared_task
from subprocess import run
from subprocess import run, CalledProcessError
import datetime
from celery import shared_task


hoy=datetime.datetime.now().strftime("%Y-%m-%d")
año_actual=datetime.datetime.now().year

@shared_task(bind=True)
def actualizar_datos_automaticamente(self):
    try:
        print("Iniciando tarea de actualización de datos...")

        print("Ejecutando actualizacion_diaria.py...")
        run(["C:/Users/carlo/Desktop/djangoproject/venv/Scripts/python", "C:/Users/carlo/Desktop/djangoproject/esios/actualizacion_diaria.py"], check=True)
        print("Actualizacion_diaria.py ejecutado con éxito.")

        print("Cargando demanda desde CSV...")
        run(["C:/Users/carlo/Desktop/djangoproject/venv/Scripts/python", "C:/Users/carlo/Desktop/djangoproject/manage.py", "load_data", f"demanda/{año_actual}/demand_{hoy}.csv"], check=True)
        print("Carga de demanda desde CSV completa.")

        print("Cargando datos de gas desde CSV...")
        run(["C:/Users/carlo/Desktop/djangoproject/venv/Scripts/python", "C:/Users/carlo/Desktop/djangoproject/manage.py", "load_data", "gas"], check=True)
        print("Carga de datos de gas desde CSV completa.")

        print("Cargando datos de generaciones desde CSV...")
        run(["C:/Users/carlo/Desktop/djangoproject/venv/Scripts/python", "C:/Users/carlo/Desktop/djangoproject/manage.py", "load_data", f"generaciones/{año_actual}"], check=True)
        print("Carga de datos de generaciones desde CSV completa.")

        print("Cargando datos de precios desde CSV...")
        run(["C:/Users/carlo/Desktop/djangoproject/venv/Scripts/python", "C:/Users/carlo/Desktop/djangoproject/manage.py", "load_data", f"indicadores/{año_actual}"], check=True)
        print("Carga de datos de precios desde CSV completa.")

        print("Tarea de actualización de datos completada.")

    except CalledProcessError as e:
        error_msg = f"Error al ejecutar el comando: {e}"
        print(error_msg)


