# Generated by Django 5.0.4 on 2024-06-04 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0039_analisis_terminos_y_condiciones'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraficaImagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('titulo', models.CharField(max_length=100)),
                ('tipo_dato', models.CharField(max_length=50)),
                ('imagen', models.ImageField(upload_to='')),
                ('analisis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analisis.analisis')),
            ],
        ),
    ]