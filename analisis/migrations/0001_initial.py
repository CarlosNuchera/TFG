# Generated by Django 5.0.4 on 2024-04-23 13:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('esios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Analisis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('frecuencia', models.CharField(choices=[('10 minutos', '10 minutos'), ('horas', 'Horas'), ('dias', 'Dias'), ('meses', 'Meses'), ('años', 'Años')], default='dias', max_length=20)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AnalisisDatos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analisis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analisis.analisis')),
                ('datos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esios.datos')),
            ],
        ),
        migrations.AddField(
            model_name='analisis',
            name='tipos_de_dato',
            field=models.ManyToManyField(related_name='analisis', through='analisis.AnalisisDatos', to='esios.datos'),
        ),
    ]
