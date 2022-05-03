# Generated by Django 3.2 on 2022-05-03 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_order_restaurant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='restaurant',
        ),
        migrations.CreateModel(
            name='OrderRestaurant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='restaurants', to='foodcartapp.order', verbose_name='Заказ')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан')),
            ],
            options={
                'verbose_name': 'Ресторан доставки',
                'verbose_name_plural': 'Рестораны доставки',
            },
        ),
    ]
