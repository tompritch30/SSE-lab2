from flask import Flask, render_template, request
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
from datetime import datetime
import pytz
import folium
import json
import matplotlib
import os

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


@app.route("/generate_earthquake_map")
def generate_earthquake_map():
    try:
        # URL endpoint for the earthquake data API
        endpoint = "https://earthquake.usgs.gov/fdsnws/event/1/query?"

        # Parameters for the API request
        ps = {
            "format": "geojson",  # Requesting data in GeoJSON format
            "starttime": "2023-11-20",  # Start date for the earthquake data
            "endtime": "2023-11-27",  # End date for the earthquake data
            "minmagnitude": 4.5  # Minimum magnitude of earthquakes to retrieve
        }

        # Make an API request and get the response
        response = requests.get(endpoint, params=ps)

        # Convert the response text (JSON) into a Python dictionary
        data_dict = json.loads(response.text)

        # List to store latitude, longitude, and magnitude of each earthquake
        lat_long_mag = []

        # Loop through each earthquake in the data
        for eq in data_dict['features']:
            # Extract latitude, longitude, and magnitude
            latitude = float(eq['geometry']['coordinates'][0])
            longitude = float(eq['geometry']['coordinates'][1])
            magnitude = float(eq['properties']['mag'])

            # Append the data to the list
            lat_long_mag.append([latitude, longitude, magnitude])

        # Print the extracted data and its length
        #print(lat_long_mag)
        #print(len(lat_long_mag))

        # Create a base map centered around the Pacific Ocean
        eq_map = folium.Map(location=[0, -180], zoom_start=2)

        # Define a function to get color based on earthquake magnitude
        def get_color(magnitude):
            # Access the colormap using the new method
            colormap = matplotlib.colormaps['RdYlGn_r']  # Red-Yellow-Green reversed colormap
            normed_value = (magnitude - 6.0) / 4  # Normalize the magnitude value for color mapping
            rgba = colormap(normed_value)  # Get RGBA value from colormap
            return matplotlib.colors.rgb2hex(rgba)  # Convert RGBA to hexadecimal color

        # Loop through each point in lat_long_mag
        for point in lat_long_mag:
            folium.CircleMarker(
                location=[point[1], point[0]],  # Set location (latitude, longitude)
                popup=f'Mag: {point[2]}',  # Popup text showing the magnitude
                radius=(point[2] ** 3) / 15.0,  # Radius of the circle, scaled by magnitude
                color=get_color(point[2]),  # Border color of the circle
                fill=True,  # Fill the circle
                fill_color=get_color(point[2]),  # Fill color
                fill_opacity=0.7  # Fill opacity
            ).add_to(eq_map)

        # Instead of saving the map, embed it directly in the template
        map_html = eq_map.get_root().render()
        # Pass the HTML string to the template and use the | safe filter in Jinja2
        return render_template("earthquake_map_display.html", map_html=map_html)  # Pass the HTML string to the template and use the | safe filter in Jinja2
    except Exception as e:
        app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}, 500"

@app.route("/restaurant_map")
def restaurant_map():
    return render_template("restaurant_map.html")

@app.route("/restaurants")
#@limiter.limit("10 per minute")
def show_restaurants():
    try: 
        api_key = os.getenv('GOOGLE_MAPS_API_KEY', 'default_key')  # Replace with your actual API key

        address = request.args.get('address', 'London')  # Get address from query parameter
        price = request.args.get('price', '2')
        dist = int(request.args.get('dist', 1000))
        open_q = request.args.get('open', '')

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

        lat = js['results'][0]['geometry']['location']['lat']
        lng = js['results'][0]['geometry']['location']['lng']

        lat_long = 'location=' + str(lat) + ',' + str(lng)
        url_radius = '&radius=' + str(dist)
        url_price = '&maxprice=' + str(price) if price else ''
        url_open_status = '&opennow=' + str(open_q) if open_q else ''

        url2 = ("https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
                + lat_long + "&keyword='restaurant'" + url_radius
                + url_price + url_open_status + "&key=" + api_key)

        buh = urllib.request.urlopen(url2)
        data = buh.read().decode()
        js = json.loads(data)

        if 'status' not in js or js['status'] != 'OK':
            return 'Failed to retrieve data', 500

        Restaurants = {}
        for count, result in enumerate(js['results']):
            if count >= 15:  # Limit to 15 results
                break
            name = result['name']
            rating = result.get('rating', 'No rating')
            rating_count = result.get('user_ratings_total', 'No rating count')
            Restaurants[name] = (rating, rating_count)

        return render_template("restaurant_map.html", restaurants=Restaurants)
    except Exception as e:
        app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}, 500"
