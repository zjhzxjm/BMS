# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-11 05:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fm', '0004_auto_20170111_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='date',
            field=models.DateField(verbose_name='到账日期'),
        ),
    ]