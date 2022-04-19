import phonenumbers
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


from .models import Product
from .models import Order
from .models import OrderItem


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


@api_view(['POST'])
def register_order(request):
    order = request.data
    order_fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']
    try:
        for field in order_fields:
            order[field]
    except KeyError:
        content = {'products, firstname, lastname, phonenumber, address': 'Обязательное поле'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    if isinstance(order['products'], str):
        content = {'products': 'Поле должно содержать list со значениями. Был получен str'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    if not isinstance(order['firstname'], str):
        content = {'firstname': f'Поле должно содержать str. Был получен {type(order["firstname"])}'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    phonenumber = phonenumbers.parse(order['phonenumber'])
    if not phonenumbers.is_valid_number(phonenumber):
        content = {'phonenumber': 'Введен некорректный номер телефона'}
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    try:
        content = {}
        for field in order_fields:
            if not order[field]:
                content.update({field: 'Поле не может быть пустым'})
        return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
    except:
        pass

    customer = Order.objects.create(
        first_name=order['firstname'],
        last_name=order['lastname'],
        phone_number=order['phonenumber'],
        address=order['address']
    )

    for product in order['products']:
        OrderItem.objects.create(
            order_customer=customer,
            product=Product.objects.get(id=product['product']),
            quantity=product['quantity']
        )

    return Response(order)
