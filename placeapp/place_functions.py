import requests

from django.conf import settings

from .models import Place


class PlaceNotFound(Exception):
    pass


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    if not found_places:
        raise PlaceNotFound
    most_relevant = found_places[0]
    lng, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lng, lat


def create_place(address):
    try:
        lng, lat = fetch_coordinates(settings.YANDEX_TOKEN, address)
        place = Place.objects.create(address=address, lng=lng, lat=lat)
    except requests.exceptions.HTTPError:
        return None
    except PlaceNotFound:
        return None
    return place


def get_or_create_places(addresses):
    places = Place.objects.in_bulk(addresses, field_name='address')
    missing_addresses = [address for address in addresses if address not in places.keys()]
    for address in missing_addresses:
        places[address] = create_place(address)
    return places
