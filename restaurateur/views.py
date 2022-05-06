import requests
from geopy import distance
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Order
from foodcartapp.models import OrderRestaurant
from foodcartapp.models import Product
from foodcartapp.models import Restaurant
from foodcartapp.models import RestaurantMenuItem

from placeapp.models import Place


def find_restaurants(order):
    rests_for_products = []

    for order_item in order.items.all():
        rest_for_product = [
            item.restaurant
            for item in RestaurantMenuItem.objects.filter(product=order_item.product)
            if item.availability
        ]
        rests_for_products.append(rest_for_product)

    appropriate_rests = set(rests_for_products[0])

    for rests in rests_for_products:
        appropriate_rests = appropriate_rests & set(rests)

    return appropriate_rests


def fetch_coordinates(apikey, address):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    response = requests.get(
        base_url,
        params={
            'geocode': address,
            'apikey': apikey,
            'format': 'json',
        }
    )
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')

    Place.objects.create(
        name=address,
        lon=lon,
        lat=lat
    )

    return lon, lat


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('item_products'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.item_products.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def get_order_details(order, restaurants):
    yandex_token = settings.YANDEX_TOKEN

    try:
        order_coord = Place.objects.get(name=order.address)
        order_lon = order_coord.lon
        order_lat = order_coord.lat
    except Place.DoesNotExist:
        order_lon, order_lat = fetch_coordinates(yandex_token, order.address)

    restaurants_coordinates = []
    for rest in restaurants:

        try:
            rest_coord = Place.objects.get(name=rest.restaurant.address)
            rest_lon = rest_coord.lon
            rest_lat = rest_coord.lat
        except Place.DoesNotExist:
            rest_lon, rest_lat = fetch_coordinates(
                yandex_token,
                rest.restaurant.address
            )

        restaurants_coordinates.append(
            {
                'name': rest.restaurant.name,
                'distance': round(
                    distance.distance(
                        (order_lon, order_lat),
                        (rest_lon, rest_lat)
                    ).km, 2
                )
            }
        )
    restaurants_coordinates = sorted(restaurants_coordinates, key=lambda k: k['distance'])

    return {
        'id': order.id,
        'status': order.get_status_display(),
        'order_price': order.order_price,
        'firstname': order.firstname,
        'lastname': order.lastname,
        'address': order.address,
        'phonenumber': order.phonenumber,
        'comment': order.comment,
        'payment': order.get_payment_method_display(),
        'restaurant': restaurants_coordinates
    }


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.filter(status='u').get_order_price()
    restaurants = OrderRestaurant.objects.all().prefetch_related('restaurant')
    return render(
        request,
        template_name='order_items.html',
        context={
        'order_items': [
            get_order_details(order, restaurants.filter(order=order)) for order in orders
        ]
        }
    )
