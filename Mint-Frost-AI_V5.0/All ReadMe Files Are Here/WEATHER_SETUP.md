# Weather API Setup Guide

## Getting Your OpenWeatherMap API Key

1. **Sign up for OpenWeatherMap**
   - Go to [https://openweathermap.org/api](https://openweathermap.org/api)
   - Click "Sign Up" and create a free account
   - Verify your email address

2. **Get Your API Key**
   - Log in to your OpenWeatherMap account
   - Go to [https://home.openweathermap.org/api_keys](https://home.openweathermap.org/api_keys)
   - Copy your default API key (or create a new one)

3. **Add API Key to Your Project**
   
   **Option 1: Using weather_key.txt file**
   - Open `weather_key.txt` in your project folder
   - Replace `YOUR_OPENWEATHER_API_KEY_HERE` with your actual API key
   - Save the file

   **Option 2: Using environment variable**
   - Set environment variable: `OPENWEATHER_API_KEY=your_api_key_here`
   - On Windows: `set OPENWEATHER_API_KEY=your_api_key_here`
   - On Linux/Mac: `export OPENWEATHER_API_KEY=your_api_key_here`

## Weather Features Available

### Real-time Weather Data
- Current temperature, humidity, pressure
- Weather conditions (sunny, cloudy, rainy, etc.)
- Wind speed and direction
- Visibility information
- Sunrise and sunset times

### Location Support
- City name search (e.g., "London", "New York")
- Country codes (e.g., "London,UK", "Paris,FR")
- GPS coordinates (latitude/longitude)
- Automatic location detection (with user permission)

### Chat Integration
The AI can now provide real weather information when you ask:
- "What's the weather like?"
- "Temperature in London"
- "Weather forecast for Paris"
- "Is it raining in Tokyo?"

### Keyboard Shortcuts
- `Ctrl+W` - Get weather for your current location
- `Ctrl+Shift+U` - Set/update weather API key

## API Endpoints

- `GET /weather?location=CityName` - Get weather for a city
- `GET /api/weather/coordinates?lat=X&lon=Y` - Get weather by coordinates
- `GET /api/weather/forecast?location=CityName&days=5` - Get weather forecast
- `GET /api/weather/search?q=CityName` - Search for cities
- `POST /api/weather/set-key` - Set API key programmatically

## Troubleshooting

### No Weather Data Showing
1. Check if your API key is correctly set in `weather_key.txt`
2. Ensure your API key is activated (can take up to 2 hours after signup)
3. Check browser console for error messages

### "Fallback Data" Message
- This means the API key is not working or not set
- Verify your API key is correct and active
- Check your internet connection

### Rate Limits
- Free OpenWeatherMap accounts have 1000 calls/day limit
- The app updates weather every 10 minutes to conserve API calls
- Premium accounts have higher limits

## Free vs Paid Plans

**Free Plan (Current Limit):**
- 1,000 API calls per day
- Current weather data
- 5-day forecast
- Basic weather parameters

**Paid Plans:**
- Higher API call limits
- Historical weather data
- More detailed forecasts
- Additional weather parameters

For most personal use cases, the free plan is sufficient.