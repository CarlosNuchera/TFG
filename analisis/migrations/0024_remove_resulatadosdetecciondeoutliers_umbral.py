# Generated by Django 5.0.4 on 2024-05-27 16:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0023_rename_autocorrelacion_resulatadosdetecciondeoutliers_deteccion_de_outlier'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resulatadosdetecciondeoutliers',
            name='umbral',
        ),
    ]
