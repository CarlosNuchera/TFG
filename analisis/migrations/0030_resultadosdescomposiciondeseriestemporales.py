# Generated by Django 5.0.4 on 2024-05-28 20:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0029_remove_descomposiciondeseriestemporales_componente_estacionalidad_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResultadosDescomposicionDeSeriesTemporales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_dato', models.CharField(default='', max_length=100)),
                ('fecha_dato', models.DateTimeField()),
                ('valor_dato', models.FloatField(blank=True, null=True)),
                ('tendencia', models.FloatField(blank=True, null=True)),
                ('estacionalidad', models.FloatField(blank=True, null=True)),
                ('residuo', models.FloatField(blank=True, null=True)),
                ('descomposicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analisis.descomposiciondeseriestemporales')),
            ],
        ),
    ]
