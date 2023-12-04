from flask import Flask, render_template, request, jsonify, session
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
from datetime import datetime
import pytz
import folium
import json
import matplotlib
import os
import urllib.request
import urllib.parse
import urllib.error

import requests

app = Flask(__name__)
#limiter = Limiter(
#    app,
#    key_func=get_remote_address,
#    default_limits=["200 per day", "50 per hour"]
#)

@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/github_form")
def github_username_form():
    return render_template("github_form.html")

# @app.route("/query?q=dinosaurs", methods=["GET"])
@app.route("/query", methods=["GET"])
def dinosaurs():
    q = request.args.get("q")
    return process_query(q)


@app.route("/nasa_form", methods=["GET", "POST"])
def nasa_form():
    if request.method == "POST":
        search_query = request.form.get("nasa_query")
        image_index = request.form.get("image_index", 0, type=int)
        response = requests.get(f"https://images-api.nasa.gov/search?q={search_query}")
        
        if response.status_code == 200:
            results = response.json()
            items = results['collection']['items']
            if items and len(items) > image_index:
                item = items[image_index]
                if 'links' in item and item['links']:
                    image_url = item['links'][0]['href']
                    return render_template(
                        "nasa_image.html", 
                        image_url=image_url,
                        search_query=search_query,
                        image_index=image_index + 1  # Prepare the next index
                    )
            return render_template("nasa_image.html", error="No more images found.")
        else:
            return render_template("nasa_image.html", error="Failed to retrieve images from NASA.")
    else:
        return render_template("nasa_form.html")




@app.route("/dog_form", methods=["GET", "POST"])
def dog_form():
    if request.method == "POST":
        # Get a random dog image
        response = requests.get("https://dog.ceo/api/breeds/image/random")
        
        if response.status_code == 200:
            image_data = response.json()
            if image_data["status"] == "success":
                image_url = image_data["message"]
                # Pass the image URL to the template
                return render_template("dog_image.html", image_url=image_url)
            else:
                return render_template("dog_form.html", error="API status is not success.")
        else:
            return render_template("dog_form.html", error=f"Failed to retrieve image: HTTP status code is {response.status_code}.")
    else:
        # If it's not a POST request, just render the form
        return render_template("dog_form.html")


@app.route("/submit", methods=["POST"])
def submit():
    input_name = request.form.get("name")
    input_age = request.form.get("age")
    input_sort = request.form.get("sortcode")
    input_account = request.form.get("accountnumber")
    input_pg = request.form.get("pgnum")
    return render_template(
        "hello.html",
        name=input_name,
        age=input_age,
        sort=input_sort,
        acc=input_account,
        pg=input_pg,
    )


@app.route("/github_form/submit", methods=["POST"])
def submit_github():
    input_username = request.form.get("github_username")
    response = (requests.get
                (f"https://api.github.com/users/{input_username}/repos"))

    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            repo_commit_details = requests.get(
                f'https://api.github.com/repos/{repo["full_name"]}/commits'
            )

            if repo_commit_details.status_code == 200:
                commits = repo_commit_details.json()
                if commits:
                    # Get the first commit's data
                    commit_data = commits[0]["commit"]
                    author_data = commit_data["author"]

                    # Format the date string to a more readable format
                    date_str = author_data["date"]
                    date_obj = (datetime.strptime
                                (date_str, "%Y-%m-%dT%H:%M:%SZ"))
                    date_obj = date_obj.replace(
                        tzinfo=pytz.utc
                    )  # Attach UTC timezone information

                    # Here you can adjust the
                    # date format as per your requirement
                    formatted_date = (
                        date_obj.strftime("%B %d, %Y %H:%M:%S UTC"))

                    # Add the cleaned up data to the repo dictionary
                    repo["special_sha"] = commits[0]["sha"]
                    repo["author_name"] = author_data["name"]
                    repo["author_email"] = author_data["email"]
                    repo["commit_date"] = formatted_date
                else:
                    repo["special_sha"] = "No commits available"
                    repo["author_name"] = ""
                    repo["author_email"] = ""
                    repo["commit_date"] = ""
            else:
                repo["special_sha"] = "Error fetching commits"
                repo["author_name"] = ""
                repo["author_email"] = ""
                repo["commit_date"] = ""
        return render_template(
            "github_form_post.html",
            github_username=input_username,
            github_repos=repos
        )
    else:
        repos = None
        error_message = ("Failed to fetch repositories. "
                         "Please check the GitHub username and try again.")
        return render_template(
            "github_form_post.html",
            github_username=input_username,
            github_repos=repos,
            error_message=error_message,
        )


def process_query(word):
    if "dinosaurs" in word:
        return "Dinosaurs ruled the Earth 200 million years ago"
    elif "name" in word:
        return "agiledevs"
    if "largest" in word:
        numbers = word.split(": ")[1]
        numbers = numbers.replace("?", "")
        numbers = numbers.replace(" ", "")
        numbers = numbers.split(",")
        return str(max([int(i) for i in numbers]))

    if "plus" in word:
        numbers = word[:-1].split()
        return str(int(numbers[2]) + int(numbers[4]))
    if "multiplied" in word:
        numbers = word[:-1].split()
        return str(int(numbers[2]) * int(numbers[5]))
    else:
        return "Unknown"

@app.route("/restaurant_map")
def restaurant_map():
    return render_template("restaurant_map.html")

def generate_map(restaurant_data, to_do_lat, to_do_long, radius):
    try:
        # Center the map by calculating the average latitude and longitude
        latitudes = [data['lat'] for data in restaurant_data]
        longitudes = [data['lng'] for data in restaurant_data]
        #avg_lat = sum(latitudes) / len(latitudes)
        #avg_lng = sum(longitudes) / len(longitudes)
        eq_map = folium.Map(location=[to_do_lat, to_do_long], zoom_start=14)

        # Define two different icons for markers
        to_do_map_pin = folium.Icon(icon='map-pin', prefix='fa', color='red')
                    
        # Create and add the to-do marker to the map
        folium.Marker(
            location=[to_do_lat, to_do_long],
            # tooltip can be added if needed
            # popup can be added if needed
            icon=to_do_map_pin  # Use the red pin icon for to-do locations
        ).add_to(eq_map)

        #radius =  2000

        folium.Circle(
            location=[to_do_lat, to_do_long],
            radius=radius+200, # input is in m
            color='#ADD8E6',
            fill=True,
            fill_color='#ADD8E6',
            fill_opacity=0.30
        ).add_to(eq_map)

        for data in restaurant_data:
            # Create the HTML for the popup
            popup_html = f"""
                <div style='min-width: 200px; max-width: 250px; padding: 1rem; background-color: white; border-radius: 0.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'>
                    <img style='width: 100%; height: auto; border-radius: 0.25rem;' src='{data['image_url']}' alt='Restaurant Image'>
                    <div style='margin-top: 0.5rem;'>
                        <div style='font-weight: 600; font-size: 1.25rem; line-height: 1.75rem; color: #4338ca;'>
                            <a href='{data['website_url']}' target='_blank' style='text-decoration: none; color: #4338ca;'>{data['name']}</a>
                        </div>
                    </div>
                    <div style='text-align: right; margin-top: 0.5rem;'>
                        <span style='font-weight: 700; font-size: 1rem; color: #475569;'>{data['ratings']}/5</span>
                    </div>
                </div>
            """
            iframe = folium.IFrame(popup_html, width=150, height=200)
            popup = folium.Popup(iframe, max_width=150)           

            #map_pin = folium.Icon(icon='location-dot', prefix='fa', color='blue')
            map_pin = folium.Icon(icon='location-dot', prefix='fa', color='blue')
            
            # Create and add a marker to the map
            folium.Marker(
                location=[data['lat'], data['lng']],
                tooltip=data['name'],
                popup=folium.Popup(popup_html, max_width=300),
                icon=map_pin
            ).add_to(eq_map)
        
        return eq_map._repr_html_()  # Return the HTML representation of the map

    except Exception as e:
        app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}", 500

def fetch_place_details(api_key, place_id):
    """Fetch place details using place_id."""
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={api_key}"
    response = requests.get(geocode_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            result = data['results'][0]
            lat = result['geometry']['location']['lat']
            lng = result['geometry']['location']['lng']
            # will give the street address not the name of the thing
            #place_name = result['formatted_address']
            return lat, lng
    return None, None

def parse_request_parameters():
    place_id = request.args.get('place_id', 'ChIJz-VvsdMEdkgR1lQfyxijRMw')  # Default to Chinatown London
    address = request.args.get('address', 'Default: China Town')
    keyword_string = request.args.get('keyword', 'restaurant')       
    price = request.args.get('price', '2')
    dist = int(request.args.get('dist', 1000))
    open_q = request.args.get('open', '')

    return place_id, address, keyword_string, price, dist, open_q

def search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q):
    keyword = '&keyword=' + keyword_string
    lat_long = 'location=' + str(lat) + ',' + str(lng)
    url_radius = '&radius=' + str(dist)
    url_price = '&maxprice=' + str(price) if price else ''
    url_open_status = '&opennow=' + str(open_q) if open_q else ''                                       

    nearby_url = ("https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
                  + lat_long + keyword + url_radius
                  + url_price + url_open_status + "&key=" + api_key)

    nearby_raw = urllib.request.urlopen(nearby_url)
    nearby_data = nearby_raw.read().decode()
    return json.loads(nearby_data)

def process_restaurant_data(nearby_data):
    all_restaurants = {}        
    for result in nearby_data['results']:
        name = result['name']
        rating = result.get('rating', 'No rating')
        rating_count = result.get('user_ratings_total', 'No rating count')
        encoded_name = urllib.parse.quote(name)  # URL encode the name
        search_link = "https://www.google.com/search?q=" + encoded_name
        rest_lat = result.get('geometry', {}).get('location', {}).get('lat', 0)
        rest_long = result.get('geometry', {}).get('location', {}).get('lng', 0)

        photo_reference = result.get('photos', [{}])[0].get('photo_reference', None)
        place_id = result.get('place_id', None)
        
        # Add to dictionary only if rating and rating_count are not default values
        if rating != 'No rating' and rating_count != 'No rating count':
            all_restaurants[name] = (rating, rating_count, search_link, rest_lat, rest_long, photo_reference, place_id)

    return all_restaurants

def sort_and_slice_restaurants(all_restaurants, top_n=15):
    sorted_restaurants = dict(sorted(all_restaurants.items(), key=lambda item: item[1][1], reverse=True))
    return dict(list(sorted_restaurants.items())[:top_n])

def fetch_additional_details(api_key, top_restaurants_dict, max_requests=15):
    counter = 0
    for name, details in top_restaurants_dict.items():
        if counter >= max_requests:
            break
        
        place_id = details[6]  # place_id is at index 6
        if place_id:
            place_details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website,editorial_summary&key=" + api_key
            response = requests.get(place_details_url)
            place_details_data = response.json()

            if place_details_data.get('status') == 'OK':                    
                result = place_details_data.get('result', {})
                formatted_phone_number = result.get('formatted_phone_number', 'Phone number not found')
                website = result.get('website', details[2])
                editorial_summary_overview = result.get('editorial_summary', {}).get('overview', 'Editorial summary not found')
                
                photo_reference = details[5]  # Assuming photo_reference is at index 5
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key=" + api_key if photo_reference else 'Image not found'

                updated_details = (details[0], details[1], website, details[3], details[4], photo_url, details[6], formatted_phone_number, editorial_summary_overview)
            
                top_restaurants_dict[name] = updated_details

        counter += 1
    return top_restaurants_dict

@app.route("/restaurants")
#@limiter.limit("10 per minute")
## WILL NEED TO PASS IN PLACE_ID and ADDRESS? or pass place_id as an argument?
#Example query: /restaurants?places_id=Cdfsdgsdfsdf&address=New+York&keyword=restaurant&price=3&dist=500&open=true
        
def show_restaurants():
    try: 
        # will need to change the key name
        api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')  # Replace with your actual API key
        
        if not api_key:
            app.logger.error("API key is empty")
            return jsonify({'error': 'API key is empty'}), 400
        
        ##### is this how we are going to do it? #####
        # Parse request parameters
        place_id, address, keyword_string, price, dist, open_q = parse_request_parameters()

        #details return to the Jinja
        search_details = {
            'place_id' : place_id,
            'address': address,
            'keyword': keyword_string,
            'price': price,
            'dist': dist,
            'open' : open_q
        }  
        
        lat, lng = fetch_place_details(api_key, place_id)
        if not lat or not lng:
            return 'Failed to retrieve place details', 500        

       # Search nearby restaurants
        nearby_data = search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q)
        if 'status' not in nearby_data or nearby_data['status'] != 'OK':
            return 'Failed to retrieve data', 500

        # Process and sort restaurants
        all_restaurants = process_restaurant_data(nearby_data)  # Assuming this function exists
        top_restaurants_dict = sort_and_slice_restaurants(all_restaurants)

        # Fetch additional details
        top_restaurants_dict = fetch_additional_details(api_key, top_restaurants_dict)            
    
    except urllib.error.URLError as e:
        app.logger.exception("URL Error occurred")
        return jsonify({'error': str(e)}), 500
    except json.JSONDecodeError as e:
        app.logger.exception("JSON Decode Error")
        return jsonify({'error': 'Invalid JSON response'}), 500
    except Exception as e:
        app.logger.exception("An unexpected error occurred")
        return jsonify({'error': str(e)}), 500

     # Prepare data for map generation
    restaurant_data = [
    {
        'name': name,
        'lat': details[3],
        'lng': details[4],
        'website_url': details[2],
        'image_url': details[5], 
        'ratings' : details[0]
    }
    for name, details in top_restaurants_dict.items()
    ]
    
    # Generate map HTML using to_do lat and logn
    map_html = generate_map(restaurant_data, lat, lng, dist) 

    return render_template("restaurant_map.html", restaurants=top_restaurants_dict, map_html=map_html, search_details=search_details)
    