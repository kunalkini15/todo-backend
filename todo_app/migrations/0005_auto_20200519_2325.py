# Generated by Django 2.2.6 on 2020-05-19 17:55

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('todo_app', '0004_auto_20200519_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 19, 17, 55, 4, 90827, tzinfo=utc)),
        ),
    ]
