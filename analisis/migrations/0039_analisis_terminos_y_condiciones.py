# Generated by Django 5.0.4 on 2024-05-31 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analisis', '0038_autocorrelacion_uuid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='analisis',
            name='terminos_y_condiciones',
            field=models.BooleanField(default=False),
        ),
    ]
