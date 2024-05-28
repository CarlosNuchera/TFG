from django.db import models
    
class Datos(models.Model):
    TIPO_DATO = [
        ('demanda', 'demanda'),
        ('gas', 'gas'),
        ('generacion', 'generacion'),
        ('precio', 'precio'),
    ]
    NOMBRE = [
        ('solar', 'Solar'),
        ('eolica', 'Eólica'),
        ('nuclear', 'Nuclear'),
        ('hidraulica', 'Hidráulica'),
        ('demanda real', 'Demanda real'),
        ('demanda programada', 'Demanda programada'),
        ('demanda prevista', 'Demanda prevista'),
        ('gdaes','GDAES_D+1'),
        ('Precio mercado spot diario','Precio mercado SPOT Diario'),
        ('Precio mercado spot intradiario sesión 1','Precio mercado SPOT Intradiario Sesión 1'),
        ('Precio mercado spot intradiario sesión 2','Precio mercado SPOT Intradiario Sesión 2'),
        ('Precio mercado spot intradiario sesión 3','Precio mercado SPOT Intradiario Sesión 3'),
        ('Precio mercado spot intradiario sesión 4','Precio mercado SPOT Intradiario Sesión 4'),
        ('Precio mercado spot intradiario sesión 5','Precio mercado SPOT Intradiario Sesión 5'),
        ('Precio mercado spot intradiario sesión 6','Precio mercado SPOT Intradiario Sesión 6'),
        ('Precio mercado spot intradiario sesión 7','Precio mercado SPOT Intradiario Sesión 7'),

    ]


    tipo_dato = models.CharField(max_length=100, choices=TIPO_DATO)
    nombre=models.CharField(max_length=100, choices=NOMBRE)
    fecha = models.DateTimeField()
    consumo = models.FloatField(null=True, blank=True)
    precio = models.FloatField(null=True, blank=True)
    porcentaje = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Datos'    