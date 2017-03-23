from xml.etree import ElementTree as ET
from decimal import Decimal

import attr
from tabulate import tabulate


@attr.s
class Flight:
    carrier = attr.ib()
    number = attr.ib()
    source = attr.ib()
    destination = attr.ib()
    departure_date = attr.ib()
    arrival_date = attr.ib()
    class_ = attr.ib()
    num_stops = attr.ib()


@attr.s
class Itinerary:
    flights = attr.ib()
    departure_date = attr.ib()
    arrival_date = attr.ib()
    return_flights = attr.ib()
    return_departure_date = attr.ib()
    return_arrival_date = attr.ib()
    price = attr.ib()
    num_passengers = attr.ib()


def find_routes(tree):
    root = tree.getroot()
    itineraries = root.find('PricedItineraries')
    return itineraries.findall('Flights')


def parse_route(route_tree):
    onward = route_tree.find('OnwardPricedItinerary')
    returning = route_tree.find('ReturnPricedItinerary')
    pricing = route_tree.find('Pricing')

    flights = [parse_flight(f) for f in onward.find('Flights').findall('Flight')]

    if returning:
        return_flights = [parse_flight(f) for f in returning.find('Flights').findall('Flight')]
    else:
        return_flights = ''

    return create_itinerary(flights, return_flights, pricing)


def create_itinerary(flights, return_flights, pricing):
    flight_pairs = [(f.source, f.destination) for f in flights]
    departure_date = flights[0].departure_date
    arrival_date = flights[-1].arrival_date

    return_flight_pairs = [(rf.source, rf.destination) for rf in return_flights] or None
    return_departure_date = return_flights[0].departure_date if return_flights else None
    return_arrival_date = return_flights[-1].arrival_date if return_flights else None

    price, num_passengers = calculate_price_and_num_passengers(pricing)

    return Itinerary(
        flight_pairs,
        departure_date,
        arrival_date,
        return_flight_pairs,
        return_departure_date,
        return_arrival_date,
        price,
        num_passengers
    )


def calculate_price_and_num_passengers(pricing):
    price = 0
    num_passengers = 0
    currency = pricing.attrib['currency']
    for p in pricing.findall('ServiceCharges'):
        if p.attrib['ChargeType'] == 'TotalAmount':
            price += Decimal(p.text)
            num_passengers += 1
    return str(price) + ' ' + currency, num_passengers


def parse_flight(flight_tree):
    carrier = flight_tree.find('Carrier').text
    number = flight_tree.find('FlightNumber').text
    source = flight_tree.find('Source').text
    destination = flight_tree.find('Destination').text
    departure_date = flight_tree.find('DepartureTimeStamp').text
    arrival_date = flight_tree.find('ArrivalTimeStamp').text
    class_ = flight_tree.find('Class').text
    num_stops = flight_tree.find('NumberOfStops').text

    return Flight(
        carrier, number, source, destination,
        departure_date, arrival_date, class_, num_stops
    )


if __name__ == '__main__':
    first_tree = ET.parse('RS_ViaOW.xml')
    first_routes = [parse_route(r) for r in find_routes(first_tree)]

    second_tree = ET.parse('RS_Via-3.xml')
    second_routes = [parse_route(r) for r in find_routes(second_tree)]

    for first, second in zip(first_routes, second_routes):
        data = [
            ('Onward Flights', first.flights, second.flights),
            ('Departure', first.departure_date, second.departure_date),
            ('Arrival', first.arrival_date, second.arrival_date),
            (None, None, None),
            ('Return Flights', first.return_flights, second.return_flights),
            ('Departure', first.return_departure_date, second.return_departure_date),
            ('Arrival', first.return_arrival_date, second.return_arrival_date),
            (None, None, None),
            ('Price', first.price, second.price),
            ('Number of passengers', first.num_passengers, second.num_passengers)
        ]

        print(tabulate(data))
        print('\n')

    if len(second_routes) > len(first_routes):
        more_routes = 'second'
    elif len(second_routes) < len(first_routes):
        more_routes = 'first'
    else:
        more_routes = None

    if more_routes:
        print("There's also %s itineraries in %s response that do not have pairs in %s." % (
            max(len(first_routes), len(second_routes)) - min(len(first_routes), len(second_routes)),
            more_routes,
            'first' if more_routes == 'second' else 'second'
        ))

