import requests
import json
from datetime import datetime, timezone
import logging
from typing import Dict, Optional

class WeatherService:
    """Real-time weather service using OpenWeatherMap API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"
        
    def get_weather_by_city(self, city: str, country_code: str = None) -> Dict:
        """Get current weather by city name"""
        try:
            if not self.api_key:
                logging.error("No weather API key available")
                return self._get_fallback_weather()
                
            # Build location query
            location = city
            if country_code:
                location += f",{country_code}"
                
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            url = f"{self.base_url}/weather"
            logging.info(f"Weather API request: {url} with params: {params}")
            
            response = requests.get(url, params=params, timeout=5)
            
            logging.info(f"Weather API response: Status {response.status_code}, Content: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                return self._format_weather_data(data)
            else:
                logging.error(f"Weather API failed: {response.status_code} - {response.text}")
                return self._get_fallback_weather()
                
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            return self._get_fallback_weather()
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Dict:
        """Get current weather by coordinates"""
        try:
            if not self.api_key:
                return self._get_fallback_weather()
                
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(f"{self.base_url}/weather", params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_weather_data(data)
            else:
                return self._get_fallback_weather()
                
        except Exception as e:
            logging.error(f"Weather coordinates API error: {e}")
            return self._get_fallback_weather()
    
    def get_weather_forecast(self, city: str, days: int = 5) -> Dict:
        """Get weather forecast for specified days"""
        try:
            if not self.api_key:
                return self._get_fallback_forecast()
                
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': min(days * 8, 40)  # 8 forecasts per day, max 40 (API limit)
            }
            
            response = requests.get(f"{self.base_url}/forecast", params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_forecast_data(data)
            else:
                return self._get_fallback_forecast()
                
        except Exception as e:
            logging.error(f"Forecast API error: {e}")
            return self._get_fallback_forecast()
    
    def search_cities(self, query: str, limit: int = 5) -> list:
        """Search for cities by name"""
        try:
            if not self.api_key:
                return []
                
            params = {
                'q': query,
                'limit': limit,
                'appid': self.api_key
            }
            
            response = requests.get(f"{self.geo_url}/direct", params=params, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            logging.error(f"City search error: {e}")
            return []
    
    def _format_weather_data(self, data: Dict) -> Dict:
        """Format API response to standardized format"""
        weather = data.get('weather', [{}])[0]
        main = data.get('main', {})
        wind = data.get('wind', {})
        sys = data.get('sys', {})
        
        return {
            'location': data.get('name', 'Unknown'),
            'country': sys.get('country', ''),
            'temperature': round(main.get('temp', 0)),
            'feels_like': round(main.get('feels_like', 0)),
            'condition': weather.get('main', 'Clear'),
            'description': weather.get('description', '').title(),
            'humidity': main.get('humidity', 0),
            'pressure': main.get('pressure', 0),
            'wind_speed': wind.get('speed', 0),
            'wind_direction': wind.get('deg', 0),
            'visibility': data.get('visibility', 0) / 1000 if data.get('visibility') else 0,
            'icon': weather.get('icon', '01d'),
            'sunrise': datetime.fromtimestamp(sys.get('sunrise', 0), timezone.utc).strftime('%H:%M') if sys.get('sunrise') else '',
            'sunset': datetime.fromtimestamp(sys.get('sunset', 0), timezone.utc).strftime('%H:%M') if sys.get('sunset') else '',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'OpenWeatherMap'
        }
    
    def _format_forecast_data(self, data: Dict) -> Dict:
        """Format forecast API response"""
        forecasts = []
        
        for item in data.get('list', []):
            weather = item.get('weather', [{}])[0]
            main = item.get('main', {})
            
            forecasts.append({
                'datetime': item.get('dt_txt', ''),
                'temperature': round(main.get('temp', 0)),
                'condition': weather.get('main', 'Clear'),
                'description': weather.get('description', '').title(),
                'humidity': main.get('humidity', 0),
                'icon': weather.get('icon', '01d')
            })
        
        return {
            'city': data.get('city', {}).get('name', 'Unknown'),
            'country': data.get('city', {}).get('country', ''),
            'forecasts': forecasts,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'OpenWeatherMap'
        }
    
    def _get_fallback_weather(self) -> Dict:
        """Fallback weather data when API is unavailable"""
        return {
            'location': 'Your Location',
            'country': '',
            'temperature': 22,
            'feels_like': 24,
            'condition': 'Clear',
            'description': 'Clear Sky',
            'humidity': 65,
            'pressure': 1013,
            'wind_speed': 3.5,
            'wind_direction': 180,
            'visibility': 10.0,
            'icon': '01d',
            'sunrise': '06:30',
            'sunset': '18:45',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'Fallback Data'
        }
    
    def _get_fallback_forecast(self) -> Dict:
        """Fallback forecast data"""
        return {
            'city': 'Your Location',
            'country': '',
            'forecasts': [
                {
                    'datetime': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'temperature': 22,
                    'condition': 'Clear',
                    'description': 'Clear Sky',
                    'humidity': 65,
                    'icon': '01d'
                }
            ],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'Fallback Data'
        }
    
    # Class-level constant to avoid recreating on each call
    _ICON_MAP = {
        '01d': 'fas fa-sun',           # clear sky day
        '01n': 'fas fa-moon',          # clear sky night
        '02d': 'fas fa-cloud-sun',     # few clouds day
        '02n': 'fas fa-cloud-moon',    # few clouds night
        '03d': 'fas fa-cloud',         # scattered clouds
        '03n': 'fas fa-cloud',
        '04d': 'fas fa-clouds',        # broken clouds
        '04n': 'fas fa-clouds',
        '09d': 'fas fa-cloud-rain',    # shower rain
        '09n': 'fas fa-cloud-rain',
        '10d': 'fas fa-cloud-sun-rain', # rain day
        '10n': 'fas fa-cloud-moon-rain', # rain night
        '11d': 'fas fa-bolt',          # thunderstorm
        '11n': 'fas fa-bolt',
        '13d': 'fas fa-snowflake',     # snow
        '13n': 'fas fa-snowflake',
        '50d': 'fas fa-smog',          # mist
        '50n': 'fas fa-smog'
    }
    
    def get_weather_icon_class(self, icon_code: str) -> str:
        """Convert OpenWeatherMap icon code to Font Awesome class"""
        return self._ICON_MAP.get(icon_code, 'fas fa-sun')