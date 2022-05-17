import requests

from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Prefetch
from phonenumber_field.modelfields import PhoneNumberField
from geopy import distance

from placeapp.models import Place


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    if not found_places:
        return 0, 0
    most_relevant = found_places[0]
    lng, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lng, lat


def get_coordinates(apikey, address):
    try:
        place = Place.objects.get(address=address)
    except ObjectDoesNotExist:
        lng, lat = fetch_coordinates(apikey, address)
        place = Place(address=address, lat=lat, lng=lng)
        place.save()
    return place.lng, place.lat


class OrderQuerySet(models.QuerySet):

    def find_restaurants(self):
        orders = self.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        )
        res_orders = []
        for order in orders:
            order_items = set([item.product.name for item in order.items.all()])
            order.coord = get_coordinates(settings.YANDEX_TOKEN, order.address)
            restaurants = Restaurant.objects.all().prefetch_related(
                Prefetch('menu_items', queryset=RestaurantMenuItem.objects.select_related('product'))
            )
            order.restaurants = []
            for restaurant in restaurants:
                menu_items = set(
                    [item.product.name for item in restaurant.menu_items.all() if item.availability]
                )
                if order_items.issubset(menu_items):
                    restaurant.coord = get_coordinates(settings.YANDEX_TOKEN, restaurant.address)
                    restaurant.distance = round(distance.distance(order.coord, restaurant.coord).km, 3)
                    order.restaurants.append(restaurant)
            order.restaurants.sort(key=lambda place: place.distance)
            res_orders.append(order)
        return res_orders


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    STATUS = [
        ('p', 'Обработанный'),
        ('u', 'Необработанный')
    ]
    PAYMENTS = [
        ('c', 'Наличными'),
        ('o', 'Электронно')
    ]

    status = models.CharField(
        'Статус заказа',
        max_length=1,
        choices=STATUS,
        default='u',
        db_index=True
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=1,
        choices=PAYMENTS,
        db_index=True
    )
    firstname = models.CharField(
        'Имя',
        max_length=50,
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=50,
    )
    phonenumber = PhoneNumberField(
        'Телефонный номер',
        db_index=True
    )
    address = models.CharField(
        'Адрес доставки',
        max_length=100,
    )
    comment = models.TextField(
        'Комментарий',
        blank=True
    )
    registered_at = models.DateTimeField(
        'Время регистрации заказа',
        auto_now_add=True,
        db_index=True
    )
    called_at = models.DateTimeField(
        'Время звонка клиенту',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'Время доставки заказа',
        blank=True,
        null=True,
        db_index=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name='Ресторан',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        related_name='items',
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Количество'
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product.name} {self.order.lastname}'
