# Weather App

A simple Flask application that provides current weather, a 5-day forecast, and a long-term outlook for any city using the OpenWeatherMap API.

## Features

- **Current Weather**: Get real-time weather data for a specified city.
- **5-Day Forecast**: View weather predictions for the next 5 days (sampled at 12:00 PM).
- **Long-term Outlook**: Provides a general seasonal outlook for the city.
- **Error Handling**: Handles invalid city names, API key issues, and connection errors.

## Tech Stack

- **Backend**: Python, Flask
- **API**: OpenWeatherMap API
- **WSGI Server**: Gunicorn (for production)
- **Environment Management**: python-dotenv

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd weatherApp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # Activate on Windows:
   venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add your OpenWeatherMap API key:
   ```env
   OPENWEATHER_API_KEY=your_api_key_here
   ```

## Running the Application

### Development Mode
```bash
python app.py
```
The app will be available at `http://127.0.0.1:5000`.

### Production Mode (using Gunicorn)
```bash
gunicorn app:app
```

## Project Structure

- `app.py`: Main Flask application logic and routes.
- `templates/index.html`: The frontend user interface.
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables (not tracked by git).
