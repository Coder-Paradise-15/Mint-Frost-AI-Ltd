# Mint Frost AI Chat - Enhanced Version 2.0

A modern, feature-rich AI chat application built with Flask, featuring advanced UI/UX, real-time interactions, and comprehensive chat management.

## 🚀 New Features & Enhancements

### 🎨 **Advanced UI/UX**
- **Dark/Light Theme Toggle** - Switch between themes with smooth transitions
- **Glassmorphism Design** - Enhanced frosted glass effects with better blur
- **Responsive Layout** - Optimized for all screen sizes
- **Smooth Animations** - Fade-in messages, typing indicators, and micro-interactions
- **Custom Scrollbars** - Styled scrollbars for better visual consistency

### 💬 **Enhanced Chat Features**
- **Message History** - Persistent chat history with session management
- **Context Memory** - AI remembers conversation context (last 10 messages)
- **Typing Indicators** - Visual feedback when AI is processing
- **Message Reactions** - Like/dislike messages with visual feedback
- **Copy Messages** - One-click copy functionality for any message
- **Message Search** - Real-time search through chat history
- **Export Chat** - Download chat history as JSON file
- **Clear History** - Reset conversation with confirmation

### 🌤️ **Real-Time Weather System**
- **Live Weather Data** - Integration with OpenWeatherMap API for accurate meteorological data
- **Location-Based Weather** - Support for city names, coordinates, and auto-location detection
- **Comprehensive Weather Info** - Temperature, humidity, wind, pressure, visibility, sunrise/sunset
- **Weather Context in Chat** - AI provides real-time weather information when asked
- **Multiple Location Support** - Get weather for any city worldwide
- **Smart Weather Queries** - Natural language weather requests ("weather in London", "is it raining?")

### ⌨️ **Keyboard Shortcuts**
- `Enter` - Send message
- `Ctrl+K` - Toggle shortcuts panel
- `Ctrl+L` - Clear chat history
- `Ctrl+E` - Export chat
- `Ctrl+F` - Search messages
- `Ctrl+W` - Get current location weather
- `Ctrl+Shift+U` - Set weather API key
- `Esc` - Close panels/modals

### 🎤 **Voice Input** (Browser Supported)
- **Speech Recognition** - Voice-to-text input
- **Visual Feedback** - Recording indicator with stop functionality
- **Auto-transcription** - Converts speech to text in input field

### 🔒 **Security & Performance**
- **Rate Limiting** - 10 messages per minute per IP
- **Input Validation** - Message length limits and sanitization
- **Session Management** - Secure session handling
- **Error Handling** - Comprehensive error messages and recovery
- **Auto-save Drafts** - Saves message drafts automatically
- **API Key Security** - Secure handling of weather and AI API keys

## 📋 **API Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main chat interface |
| `POST` | `/chat` | Send message to AI |
| `POST` | `/clear-history` | Clear chat history |
| `GET` | `/export-chat` | Export chat as JSON |
| `GET` | `/weather` | Get weather by location |
| `GET` | `/api/weather/coordinates` | Get weather by coordinates |
| `GET` | `/api/weather/forecast` | Get weather forecast |
| `GET` | `/api/weather/search` | Search cities |
| `POST` | `/api/weather/set-key` | Set weather API key |
| `GET` | `/api/sessions` | Get chat sessions |
| `GET` | `/ping` | Health check |

## 🎯 **Installation & Setup**

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Keys**
   - **OpenAI API Key**: Add your API key to `temp.txt` file
   - **Weather API Key**: Get free key from [OpenWeatherMap](https://openweathermap.org/api) and add to `weather_key.txt`
   - See `WEATHER_SETUP.md` for detailed weather API setup instructions

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access Application**
   - Open `http://localhost:5000` in your browser
   - Weather data will show "Fallback Data" until API key is configured

## 🌟 **Key Improvements Made**

✅ **Backend Enhancements:**
- Session-based chat history with context memory
- Rate limiting (10 messages/minute per IP)
- Advanced error handling with user-friendly messages
- Input validation and security improvements
- Real-time weather API integration with OpenWeatherMap
- Comprehensive weather service with fallback support
- New API endpoints for chat and weather management

✅ **Frontend Enhancements:**
- Dark/Light theme toggle with localStorage persistence
- Advanced message UI with copy/reaction buttons
- Real-time typing indicators and smooth animations
- Voice input support with visual feedback
- Live weather display in navigation bar
- Location-based weather updates with geolocation support
- Comprehensive keyboard shortcuts system
- Message search and export functionality
- Character counter and message statistics
- Auto-save draft functionality

✅ **UI/UX Improvements:**
- Enhanced glassmorphism design
- Improved accessibility with ARIA labels
- Responsive design for all devices
- Custom scrollbars and smooth scrolling
- Toast notifications for user feedback
- Loading states and error handling

✅ **Performance Optimizations:**
- Efficient DOM manipulation
- Smooth animations with CSS transitions
- Memory management for chat history
- Optimized message rendering

## 🎨 **Visual Enhancements**

The application now features:
- **Modern Design Language** with improved spacing and typography
- **Interactive Elements** with hover effects and micro-animations
- **Status Indicators** for connection, rate limits, and processing states
- **Visual Feedback** for all user actions
- **Consistent Iconography** using Font Awesome icons

---

**Your Flask AI Chat application is now significantly enhanced with modern features while maintaining the original code structure!**