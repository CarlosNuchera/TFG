# Generated by Django 5.0.4 on 2024-04-23 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Datos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_dato', models.CharField(choices=[('demanda', 'demanda'), ('gas', 'gas'), ('generacion', 'generacion'), ('precio', 'precio')], max_length=100)),
                ('nombre', models.CharField(choices=[('solar', 'Solar'), ('eolica', 'Eólica'), ('nuclear', 'Nuclear'), ('hidraulica', 'Hidráulica'), ('demanda real', 'Demanda real'), ('demanda programada', 'Demanda programada'), ('demanda prevista', 'Demanda prevista'), ('gdaes', 'GDAES_D+1'), ('Precio mercado spot diario', 'Precio mercado SPOT Diario'), ('Precio mercado spot intradiario sesión 1', 'Precio mercado SPOT Intradiario Sesión 1'), ('Precio mercado spot intradiario sesión 2', 'Precio mercado SPOT Intradiario Sesión 2'), ('Precio mercado spot intradiario sesión 3', 'Precio mercado SPOT Intradiario Sesión 3'), ('Precio mercado spot intradiario sesión 4', 'Precio mercado SPOT Intradiario Sesión 4'), ('Precio mercado spot intradiario sesión 5', 'Precio mercado SPOT Intradiario Sesión 5'), ('Precio mercado spot intradiario sesión 6', 'Precio mercado SPOT Intradiario Sesión 6'), ('Precio mercado spot intradiario sesión 7', 'Precio mercado SPOT Intradiario Sesión 7')], max_length=100)),
                ('fecha', models.DateTimeField()),
                ('consumo', models.FloatField(blank=True, null=True)),
                ('precio', models.FloatField(blank=True, null=True)),
                ('porcentaje', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Datos',
            },
        ),
    ]