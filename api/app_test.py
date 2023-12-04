from app import generate_map
from app import fetch_place_details
from app import parse_request_parameters
from app import search_nearby_restaurants
from app import process_restaurant_data
from app import sort_and_slice_restaurants
from app import fetch_additional_details
import unittest.mock as mock

import os
api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')  
place_id = 'ChIJz-VvsdMEdkgR1lQfyxijRMw'  #default place id      

def test_generate_map():
    # Mock data
    restaurant_data = [{'lat': 51.5114, 'lng': -0.1335, 'image_url': 'http://example.com/image.jpg', 'website_url': 'http://example.com', 'name': 'Test Restaurant', 'ratings': 4.5}]
    to_do_lat = 51.5114
    to_do_long = -0.1335
    radius = 2000

    # Call the function
    result = generate_map(restaurant_data, to_do_lat, to_do_long, radius)

    # Assertions
    assert '<div id="map_' in result  # Check if the map div is present
    assert 'Test Restaurant' in result  # Check if the restaurant's name is in the map
    assert 'http://example.com/image.jpg' in result  # Check if the image URL is included
    assert '51.5114' in result and '-0.1335' in result  # Check if the restaurant's location is correct

def test_fetch_place_details():
    # Mock data
    mock_response_json = {
        "status": "OK",
        "results": [{
            "geometry": {
                "location": {"lat": 51.5114, "lng": -0.1335}
            }
        }]
    }

    # Setup the mock to replace requests.get
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response_json

        # Call the function
        lat, lng = fetch_place_details(api_key, place_id)

        # Assertions
        assert lat is not None
        assert lng is not None
        assert lat == 51.5114
        assert lng == -0.1335

    # Assertions to check if requests.get was called properly
    mock_get.assert_called_once()
    assert mock_get.call_args[0][0] == f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={api_key}"
    
def test_parse_request_parameters():
    # Call the function
    place_id, address, keyword_string, price, dist, open_q = parse_request_parameters()

    # Assertions
    assert place_id is not None
    assert address is not None
    assert keyword_string is not None
    assert price is not None
    assert dist is not None
    assert open_q is not None

def test_search_nearby_restaurants():
    # Mock data
    lat, lng = 51.5114, -0.1325
    keyword_string = 'restaurant'
    dist = 1000
    price = '2'
    open_q = 'true'

    # Call the function
    result = search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q)

    # Assertions
    assert 'results' in result
    assert len(result['results']) > 0
    # Optionally, check for specific properties in the results to ensure correct data is returned

def test_process_restaurant_data():
    # Mock data
    nearby_data = {
        'results': [
            {
                'name': 'Test Restaurant',
                'rating': 4.5,
                'user_ratings_total': 100,
                'geometry': {'location': {'lat': 51.5114, 'lng': -0.1325}},
                'photos': [{'photo_reference': 'test_photo_ref'}],
                'place_id': 'test_place_id'
            }
        ]
    }

    # Call the function
    all_restaurants = process_restaurant_data(nearby_data)

    # Assertions
    assert len(all_restaurants) == 1
    assert 'Test Restaurant' in all_restaurants
    assert all_restaurants['Test Restaurant'][0] == 4.5  # Rating
    assert all_restaurants['Test Restaurant'][1] == 100  # Rating count

def test_sort_and_slice_restaurants():
    # Mock data
    all_restaurants = {
        'Restaurant A': (4.5, 100, 'search_link', 51.5114, -0.1325, 'photo_ref', 'place_id'),
        'Restaurant B': (4.0, 200, 'search_link', 51.5114, -0.1335, 'photo_ref', 'place_id')
    }

    # Call the function
    sorted_restaurants = sort_and_slice_restaurants(all_restaurants, top_n=1)

    # Assertions
    assert len(sorted_restaurants) == 1
    assert 'Restaurant B' in sorted_restaurants  # The one with the highest rating count

def test_fetch_additional_details():
    # Mock data
    top_restaurants_dict = {
        'Test Restaurant': (4.5, 100, 'search_link', 51.5114, -0.1335, 'photo_ref', 'place_id')
    }

    # Mock the requests.get response within the test

    # Call the function
    updated_restaurants = fetch_additional_details(api_key, top_restaurants_dict, max_requests=1)

    # Assertions
    assert len(updated_restaurants) == 1
    assert 'Test Restaurant' in updated_restaurants
    # Optionally, check for additional details that should be added by the function

