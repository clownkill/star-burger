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
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    data_for_order = request.data
    print(data_for_order)
    serializer = OrderSerializer(data=data_for_order)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address']
    )

    for product in serializer.validated_data['products']:
        OrderItem.objects.create(
            order=order,
            product=product['product'],
            quantity=product['quantity'],
            price=product['product'].price
        )

    return Response(serializer.data)
