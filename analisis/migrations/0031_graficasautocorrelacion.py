# Generated by Django 5.0.4 on 2024-05-29 10:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0030_resultadosdescomposiciondeseriestemporales'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraficasAutocorrelacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='')),
                ('Autocorrelacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analisis.autocorrelacion')),
            ],
        ),
    ]
