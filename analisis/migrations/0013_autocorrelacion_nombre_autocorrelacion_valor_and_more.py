# Generated by Django 5.0.4 on 2024-05-13 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0012_remove_autocorrelacion_intervalo_confianza_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='autocorrelacion',
            name='nombre',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='autocorrelacion',
            name='valor',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='ResultadosAutocorrelacion',
        ),
    ]
