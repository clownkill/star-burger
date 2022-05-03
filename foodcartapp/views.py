from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Product
from .models import Order
from .models import OrderItem
from .models import OrderRestaurant
from .models import RestaurantMenuItem

def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(
        many=True,
        allow_null=False,
        write_only=True
    )

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


def find_restaurants(order):
    rests_for_products = []
    for order_item in OrderItem.objects.filter(order_customer=order):
        rest_for_product = [
            item.restaurant
            for item in RestaurantMenuItem.objects.filter(product=order_item.product)
            if item.availability
        ]
        rests_for_products.append(rest_for_product)

    while len(rests_for_products) != 1:
        intersection = set(rests_for_products[-1]) & set(rests_for_products[-2])
        rests_for_products.pop(-1)
        rests_for_products.pop(-1)
        rests_for_products.append(intersection)

    return list(rests_for_products[0])


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    order = request.data

    serializer = OrderSerializer(data=order)
    serializer.is_valid(raise_exception=True)

    customer = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )

    for product in serializer.validated_data['products']:
        OrderItem.objects.create(
            order_customer=customer,
            product=product['product'],
            quantity=product['quantity'],
            price=product['product'].price
        )
    for restaurant in find_restaurants(customer):
        OrderRestaurant.objects.create(
            order=customer,
            restaurant=restaurant
        )

    return Response(serializer.data)
