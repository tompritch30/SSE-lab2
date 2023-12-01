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

def generate_map(restaurant_data):
    try:
        # Center the map by calculating the average latitude and longitude
        latitudes = [data['lat'] for data in restaurant_data]
        longitudes = [data['lng'] for data in restaurant_data]
        avg_lat = sum(latitudes) / len(latitudes)
        avg_lng = sum(longitudes) / len(longitudes)
        eq_map = folium.Map(location=[avg_lat, avg_lng], zoom_start=14)

        for data in restaurant_data:
            # Create the HTML for the popup
            # popup_html = f"""
            # <div class='p-4 max-w-sm rounded overflow-hidden shadow-lg'>
            # <img class='w-full' src='{data['image_url']}' alt='Restaurant Image'>
            # <div class='px-6 py-4'>
            #     <div class='font-bold text-xl mb-2'><a href='{data['website_url']}' target='_blank'>{data['name']}</a></div>
            # </div>            
            # </div>
            # """
            # iframe = folium.IFrame(popup_html, width=150, height=200)
            # popup = folium.Popup(iframe, max_width=150)

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

            # Create and add a marker to the map
            folium.Marker(
                location=[data['lat'], data['lng']],
                tooltip=data['name'],
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(eq_map)
        
        return eq_map._repr_html_()  # Return the HTML representation of the map

    except Exception as e:
        app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}", 500

# def generate_map(name_lat_long):
#     try:
#         # Find the center of all coordinates for auto-zoom
#         if name_lat_long:
#             latitudes = [lat for _, lat, _ in name_lat_long]
#             longitudes = [lng for _, _, lng in name_lat_long]
#             avg_lat = sum(latitudes) / len(latitudes)
#             avg_lng = sum(longitudes) / len(longitudes)
#             # change the lat long into the lat long of the place passing in
#             eq_map = folium.Map(location=[avg_lat, avg_lng], zoom_start=14)
#         else:
#             eq_map = folium.Map(location=[0, 0], zoom_start=2)

#         #marker_html='<i class="fa-solid fa-location-pin fa-bounce"></i>'
#         # Create a custom icon with a color and size
#         # custom_icon = folium.CustomIcon(
#         #     html=marker_html,
#         #     icon_size=(30, 30),  
#         #     prefix='fa'  
#         #     )

#         # Loop through each restaurant data
#         #count = 1
#         for name, lat, lng in name_lat_long:
#             folium.Marker(
#                 location=[lat, lng],
#                 popup=name,
#                 #icon=custom_icon
#                 # icon=folium.Icon(icon=count, prefix='fa')
#             ).add_to(eq_map)
#             #count +=1
#         #change map style
#         folium.TileLayer('openstreetmap').add_to(eq_map)

#         #map_html = eq_map #.get_root().render()
#         #return render_template("earthquake_map_display.html", map_html=map_html)
#         return eq_map._repr_html_()  # Return the HTML representation of the map
  
    
#     except Exception as e:
#         app.logger.exception(f"An error occurred: {e}")
#         return f"An error occurred: {e}", 500


@app.route("/restaurant_map")
def restaurant_map():
    return render_template("restaurant_map.html")

@app.route("/restaurants")
#@limiter.limit("10 per minute")
def show_restaurants():
    try: 
        # Will need to take in place ID
        # https://developers.google.com/maps/documentation/geocoding/requests-places-geocoding
        # this will get the lat long to the search

        # will need to change the key name
        api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')  # Replace with your actual API key
        
        if not api_key:
            app.logger.error("API key is empty")
            return jsonify({'error': 'API key is empty'}), 400

        address = request.args.get('address', 'London')  # Get address from query parameter

        if not address:
            return 'No address provided', 400

        serviceurl = 'https://maps.googleapis.com/maps/api/geocode/json?'

        parms = {'address': address, 'key': api_key}
        url = serviceurl + urllib.parse.urlencode(parms)

        uh = urllib.request.urlopen(url)
        data = uh.read().decode()
        js = json.loads(data)

        if 'status' not in js or js['status'] != 'OK':
            return 'Failed to retrieve data', 500
        
        keyword_string = request.args.get('keyword', 'restaurant')  # Get address from query parameter
        #this will be removed when passed the lat long
        
        price = request.args.get('price', '2')
        dist = int(request.args.get('dist', 1000))
        open_q = request.args.get('open', '')

        lat = js['results'][0]['geometry']['location']['lat']
        lng = js['results'][0]['geometry']['location']['lng']

        keyword = '&keyword=' + keyword_string
        lat_long = 'location=' + str(lat) + ',' + str(lng)
        url_radius = '&radius=' + str(dist)
        url_price = '&maxprice=' + str(price) if price else ''
        url_open_status = '&opennow=' + str(open_q) if open_q else ''
        # need image of the place
        # need place_id of each place

        # will need url3! for the place details API
        #https://developers.google.com/maps/documentation/places/web-service/details

        url2 = ("https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
                + lat_long + keyword + url_radius
                + url_price + url_open_status + "&key=" + api_key)
        
        #/restaurants?keyword=restaurant&address=New+York&price=3&dist=500&open=true


        buh = urllib.request.urlopen(url2)
        data = buh.read().decode()
        js = json.loads(data)

        if 'status' not in js or js['status'] != 'OK':
            return 'Failed to retrieve data', 500

        # Step 1: Fetch all restaurant data
        all_restaurants = {}        
        for result in js['results']:
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

        # Step 2: Sort the data by the number of reviews
        sorted_restaurants = dict(sorted(all_restaurants.items(), key=lambda item: item[1][1], reverse=True))

        # Step 3: Slice the sorted data to get only the top 15 entries
        top_restaurants_dict = dict(list(sorted_restaurants.items())[:15])

        # Step 3: Fetch photo URLs for the top 15 restaurants
        # to prevent accidental codes
        # Fetch photo URLs for the top 15 restaurants
        
        # Step 4: Fetch additional details for the top 15 restaurants
        counter = 0
        max_requests = 15

        for name, details in top_restaurants_dict.items():
            if counter >= max_requests:
                break

            place_id = details[6]  # Assuming place_id is at index 6
            if place_id:
                place_details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website,editorial_summary&key=" + api_key
                response = requests.get(place_details_url)
                place_details_data = response.json()
                # with open('place_details_response.json', 'w') as json_file:
                #         json.dump(place_details_data, json_file, indent=4)

                #      # Print the JSON response (optional)
                # print(json.dumps(place_details_data, indent=4))

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
    #name_lat_long = [(name, details[3], details[4]) for name, details in top_restaurants_dict.items()]
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
    #session['map_data'] = name_lat_long

    # Generate map HTML here (or call a function that generates it)
    map_html = generate_map(restaurant_data)  # assuming generate_map_html is a function that returns HTML

    return render_template("restaurant_map.html", restaurants=top_restaurants_dict, map_html=map_html)
    #return render_template("restaurant_map.html", restaurants=top_restaurants_dict, map_data=name_lat_long)

    # return render_template("restaurant_map.html", restaurants=top_restaurants_dict)
    
# @app.route("/generate_earthquake_map")
# def generate_earthquake_map():
#     try:
#         # URL endpoint for the earthquake data API
#         endpoint = "https://earthquake.usgs.gov/fdsnws/event/1/query?"

#         # Parameters for the API request
#         ps = {
#             "format": "geojson",  # Requesting data in GeoJSON format
#             "starttime": "2023-11-20",  # Start date for the earthquake data
#             "endtime": "2023-11-27",  # End date for the earthquake data
#             "minmagnitude": 4.5  # Minimum magnitude of earthquakes to retrieve
#         }

#         # Make an API request and get the response
#         response = requests.get(endpoint, params=ps)

#         # Convert the response text (JSON) into a Python dictionary
#         data_dict = json.loads(response.text)

#         # List to store latitude, longitude, and magnitude of each earthquake
#         lat_long_mag = []

#         # Loop through each earthquake in the data
#         for eq in data_dict['features']:
#             # Extract latitude, longitude, and magnitude
#             latitude = float(eq['geometry']['coordinates'][0])
#             longitude = float(eq['geometry']['coordinates'][1])
#             magnitude = float(eq['properties']['mag'])

#             # Append the data to the list
#             lat_long_mag.append([latitude, longitude, magnitude])

#         # Print the extracted data and its length
#         #print(lat_long_mag)
#         #print(len(lat_long_mag))

#         # Create a base map centered around the Pacific Ocean
#         eq_map = folium.Map(location=[0, -180], zoom_start=2)

#         # Define a function to get color based on earthquake magnitude
#         def get_color(magnitude):
#             # Access the colormap using the new method
#             colormap = matplotlib.colormaps['RdYlGn_r']  # Red-Yellow-Green reversed colormap
#             normed_value = (magnitude - 6.0) / 4  # Normalize the magnitude value for color mapping
#             rgba = colormap(normed_value)  # Get RGBA value from colormap
#             return matplotlib.colors.rgb2hex(rgba)  # Convert RGBA to hexadecimal color

#         # Loop through each point in lat_long_mag
#         for point in lat_long_mag:
#             folium.CircleMarker(
#                 location=[point[1], point[0]],  # Set location (latitude, longitude)
#                 popup=f'Mag: {point[2]}',  # Popup text showing the magnitude
#                 radius=(point[2] ** 3) / 15.0,  # Radius of the circle, scaled by magnitude
#                 color=get_color(point[2]),  # Border color of the circle
#                 fill=True,  # Fill the circle
#                 fill_color=get_color(point[2]),  # Fill color
#                 fill_opacity=0.7  # Fill opacity
#             ).add_to(eq_map)

#         # Instead of saving the map, embed it directly in the template
#         map_html = eq_map.get_root().render()
#         # Pass the HTML string to the template and use the | safe filter in Jinja2
#         return render_template("earthquake_map_display.html", map_html=map_html)  # Pass the HTML string to the template and use the | safe filter in Jinja2
#     except Exception as e:
#         app.logger.exception(f"An error occurred: {e}")
#         return f"An error occurred: {e}, 500"