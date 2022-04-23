from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


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
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
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


def get_order_details(order):
    restaurants = RestaurantMenuItem.objects.select_related('restaurant')
    order_items = order.order_items.all()
    restaurant_with_item = set()
    restaurants_for_order = []
    for item in order_items:
        for place in restaurants.filter(product=item.product.id):
            if place.availability:
                restaurant_with_item.add(place.restaurant.name)
        restaurants_for_order.append(restaurant_with_item.copy())
        restaurant_with_item.clear()
    while len(restaurants_for_order) != 1:
        intersection = restaurants_for_order[-1] & restaurants_for_order[-2]
        restaurants_for_order.pop()
        restaurants_for_order.pop()
        restaurants_for_order.append(intersection)

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
        'restaurant': restaurants_for_order[0]
    }


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.filter(status='u').get_order_price()
    return render(request, template_name='order_items.html', context={
        'order_items': [get_order_details(order) for order in orders]
    })
