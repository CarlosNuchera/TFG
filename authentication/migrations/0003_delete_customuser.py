# Generated by Django 5.0.4 on 2024-05-22 17:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_remove_post_user_customuser_delete_perfil_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomUser',
        ),
    ]
