# Generated by Django 3.2 on 2022-04-20 09:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_auto_20220420_0829'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=100, max_digits=8, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Цена'),
            preserve_default=False,
        ),
    ]