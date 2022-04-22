# Generated by Django 3.2 on 2022-04-22 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('p', 'Обработанный заказ'), ('u', 'Не обработанный заказ')], db_index=True, default='u', max_length=1, verbose_name='Статус заказа'),
        ),
    ]
