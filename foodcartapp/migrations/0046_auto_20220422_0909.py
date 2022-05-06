# Generated by Django 3.2 on 2022-04-22 09:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_order_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Время звонка клиенту'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Время доставки заказа'),
        ),
        migrations.AddField(
            model_name='order',
            name='registered_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now, verbose_name='Время регистрации заказа'),
            preserve_default=False,
        ),
    ]