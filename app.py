import os
import math
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('OPENWEATHER_API_KEY')
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_coords(city):
    """Get latitude and longitude for a city using OWM Geocoding API."""
    if not API_KEY:
        print("DEBUG: OPENWEATHER_API_KEY is MISSING in environment variables")
        return None
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {'q': city, 'limit': 1, 'appid': API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon'], data[0].get('name', city)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate Haversine distance between two points in km."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    # Try to get the real IP from X-Forwarded-For header if behind a proxy
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    print(f"Request from IP: {ip} | Data: {request.form}")
    city = request.form.get('city')
    if not city:
        return render_template('index.html', error="Please enter a city name.")

    if not API_KEY:
        return render_template('index.html', error="API Key not configured. Please add OPENWEATHER_API_KEY to your .env file.")

    try:
        # 1. Current Weather
        curr_params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
        curr_response = requests.get(BASE_URL, params=curr_params)
        curr_data = curr_response.json()

        if curr_response.status_code != 200:
            if curr_response.status_code == 404:
                return render_template('index.html', error="City not found. Please check the spelling.")
            elif curr_response.status_code == 401:
                return render_template('index.html', error="Invalid API Key.")
            else:
                return render_template('index.html', error=f"Error: {curr_data.get('message', 'Something went wrong')}")

        # 2. 5-Day / 3-Hour Forecast
        fore_params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
        fore_response = requests.get(FORECAST_URL, params=fore_params)
        fore_data = fore_response.json()

        forecast_list = []
        if fore_response.status_code == 200:
            # To get a daily summary, we take the forecast for 12:00 PM each day
            raw_list = fore_data.get('list', [])
            daily_summaries = [item for item in raw_list if "12:00:00" in item.get('dt_txt', '')]

            # Fallback if 12 PM isn't found for some days
            if len(daily_summaries) < 5:
                daily_summaries = raw_list[::8]

            forecast_list = daily_summaries[:5]
        else:
            forecast_list = []

        # Simulated 30-day outlook
        outlook = f"Long-term outlook for {city}: Typical seasonal patterns suggest stable temperatures, but precise daily forecasts are unavailable beyond 5 days on the free tier."

        return render_template('index.html',
                               weather=curr_data,
                               forecast=forecast_list,
                               outlook=outlook,
                               city_name=curr_data.get('name'))

    except requests.exceptions.RequestException as e:
        return render_template('index.html', error="Unable to connect to the weather service.")

@app.route('/v2', methods=['GET', 'POST'])
def get_weather_v2():
    city = request.form.get('city') or request.args.get('city')
    days = int(request.form.get('days', request.args.get('days', 5)))

    if not city:
        return render_template('index_v2.html')

    # 1. Geocoding
    coords = get_coords(city)
    if not coords:
        return render_template('index_v2.html', error="City not found. Please check the spelling.")

    lat, lon, city_name = coords

    # 2. Current Weather (via Open-Meteo)
    current_url = "https://api.open-meteo.com/v1/forecast"
    current_params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
        'daily': 'sunrise,sunset',
        'timezone': 'auto'
    }
    try:
        curr_res_resp = requests.get(current_url, params=current_params, timeout=10)
        curr_res = curr_res_resp.json()
    except Exception as e:
        print(f"Current weather API error: {e}")
        return render_template('index_v2.html', error="Unable to connect to weather service.")
    current_data = curr_res.get('current', {})
    daily_base = curr_res.get('daily', {})

    # Sunrise/Sunset from daily (take index 0 for today)
    sunrise = daily_base.get('sunrise', [''])[0]
    sunset = daily_base.get('sunset', [''])[0]

    # 3. Forecast (via Open-Meteo)
    forecast_days = min(days, 16)
    fore_params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum',
        'timezone': 'auto',
        'forecast_days': forecast_days
    }
    try:
        fore_res_resp = requests.get(current_url, params=fore_params, timeout=10)
        fore_res = fore_res_resp.json()
    except Exception as e:
        print(f"Forecast API error: {e}")
        return render_template('index_v2.html', error="Unable to connect to weather service.")
    daily = fore_res.get('daily', {})

    forecast_list = []
    if 'time' in daily:
        for i in range(len(daily['time'])):
            forecast_list.append({
                'date': daily['time'][i],
                'max': daily['temperature_2m_max'][i],
                'min': daily['temperature_2m_min'][i],
                'precip': daily['precipitation_sum'][i],
                'code': daily['weather_code'][i]
            })

    # 4. Distance Calculation
    user_lat, user_lon = 44.4268, 26.1025
    distance = calculate_distance(user_lat, user_lon, lat, lon)

    # 5. Google Maps URL
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={city_name}"

    # 6. Historical Records (Expanded)
    historical = {
        'record_high': {"val": "39.6°C", "date": "19 iulie 2007"},
        'record_low': {"val": "-29.7°C", "date": "28 decembrie 1996"},
        'avg_temp': "12.4°C"
    }

    return render_template('index_v2.html',
                           weather=current_data,
                           forecast=forecast_list,
                           city_name=city_name,
                           distance=round(distance, 1),
                           google_maps_url=google_maps_url,
                           historical=historical,
                           sunrise=sunrise,
                           sunset=sunset,
                           days=days,
                           city=city)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
