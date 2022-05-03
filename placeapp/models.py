from django.db import models


class Place(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название места',
        unique=True
    )
    lon = models.FloatField(
        'Долгота'
    )
    lat = models.FloatField(
        'Широта'
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
        return f'{self.name} ({self.lon}, {self.lat})'
