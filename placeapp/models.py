from django.db import models


class Place(models.Model):
    address = models.CharField(
        max_length=100,
        verbose_name='Адрес места',
        unique=True
    )
    lng = models.FloatField(
        'Долгота',
        blank=True,
        null=True
    )
    lat = models.FloatField(
        'Широта',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return f'{self.address} ({self.lng}, {self.lat})'
