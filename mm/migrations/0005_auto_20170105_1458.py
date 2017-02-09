# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-05 06:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mm', '0004_auto_20170105_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='receive_date',
            field=models.DateTimeField(null=True, verbose_name='合同寄回日'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='send_date',
            field=models.DateTimeField(null=True, verbose_name='合同寄出日'),
        ),
    ]