# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-23 02:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('crm', '0003_auto_20161222_1545'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_number', models.CharField(max_length=15, unique=True, verbose_name='合同号')),
                ('name', models.CharField(help_text='最大只允许20个字符', max_length=20, verbose_name='项目名')),
                ('init_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('description', models.TextField(blank=True, verbose_name='项目简介')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Customer', verbose_name='客户')),
            ],
            options={
                'verbose_name': '项目管理',
                'verbose_name_plural': '项目管理',
            },
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='最大只允许15个字符', max_length=15, verbose_name='样品名称')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pm.Project', verbose_name='项目名')),
            ],
            options={
                'verbose_name': '样品管理',
                'verbose_name_plural': '样品管理',
            },
        ),
    ]
