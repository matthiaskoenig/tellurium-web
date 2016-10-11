# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-11 10:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(auto_created=True, verbose_name='date published')),
                ('name', models.CharField(max_length=200)),
                ('file', models.FileField(upload_to='archives/%Y/%m/%d')),
            ],
        ),
    ]
