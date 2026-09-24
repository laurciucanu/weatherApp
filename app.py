import os
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('OPENWEATHER_API_KEY')
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

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

if __name__ == '__main__':
    app.run(debug=True)
