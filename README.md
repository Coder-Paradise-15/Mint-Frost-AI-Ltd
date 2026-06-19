# Mint Frost AI Chat - Enhanced Version 5.0

A modern, feature-rich AI chat application built with Flask, featuring advanced UI/UX, real-time interactions, comprehensive chat management, and a complete administrative control suite.

## 🚀 New Features & Enhancements

### 🎨 **Advanced UI/UX**
- **Dark/Light Theme Toggle** - Switch between themes with localStorage persistence
- **Glassmorphism Design** - Sleek frosted glass effects with custom blurs and harmonies
- **Responsive Layout** - Optimized layout structures with a 100% responsive user panel
- **Custom-Themed Modals** - Premium glassmorphic confirmation dialogs replacing raw native browser alerts
- **Micro-animations & Interactions** - Smooth transition animations, hover effects, and slide-in views

### 🛡️ **Administrative Suite (Version 5.0)**
- **Admin Support Inbox Dashboard** - View, filter (Open, Resolved, Closed), search, and delete user support tickets from a unified dashboard.
- **Inline Reply Drawer** - Quick-reply drawer with rich styling directly in the ticket details pane.
- **Right-Click Context Menus** - Right-click a ticket to immediately View, Reply, or Delete it.
- **Dynamic Status Badges** - Color-coded indicators tracking ticket statuses in real time.
- **In-Web File Explorer & Editor** - Browse project directories and edit source code live with syntax styling and save capabilities directly from the Admin Panel.

### ✉️ **Support Hub & SMTP Enhancements**
- **User-Side Support Hub** - Embedded Support panel featuring Knowledge Base, Contact Us, and Community Forum cards.
- **Gmail-style Email Composer** - Centered glassmorphic mail composer built directly into the UI.
- **Daily Newsletter Subscription** - Dynamic subscription system with immediate toast status notifications.
- **SMTP Anti-Spam Optimization** - Embedded logo branding via secure public HTTPS URLs instead of local file attachments to ensure high inbox delivery rates.
- **Persistent User Notifications** - User-side notification deletion blacklisted in `localStorage` to permanently clear announcements without database deletion.
- **Bring Your Own Key (BYOK)** - Fixed OpenAI initialization crash to enable stable startup fallback.

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
| `GET` | `/api/announcements` | Get announcements list |
| `GET` | `/api/announcement` | Get active site announcement config |
| `POST` | `/api/support/send` | Send support contact inquiry |
| `POST` | `/api/admin/support-tickets/reply` | Reply to support ticket (SMTP) |
| `POST` | `/api/admin/support-tickets/update-status` | Update ticket status |
| `DELETE` | `/api/admin/support-tickets/<id>` | Delete individual support ticket |
| `DELETE` | `/api/admin/support-tickets/clear-all` | Purge all support tickets |

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

✅ **Backend & Administrative Enhancements:**
- Administrative Support Inbox persistence with status routing
- Administrative Code Editor & File Explorer built-in
- SMTP spam prevention with HTTPS inline branding logo
- User-specific notification local persistence
- Session-based chat history with context memory
- Rate limiting (10 messages/minute per IP)
- Advanced error handling with user-friendly messages
- Input validation and security improvements
- Real-time weather API integration with OpenWeatherMap
- Comprehensive weather service with fallback support
- New API endpoints for support ticket management and system config

✅ **Frontend Enhancements:**
- Custom confirmation modals replacing native alerts
- Right-click context menus for support registry
- Modern sliding pill filter tab transitions
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
- Premium glassmorphic theme elements and custom scrollbars
- Enhanced accessibility with ARIA labels
- Responsive design for all devices
- Toast notifications for user feedback
- New Support tab with Knowledge Base, Contact Us, and Community links
- Embedded Email Composer modal for direct support requests

## 🎨 **Visual Enhancements**

The application now features:
- **Modern Design Language** with improved spacing and typography
- **Interactive Elements** with hover effects and micro-animations
- **Status Indicators** for connection, rate limits, and processing states
- **Visual Feedback** for all user actions
- **Consistent Iconography** using Font Awesome icons

---

**Your Flask AI Chat application is now significantly enhanced with modern features while maintaining the original code structure!**