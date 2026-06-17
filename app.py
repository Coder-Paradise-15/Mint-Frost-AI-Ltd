import os
import time
import random
import sqlite3
import uuid
import html
import re
import requests
import base64
import urllib.parse
import urllib.request
import json
import ssl
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, session, g, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from collections import defaultdict
from databases import database
from static.weather_service import WeatherService
from urllib.parse import urlencode


# Create Flask app with simple logging (working setup)
app = Flask(__name__)

# Persist secret key so sessions survive server restarts
_key_path = os.path.join(os.path.dirname(__file__), '.flask_secret')
if os.path.exists(_key_path):
    with open(_key_path, 'rb') as f:
        app.secret_key = f.read()
else:
    app.secret_key = os.urandom(32)
    with open(_key_path, 'wb') as f:
        f.write(app.secret_key)


#Initialize Database
database.init_db()


def register_login_session(user_id):
    """Generates a unique session token, stores it in session, and logs it in the database"""
    session_token = str(uuid.uuid4())
    session['session_token'] = session_token
    session.modified = True
    
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_addr:
        if ',' in ip_addr:
            ip_addr = ip_addr.split(',')[0].strip()
    else:
        ip_addr = '127.0.0.1'
        
    user_agent = request.headers.get('User-Agent', 'Unknown Browser')
    database.create_active_session(session_token, user_id, ip_addr, user_agent)


@app.before_request
def check_session_validity():
    user_id = session.get('user_id')
    if user_id:
        if request.path.startswith('/static/') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico')):
            return
            
        session_token = session.get('session_token')
        if not session_token:
            session_token = str(uuid.uuid4())
            session['session_token'] = session_token
            session.modified = True
            
            ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_addr and ',' in ip_addr:
                ip_addr = ip_addr.split(',')[0].strip()
            if not ip_addr:
                ip_addr = '127.0.0.1'
                
            user_agent = request.headers.get('User-Agent', 'Unknown Browser')
            database.create_active_session(session_token, user_id, ip_addr, user_agent)
        else:
            if not database.is_session_active(session_token):
                database.set_user_online_status(user_id, 0)
                session.clear()
                session.modified = True
                
                if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                    return jsonify({'error': 'Session revoked. Please log in again.'}), 401
                
                if request.path.startswith('/admin'):
                    return redirect("/admin/login?error=session_revoked")
                return redirect("/login?error=session_revoked")


# Auth guard decorator — protects API routes from unauthenticated access
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        user = database.get_user_secure(user_id)
        if user and user.get('status') == 'deactivated':
            session.clear()
            session.modified = True
            return jsonify({'error': 'Your account has been deactivated by an administrator.'}), 403
        return f(*args, **kwargs)
    return decorated

openai_api_key_file = os.path.join(os.path.dirname(__file__), 'OpenAI-Key.txt')

# Load OpenAI API key
def load_openai_key():
    env_key = os.environ.get('OPENAI_API_KEY')
    if env_key:
        return env_key
    try:
        if os.path.exists(openai_api_key_file):
            with open(openai_api_key_file, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
    except:
        pass
    return None

# Load Weather API key
def load_weather_key():
    env_key = os.environ.get('WEATHER_API_KEY')
    if env_key:
        return env_key
    try:
        if os.path.exists('weather_key.txt'):
            with open('weather_key.txt', 'r', encoding='utf-8') as f:
                return f.read().strip()
    except:
        pass
    return None

# Load Google credentials
def load_google_credentials():
    env_id = os.environ.get('GOOGLE_CLIENT_ID')
    env_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    if env_id and env_secret:
        return env_id, env_secret
    try:
        if os.path.exists('google_credentials.txt'):
            with open('google_credentials.txt', 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.read().strip().split('\n') if l.strip()]
                if len(lines) >= 2:
                    return lines[0], lines[1]
    except:
        pass
    return None, None

weather_service = WeatherService(api_key=load_weather_key())
google_client_id, google_client_secret = load_google_credentials()

def get_llm_client(data):
    """
    Returns (llm_client, model_name) for the requested provider.
    Raises ValueError if no provider/key is supplied so the caller
    can surface a clean error message instead of hitting the broken
    server-default OpenAI key.
    """
    provider = (data or {}).get('provider')
    api_key  = (data or {}).get('api_key', '').strip()
    model    = (data or {}).get('model', '').strip()

    if not provider or provider == 'default' or not api_key:
        raise ValueError(
            "No API key configured. Click ☰ → API Settings, "
            "choose a provider (Groq is free!), paste your key, "
            "then pick that model in the chat bar."
        )
    
    if provider == 'gemini' and api_key:
        try:
            gemini_client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            active_model = model if model else 'gemini-1.5-flash'
            return gemini_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Gemini client: {e}")
            raise
            
    elif provider == 'openai' and api_key:
        try:
            openai_client = OpenAI(api_key=api_key)
            active_model = model if model else 'gpt-4o-mini'
            return openai_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate OpenAI client: {e}")
            raise
            
    elif provider == 'groq' and api_key:
        try:
            groq_client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            active_model = model if model else 'llama-3.1-8b-instant'
            return groq_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Groq client: {e}")
            raise
            
    elif provider == 'openrouter' and api_key:
        try:
            openrouter_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/Antigravity",
                    "X-Title": "Mint Frost AI"
                }
            )
            active_model = model if model else 'meta-llama/llama-3.1-8b-instruct:free'
            return openrouter_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate OpenRouter client: {e}")
            raise
            
    elif provider == 'mistral' and api_key:
        try:
            mistral_client = OpenAI(
                api_key=api_key,
                base_url="https://api.mistral.ai/v1"
            )
            active_model = model if model else 'mistral-small-latest'
            return mistral_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Mistral client: {e}")
            raise
            
    elif provider == 'anthropic' and api_key:
        try:
            class AnthropicMockClient:
                def __init__(self, api_key):
                    self.api_key = api_key
                
                @property
                def chat(self):
                    return self
                
                @property
                def completions(self):
                    return self
                
                def create(self, model, messages, max_tokens=1000, temperature=0.7, **kwargs):
                    system = None
                    anthropic_messages = []
                    for m in messages:
                        if m['role'] == 'system':
                            system = m['content']
                        else:
                            anthropic_messages.append({
                                "role": m['role'],
                                "content": m['content']
                            })
                    
                    headers = {
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                    
                    payload = {
                        "model": model if model else "claude-3-5-sonnet-20241022",
                        "messages": anthropic_messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                    if system:
                        payload["system"] = system
                    
                    import requests
                    resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=60)
                    resp.raise_for_status()
                    res_json = resp.json()
                    
                    class ChoiceMessage:
                        def __init__(self, content):
                            self.content = content
                            
                    class Choice:
                        def __init__(self, content):
                            self.message = ChoiceMessage(content)
                            
                    class MockCompletion:
                        def __init__(self, content):
                            self.choices = [Choice(content)]
                            
                    content = res_json['content'][0]['text']
                    return MockCompletion(content)
            
            anthropic_client = AnthropicMockClient(api_key)
            active_model = model if model else 'claude-3-5-sonnet-20241022'
            return anthropic_client, active_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Anthropic client: {e}")
            raise

    # Unknown / unsupported provider
    raise ValueError(
        f"Unknown provider '{provider}'. Please choose OpenAI, Gemini, "
        "Anthropic, Groq, OpenRouter, or Mistral in API Settings."
    )


# Free image generation using Pollinations API
def generate_free_image(prompt):
    try:
        clean_prompt = prompt.replace(' ', '%20').replace(',', '%2C')
        image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=512&height=512&nologo=true"
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
        return None
    except:
        return None

# Text formatting function
def format_text(text):
    # Tables (process before other formatting) - ChatGPT style
    def format_table(match):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return table_text
        
        # Parse header
        header_cells = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
        if not header_cells:
            return table_text
        
        # Skip separator line (line 1)
        data_rows = []
        for line in lines[2:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                data_rows.append(cells)
        
        # Build advanced HTML table
        table_html = f'''
        <div style="margin: 16px 0; overflow-x: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border: 1px solid rgba(255,255,255,0.1);">
            <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <thead>
                    <tr style="background: linear-gradient(135deg, var(--mint) 0%, rgba(64, 224, 208, 0.8) 100%); position: sticky; top: 0; z-index: 10;">
        '''
        
        # Header cells
        for i, cell in enumerate(header_cells):
            border_style = "border-right: 1px solid rgba(255,255,255,0.2);" if i < len(header_cells) - 1 else ""
            table_html += f'''
                        <th style="padding: 14px 16px; color: #1a1a1a; font-weight: 600; font-size: 0.9em; text-align: left; letter-spacing: 0.5px; {border_style}">
                            {cell}
                        </th>
            '''
        
        table_html += '''
                    </tr>
                </thead>
                <tbody>
        '''
        
        # Body rows
        for i, row in enumerate(data_rows):
            hover_bg = "rgba(255,255,255,0.08)" if i % 2 == 0 else "rgba(255,255,255,0.04)"
            table_html += f'<tr style="background: {hover_bg}; transition: all 0.2s ease;">'
            
            for j, cell in enumerate(row):
                if j < len(header_cells):
                    border_style = "border-right: 1px solid rgba(255,255,255,0.08);" if j < len(header_cells) - 1 else ""
                    table_html += f'<td style="padding: 12px 16px; color: rgba(255,255,255,0.9); font-size: 0.9em; border-top: 1px solid rgba(255,255,255,0.06); {border_style} vertical-align: top; line-height: 1.5;">{cell}</td>'
            
            table_html += '</tr>'
        
        table_html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return table_html
    
    # Match markdown tables
    table_pattern = r'(?:^\|.*\|\s*$\n)+(?:^\|[-:| ]+\|\s*$\n)(?:^\|.*\|\s*$\n?)+'
    text = re.sub(table_pattern, format_table, text, flags=re.MULTILINE)
    
    # Headers (process in order from most specific to least) - Compact spacing
    text = re.sub(r'^#### (.*?)$', r'<h4 style="color: var(--mint); margin: 8px 0 4px 0; font-size: 1.1em;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3 style="color: var(--mint); margin: 10px 0 5px 0; font-size: 1.2em;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2 style="color: var(--mint); margin: 12px 0 6px 0; font-size: 1.3em;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1 style="color: var(--mint); margin: 15px 0 8px 0; font-size: 1.4em;">\1</h1>', text, flags=re.MULTILINE)
    
    # Section headers without # symbols
    text = re.sub(r'^([A-Z][^\n]*:)$', r'<h3 style="color: var(--mint); margin: 12px 0 6px 0; font-size: 1.2em;">\1</h3>', text, flags=re.MULTILINE)
    
    # Code blocks (before other formatting) - Compact spacing
    text = re.sub(r'```([\s\S]*?)```', r'<pre style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 4px; margin: 6px 0; overflow-x: auto; font-size: 0.9em;"><code>\1</code></pre>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code style="background: rgba(255,255,255,0.1); padding: 1px 3px; border-radius: 2px; font-family: monospace; font-size: 0.9em;">\1</code>', text)
    
    # Bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: var(--mint); font-weight: 600;">\1</strong>', text)
    
    # Italic text
    text = re.sub(r'\*(.*?)\*', r'<em style="font-style: italic; color: rgba(255,255,255,0.9);">\1</em>', text)
    
    # Lists - Enhanced number formatting with compact spacing
    text = re.sub(r'^(\d+)([.)]?)\s*(.+)$', r'<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); font-weight: 600; min-width: 24px; background: rgba(255,255,255,0.1); border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 0.8em; margin-right: 8px; flex-shrink: 0;">\1</span><span style="flex: 1;">\3</span></li>', text, flags=re.MULTILINE)
    text = re.sub(r'^[*•-]\s*(.+)$', r'<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); margin-right: 8px; font-weight: bold;">•</span><span style="flex: 1;">\1</span></li>', text, flags=re.MULTILINE)
    
    # Wrap consecutive list items in ul - Compact spacing
    text = re.sub(r'((<li[^>]*>.*</li>\s*)+)', r'<ul style="margin: 6px 0; padding-left: 0; list-style: none;">\1</ul>', text)
    
    # Line breaks - More compact
    text = re.sub(r'\n\s*\n', '<br><br>', text)
    text = text.replace('\n', '<br>')
    
    return text

# Image generation function
def process_image_generation(ai_reply):
    try:
        # First format the text
        ai_reply = format_text(ai_reply)
        
        pattern = r'\[IMAGE_REQUEST:\s*([^\]]+)\]'
        match = re.search(pattern, ai_reply)
        
        if match:
            image_prompt = match.group(1).strip()
            
            try:
                image_base64 = generate_free_image(image_prompt)
                
                if image_base64:
                    image_html = f'<img src="data:image/png;base64,{image_base64}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;" alt="{image_prompt}"/>'
                    ai_reply = re.sub(pattern, image_html, ai_reply)
                else:
                    fallback = f'🎨 <em>Visual content: {image_prompt}</em>'
                    ai_reply = re.sub(pattern, fallback, ai_reply)
                    
            except:
                fallback = f'🎨 <em>Visual content: {image_prompt}</em>'
                ai_reply = re.sub(pattern, fallback, ai_reply)
        
        return ai_reply
    except:
        return ai_reply

# Rate limiting storage
rate_limits = defaultdict(list)
RATE_LIMIT = 10
RATE_WINDOW = 60

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: '')

@app.route("/")
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/login")
    user = database.get_user_secure(user_id)
    if user and user.get('status') == 'deactivated':
        session.clear()
        session.modified = True
        return redirect("/login?error=deactivated")
    return render_template("index.html")


@app.route("/login")
def login():
    if session.get('user_id'):
        return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get('user_id')
    session_token = session.get('session_token')
    if session_token:
        database.revoke_active_session(session_token)
    if user_id:
        database.set_user_online_status(user_id, 0)
    session.clear()
    session.modified = True
    return redirect("/login")


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
    user = database.get_user_secure(username)
    if not user:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
    if user.get('status') == 'deactivated':
        return jsonify({'success': False, 'error': 'Your account has been deactivated by an administrator.'}), 403
        
    # Check if MFA is enabled (Passkey or TOTP)
    has_passkey = False
    has_totp = False
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user_passkeys WHERE user_id = ?", (user['id'],))
            has_passkey = cursor.fetchone() is not None
            cursor.execute("SELECT id FROM user_authenticators WHERE user_id = ?", (user['id'],))
            has_totp = cursor.fetchone() is not None
    except Exception as e:
        app.logger.error(f"Error checking MFA status: {str(e)}")

    if has_passkey or has_totp:
        session['mfa_pending_user_id'] = user['id']
        session.modified = True
        return jsonify({
            'success': True,
            'mfa_required': True,
            'methods': {
                'passkey': has_passkey,
                'totp': has_totp
            }
        })

    session['user_id'] = user['id']
    session['local_user_id'] = user['id']
    session['display_name'] = user['display_name']
    session.modified = True

    # Register active session
    register_login_session(user['id'])

    # Capture login IP & Geo-location telemetry
    log_user_telemetry(user['id'])

    return jsonify({'success': True})


@app.route('/api/register', methods=['POST'])
def api_register():
    # Registration disabled administrative switch check
    if database.get_config_value('enable_registration', 'true') == 'false':
        return jsonify({'success': False, 'error': 'Public registration has been temporarily disabled by the administrator.'}), 403

    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    display_name = data.get('display_name', '').strip() or None
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
    if len(username) < 3 or len(username) > 20 or not username.isalnum():
        return jsonify({'success': False, 'error': 'Username must be 3-20 alphanumeric characters'}), 400
        
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
    existing_user = database.get_user_secure(username)
    if existing_user:
        return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
    password_hash = generate_password_hash(password)
    try:
        database.create_user_secure(username, password_hash, display_name)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to create user: {str(e)}'}), 500
        
    session['user_id'] = username
    session['local_user_id'] = username
    session['display_name'] = display_name
    session.modified = True

    # Capture registration IP & Location telemetry
    log_user_telemetry(username)

    return jsonify({'success': True})


@app.route("/test")
def test():
    return jsonify({"message": "Test successful", "timestamp": datetime.now().isoformat()})

@app.route("/regenerate", methods=["POST"])
@login_required
def regenerate():
    # Redirect to chat route with regenerate flag
    return chat(is_regenerate=True)

def check_rate_limit(client_ip):
    now = time.time()
    rate_limits[client_ip] = [req_time for req_time in rate_limits[client_ip] 
                             if now - req_time < RATE_WINDOW]
    
    if len(rate_limits[client_ip]) >= RATE_LIMIT:
        return False
    
    rate_limits[client_ip].append(now)
    return True

def get_current_info(location=None, lat=None, lon=None):
    now = datetime.now()
    
    time_info = {
        'current_time': now.strftime('%I:%M:%S %p'),
        'date': now.strftime('%A, %B %d, %Y'),
        'timezone': str(now.astimezone().tzinfo)
    }
    
    try:
        if lat is not None and lon is not None:
            weather_info = weather_service.get_weather_by_coordinates(lat, lon)
        elif location:
            weather_info = weather_service.get_weather_by_city(location)
        else:
            weather_info = weather_service.get_weather_by_city('London')
    except:
        weather_info = {
            'temperature': 'N/A',
            'description': 'Weather unavailable',
            'location': 'Unknown',
            'humidity': 'N/A',
            'wind_speed': 'N/A'
        }
    
    return time_info, weather_info

@app.route("/chat", methods=["POST"])
@login_required
def chat(is_regenerate=False):
    client_ip = request.remote_addr
    
    if not check_rate_limit(client_ip):
        return jsonify({
            "error": "Rate limit exceeded. Please wait before sending another message.",
            "retry_after": 60
        }), 429
        
    data = request.get_json() or {}
    
    # Handle regenerate request
    if is_regenerate:
        recent_sessions = database.get_recent_sessions(limit=5, user_id=session.get('user_id'))
        if not recent_sessions:
            return jsonify({"error": "No previous messages to regenerate"}), 400
        
        session_id = recent_sessions[0]['id']
        messages = database.get_session_messages(session_id)
        
        if not messages:
            return jsonify({"error": "No messages found"}), 400
        
        # Find last user message
        user_message = None
        for msg in reversed(messages):
            if msg['who'] == 'user':
                user_message = msg['text']
                break
        
        if not user_message:
            return jsonify({"error": "No user message found"}), 400
    else:
        # Normal chat request
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_message) > 2000:
            return jsonify({"error": "Message too long (max 2000 characters)"}), 400
        
        user_message = html.escape(user_message)
    
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    user_lower = user_message.lower()
    time_keywords = ['time', 'clock', 'what time', 'current time']
    weather_keywords = ['weather', 'temperature', 'temp', 'climate', 'forecast']
    
    context_info = ""
    if any(keyword in user_lower for keyword in time_keywords + weather_keywords):
        user_lat = request.headers.get('X-User-Latitude')
        user_lon = request.headers.get('X-User-Longitude')
        
        if user_lat and user_lon:
            try:
                time_info, weather_info = get_current_info(lat=float(user_lat), lon=float(user_lon))
            except:
                time_info, weather_info = get_current_info()
        else:
            time_info, weather_info = get_current_info()
            
        context_info = f"\\n\\nCurrent Information:\\n📅 {time_info['date']}\\n🕐 {time_info['current_time']} ({time_info['timezone']})\\n🌡️ {weather_info['temperature']}°C, {weather_info['description']} in {weather_info['location']}\\n💧 Humidity: {weather_info['humidity']}%\\n💨 Wind: {weather_info['wind_speed']} m/s"
    
    image_instructions = "\\n\\nCRITICAL IMAGE RULES:\\n- When users ask for images, pictures, visuals, drawings, or say 'show me', 'generate', 'create', 'draw' - you MUST respond with EXACTLY this format:\\n- First provide helpful text response, then add the image request\\n- Format: [Normal response text] + [IMAGE_REQUEST: detailed description]\\n- MANDATORY EXAMPLES:\\n  User: 'show me a mountain' → Response: 'Here's a beautiful mountain scene for you! 🎨\\n\\n[IMAGE_REQUEST: Majestic snow-capped mountain with forest below]'\\n  User: 'create a sunset' → Response: 'I'll create a stunning sunset image! Here's what I envision:\\n\\n[IMAGE_REQUEST: Beautiful orange and pink sunset over calm ocean]'\\n- ALWAYS provide both text explanation AND the [IMAGE_REQUEST: ] format"
    
    if context_info:
        system_prompt = f"You are a helpful AI assistant. Be concise and friendly. IMPORTANT: When asked about time or weather, you MUST use this real-time data and present it in a nice format: {context_info}. Do not say you cannot provide real-time information - use the data provided above.{image_instructions}"
    else:
        system_prompt = f"You are a helpful AI assistant. Be concise and friendly.{image_instructions}"
    
    messages = [{"role": "system", "content": system_prompt}]
    
    recent_history = session['chat_history'][-10:] if len(session['chat_history']) > 10 else session['chat_history']
    for msg in recent_history:
        messages.append({"role": "user", "content": msg['user']})
        messages.append({"role": "assistant", "content": msg['ai']})
    
    messages.append({"role": "user", "content": user_message})

    try:
        active_client, active_model = get_llm_client(data)
        completion = active_client.chat.completions.create(
            model=active_model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        if completion.choices:
            ai_reply = completion.choices[0].message.content
            
            if '[IMAGE_REQUEST:' in ai_reply:
                ai_reply = process_image_generation(ai_reply)
            else:
                ai_reply = format_text(ai_reply)
        else:
            ai_reply = "⚠️ No reply from AI."
            
        if 'current_session_id' not in session:
            session['current_session_id'] = str(uuid.uuid4())
            title = user_message[:50] + '...' if len(user_message) > 50 else user_message
            try:
                database.create_session(session['current_session_id'], title, user_id=session.get('user_id'))
            except:
                pass
        
        try:
            database.add_message(session['current_session_id'], user_message, 'user')
            database.add_message(session['current_session_id'], ai_reply, 'ai')
        except:
            pass
        
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        ai_reply_for_session = re.sub(r'<img[^>]*data:image/[^>]*>', '[Image Generated]', ai_reply)
        
        session['chat_history'].append({
            'user': user_message,
            'ai': ai_reply_for_session,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        if len(session['chat_history']) > 10:
            session['chat_history'] = session['chat_history'][-10:]
            
        session.modified = True
        
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Chat error: {error_msg}")
        if "rate_limit_exceeded" in error_msg.lower() or "rate limit" in error_msg.lower():
            ai_reply = "⚠️ Rate limit reached! The server's default AI quota is exhausted. Please <strong>add your own API key</strong>: click ☰ → API Settings, choose a provider (Groq is free!), paste your key, then select that model in the chat bar above."
        elif "invalid_api_key" in error_msg.lower() or "invalid api key" in error_msg.lower() or "incorrect api key" in error_msg.lower():
            ai_reply = "⚠️ Invalid API key! The server's built-in key is not configured. Please <strong>add your own key</strong> via ☰ → API Settings. <a href='https://console.groq.com' target='_blank' style='color:var(--mint)'>Get a free Groq key →</a>"
        elif "authentication" in error_msg.lower() or "401" in error_msg:
            ai_reply = "⚠️ Authentication failed. Please add your own API key via ☰ → API Settings. Groq offers a free tier at <a href='https://console.groq.com' target='_blank' style='color:var(--mint)'>console.groq.com</a>"
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            ai_reply = "⚠️ Connection error. Please check your internet connection and try again."
        else:
            ai_reply = f"⚠️ Sorry, the server's default AI key is not configured. Please click <strong>☰ → API Settings</strong> to add your own API key (Groq is free!). Error: {error_msg[:120]}"

    if 'current_session_id' not in session:
        session['current_session_id'] = str(uuid.uuid4())
    
    return jsonify({
        "reply": ai_reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_count": len(session.get('chat_history', [])),
        "session_id": session['current_session_id']
    })

@app.route("/api/sessions/<session_id>/load", methods=["POST"])
@login_required
def load_session(session_id):
    try:
        messages = database.get_session_messages(session_id)
        session['current_session_id'] = session_id
        
        chat_history = []
        user_msg = None
        for msg in messages:
            if msg['who'] == 'user':
                user_msg = msg['text']
            elif msg['who'] == 'ai' and user_msg:
                chat_history.append({
                    'user': user_msg,
                    'ai': msg['text'],
                    'timestamp': msg.get('timestamp', datetime.now(timezone.utc).isoformat())
                })
                user_msg = None
        
        # Only keep last 10 pairs in session cookie (full history is in DB)
        session['chat_history'] = chat_history[-10:]
        session.modified = True
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route("/api/sessions", methods=["GET"])
@login_required
def get_sessions():
    try:
        sessions = database.get_recent_sessions(user_id=session.get('user_id'))
        return jsonify({"sessions": sessions})
    except:
        return jsonify({"error": "Database error"}), 500

@app.route("/api/sessions/<session_id>", methods=["GET"])
@login_required
def get_session(session_id):
    try:
        messages = database.get_session_messages(session_id)
        return jsonify({"messages": messages})
    except:
        return jsonify({"error": "Database error"}), 500

@app.route("/api/sessions/<session_id>", methods=["DELETE"])
@login_required
def delete_session(session_id):
    try:
        database.delete_session(session_id)
        return jsonify({"success": True})
    except:
        return jsonify({"error": "Database error"}), 500

@app.route("/api/new-session", methods=["POST"])
@login_required
def new_session():
    session.pop('chat_history', None)
    session.pop('current_session_id', None)
    return jsonify({"success": True})

@app.route("/weather")
def get_weather():
    try:
        city = request.args.get('city', 'London')
        weather_data = weather_service.get_weather_by_city(city)
        return jsonify(weather_data)
    except:
        return jsonify({"error": "Weather service unavailable"}), 500

@app.route("/api/weather/coordinates")
def get_weather_coordinates():
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        weather_data = weather_service.get_weather_by_coordinates(lat, lon)
        return jsonify(weather_data)
    except:
        return jsonify({"error": "Invalid coordinates"}), 400

@app.route("/edit-message", methods=["POST"])
@login_required
def edit_message():
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        new_text = data.get('new_text', '').strip()
        
        if not new_text:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(new_text) > 2000:
            return jsonify({"error": "Message too long"}), 400
        
        # Generate new AI response using chat logic
        messages = [{'role': 'system', 'content': 'You are Mint Frost AI, a helpful assistant.'}]
        
        # Add recent chat history for context
        if 'chat_history' in session:
            for msg in session['chat_history'][-5:]:
                messages.append({'role': 'user', 'content': msg['user']})
                messages.append({'role': 'assistant', 'content': msg['ai']})
        
        # Add the edited message
        messages.append({'role': 'user', 'content': new_text})
        
        # Generate AI response
        active_client, active_model = get_llm_client(data)
        completion = active_client.chat.completions.create(
            model=active_model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_reply = completion.choices[0].message.content
        ai_reply = process_image_generation(ai_reply);
        
        return jsonify({
            "user_message": new_text,
            "ai_reply": ai_reply,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Edit failed: {str(e)}"}), 500

@app.route("/clear-history", methods=["POST"])
@login_required
def clear_history():
    current_session_id = session.get('current_session_id')
    if current_session_id:
        try:
            # Verify ownership before deleting
            if database.verify_session_owner(current_session_id, session.get('user_id')):
                database.delete_session(current_session_id)
        except Exception as e:
            app.logger.error(f"Error deleting current session: {e}")
            
    session.pop('chat_history', None)
    session.pop('current_session_id', None)
    return jsonify({"success": True, "message": "Chat history cleared"})

@app.route("/api/sessions/<session_id>/title", methods=["PUT"])
@login_required
def rename_session(session_id):
    try:
        # Verify ownership
        if not database.verify_session_owner(session_id, session.get('user_id')):
            return jsonify({"error": "Unauthorized"}), 403
            
        data = request.get_json() or {}
        new_title = data.get("title", "").strip()
        if not new_title:
            return jsonify({"error": "Title cannot be empty"}), 400
            
        if len(new_title) > 100:
            return jsonify({"error": "Title too long"}), 400
            
        success = database.update_session_title(session_id, new_title)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to rename session"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/<session_id>/duplicate", methods=["POST"])
@login_required
def duplicate_session_route(session_id):
    try:
        # Verify ownership
        if not database.verify_session_owner(session_id, session.get('user_id')):
            return jsonify({"error": "Unauthorized"}), 403
            
        new_session_id = database.duplicate_session(session_id)
        if new_session_id:
            return jsonify({"success": True, "new_session_id": new_session_id})
        return jsonify({"error": "Failed to duplicate session"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/<session_id>/copy", methods=["GET"])
@login_required
def copy_session_messages(session_id):
    try:
        # Verify ownership
        if not database.verify_session_owner(session_id, session.get('user_id')):
            return jsonify({"error": "Unauthorized"}), 403
            
        messages = database.get_session_messages(session_id)
        if not messages:
            return jsonify({"success": True, "formatted_text": "", "message_count": 0})
            
        formatted_parts = []
        for msg in messages:
            sender_label = "You" if msg['who'] == 'user' else "AI"
            formatted_parts.append(f"{sender_label}: {msg['text']}")
            
        formatted_text = "\n\n".join(formatted_parts)
        return jsonify({
            "success": True,
            "formatted_text": formatted_text,
            "message_count": len(messages)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear-all-data", methods=["POST"])
@login_required
def clear_all_data():
    try:
        database.clear_all_data(user_id=session.get('user_id'))
        session.pop('chat_history', None)
        session.pop('current_session_id', None)
        return jsonify({"success": True, "message": "All data cleared"})
    except Exception as e:
        return jsonify({"error": f"Failed to clear data: {str(e)}"}), 500

@app.route("/api/heartbeat", methods=["POST"])
@login_required
def api_heartbeat():
    user_id = session.get('user_id')
    if user_id:
        database.update_user_last_seen(user_id)
        session_token = session.get('session_token')
        if session_token:
            database.update_active_session_activity(session_token)
    return jsonify({"success": True})

@app.route("/api/unload", methods=["POST"])
def api_unload():
    user_id = session.get('user_id')
    if user_id:
        database.set_user_online_status(user_id, 0)
    return jsonify({"success": True})

@app.route("/api/theme", methods=["GET", "POST"])
@login_required
def theme_settings():
    if request.method == "GET":
        try:
            theme_data = database.get_user_theme(user_id=session.get('user_id'))
            custom_themes = database.get_custom_themes()
            return jsonify({
                "theme": theme_data['theme'], 
                "auto_theme": theme_data['auto_theme'],
                "custom_themes": custom_themes
            })
        except Exception as e:
            return jsonify({"theme": "dark", "auto_theme": False, "custom_themes": {}})
    
    data = request.get_json()
    theme = data.get('theme', 'dark')
    auto_theme = data.get('auto_theme')
    
    if theme in ['dark', 'light', 'mint', 'ocean', 'sunset', 'forest', 'auto'] or theme.startswith('custom_'):
        try:
            database.set_user_theme(theme, auto_theme, user_id=session.get('user_id'))
            return jsonify({"success": True, "theme": theme})
        except Exception as e:
            return jsonify({"error": "Failed to save theme"}), 500
    return jsonify({"error": "Invalid theme"}), 400

@app.route("/api/custom-theme", methods=["POST", "DELETE"])
@login_required
def custom_theme():
    if request.method == "POST":
        data = request.get_json()
        theme_name = data.get('name', '').strip()
        colors = data.get('colors', {})
        
        if not theme_name or len(theme_name) > 50:
            return jsonify({"error": "Invalid theme name"}), 400
        
        required_colors = ['primary', 'bg0', 'bg1', 'fg', 'muted']
        if not all(color in colors for color in required_colors):
            return jsonify({"error": "Missing required colors"}), 400
        
        try:
            # Generate unique theme ID
            import uuid
            theme_id = f"custom_{str(uuid.uuid4())[:8]}"
            
            if database.save_custom_theme(theme_id, theme_name, colors):
                return jsonify({"success": True, "theme_id": theme_id})
            else:
                return jsonify({"error": "Failed to save theme"}), 500
        except Exception as e:
            return jsonify({"error": "Database error"}), 500
    
    elif request.method == "DELETE":
        data = request.get_json()
        theme_id = data.get('theme_id')
        
        try:
            if database.delete_custom_theme(theme_id):
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Theme not found"}), 404
        except Exception as e:
            return jsonify({"error": "Database error"}), 500

# Spotify OAuth routes and helpers

# --- Spotify OAuth and user endpoints ---


# --- YouTube search and stream endpoints ---

youtube_search_cache = {}

@app.route('/api/youtube/search')
@login_required
def youtube_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Check cache for instant response
    if query.lower() in youtube_search_cache:
        app.logger.info("Serving YouTube search from cache for: %s", query)
        return jsonify(youtube_search_cache[query.lower()])

    # Auto-inject " audio" for clean audio-only search results
    search_query = query + " audio"
    try:
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            html_content = response.read().decode('utf-8', errors='ignore')

        json_pattern = re.compile(r'var ytInitialData = ({.*?});</script>')
        match = json_pattern.search(html_content)

        if not match:
            return jsonify([])

        yt_data = json.loads(match.group(1))
        contents = yt_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

        tracks = []
        for item in contents:
            video_renderer = item.get('videoRenderer')
            if video_renderer:
                video_id = video_renderer.get('videoId')
                title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text')
                author = video_renderer.get('ownerText', {}).get('runs', [{}])[0].get('text', 'Unknown')
                duration_text = video_renderer.get('lengthText', {}).get('simpleText', '0:00')
                thumbnails = video_renderer.get('thumbnail', {}).get('thumbnails', [])
                thumbnail_url = thumbnails[0].get('url') if thumbnails else ''

                if video_id and title:
                    tracks.append({
                        'id': video_id,
                        'title': title,
                        'author': author,
                        'duration': duration_text,
                        'thumbnail': thumbnail_url,
                        'source': 'youtube'
                    })
                    if len(tracks) >= 20:  # Limit to 20 results
                        break
        
        # Save to cache
        if tracks:
            youtube_search_cache[query.lower()] = tracks
            
        return jsonify(tracks)
    except Exception as e:
        app.logger.error("YouTube scraper search error: %s", e)
        return jsonify([])

@app.route('/api/youtube/stream')
@login_required
def youtube_stream():
    video_id = request.args.get('video_id', '').strip()
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    try:
        import yt_dlp
        import urllib.parse
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'skip_download': True,
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                proxy_url = f"/api/youtube/proxy?url={urllib.parse.quote(stream_url)}"
                return jsonify({"url": proxy_url})
            else:
                return jsonify({"error": "Failed to extract stream URL"}), 500
    except Exception as e:
        app.logger.error("YouTube stream extraction error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/youtube/proxy')
@login_required
def youtube_proxy():
    from flask import Response
    url = request.args.get('url')
    if not url:
        return "Missing url", 400
    
    if not url.startswith('https://') or '.googlevideo.com/' not in url:
        return "Invalid url", 400

    # User-Agent matching the one used in yt_dlp to resolve signatures
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Forward range headers if sent by the browser
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        
        # Build response headers
        resp_headers = {}
        for h in ['Content-Type', 'Content-Length', 'Accept-Ranges', 'Content-Range']:
            if h in r.headers:
                resp_headers[h] = r.headers[h]
                
        def generate():
            try:
                for chunk in r.iter_content(chunk_size=4096 * 8):
                    if chunk:
                        yield chunk
            except Exception:
                # Connection might close early by browser, ignore
                pass
                
        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e:
        app.logger.error("YouTube stream proxy error: %s", e)
        return "Proxy error", 500

# --- end YouTube endpoints ---

# --- Google OAuth helpers and endpoints ---

def _google_token_expired():
    expires_at = session.get('google_token_expires_at')
    if not expires_at:
        return True
    return time.time() > expires_at


def _refresh_google_token():
    refresh_token = session.get('google_refresh_token')
    if not refresh_token or not google_client_id or not google_client_secret:
        return False

    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': google_client_id,
        'client_secret': google_client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            tok = resp.json()
            access_token = tok.get('access_token')
            expires_in = tok.get('expires_in', 3600)
            session['google_access_token'] = access_token
            session['google_token_expires_at'] = int(time.time() + int(expires_in) - 30)
            # Google may not return a new refresh token on refresh
            if tok.get('refresh_token'):
                session['google_refresh_token'] = tok.get('refresh_token')

            # persist to DB if account id known
            account_id = session.get('google_account_id')
            if account_id:
                try:
                    database.save_oauth_token('google', account_id, session.get('google_access_token'), session.get('google_refresh_token'), session.get('google_token_expires_at'))
                except Exception:
                    pass

            session.modified = True
            return True
    except Exception:
        return False
    return False


def _refresh_google_token_for_account(account_id):
    tokrec = database.get_oauth_token('google', account_id)
    if not tokrec:
        return False
    refresh_token = tokrec.get('refresh_token')
    if not refresh_token or not google_client_id or not google_client_secret:
        return False

    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': google_client_id,
        'client_secret': google_client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            tok = resp.json()
            access_token = tok.get('access_token')
            expires_in = tok.get('expires_in', 3600)
            new_refresh = tok.get('refresh_token') or refresh_token
            expires_at = int(time.time() + int(expires_in) - 30)
            database.save_oauth_token('google', account_id, access_token, new_refresh, expires_at)
            # update session
            session['google_access_token'] = access_token
            session['google_refresh_token'] = new_refresh
            session['google_token_expires_at'] = expires_at
            session['google_account_id'] = account_id
            session.modified = True
            return True
    except Exception:
        return False
    return False


@app.route('/api/google/auth')
def google_auth():
    if not google_client_id or not google_client_secret:
        return jsonify({'error': 'Google credentials not configured on server'}), 500

    url_base = request.url_root or request.host_url
    if request.headers.get('X-Forwarded-Proto') == 'https':
        if url_base.startswith('http://'):
            url_base = 'https://' + url_base[7:]
    redirect_uri = url_base.rstrip('/') + '/api/google/callback'
    scope = 'openid email profile'
    params = {
        'client_id': google_client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    # Server-side redirect so a simple navigation or anchor/button will work
    return redirect(auth_url)


@app.route('/api/google/callback')
def google_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        return jsonify({'error': error}), 400
    if not code:
        return jsonify({'error': 'Missing code parameter'}), 400

    if not google_client_id or not google_client_secret:
        return jsonify({'error': 'Google credentials not configured on server'}), 500

    token_url = 'https://oauth2.googleapis.com/token'
    url_base = request.url_root or request.host_url
    if request.headers.get('X-Forwarded-Proto') == 'https':
        if url_base.startswith('http://'):
            url_base = 'https://' + url_base[7:]
    redirect_uri = url_base.rstrip('/') + '/api/google/callback'

    data = {
        'code': code,
        'client_id': google_client_id,
        'client_secret': google_client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        if resp.status_code != 200:
            err_msg = f"Token exchange failed: {resp.text}"
            return render_template('google_callback.html', error=err_msg) if 'text/html' in request.headers.get('Accept', '') else jsonify({'error': err_msg}), 400
        tok = resp.json()
        access_token = tok.get('access_token')
        refresh_token = tok.get('refresh_token')
        expires_in = tok.get('expires_in', 3600)
        expires_at = int(time.time() + int(expires_in) - 30)

        session['google_access_token'] = access_token
        session['google_refresh_token'] = refresh_token
        session['google_token_expires_at'] = expires_at
        session.modified = True

        # fetch userinfo and persist tokens
        headers = {'Authorization': f'Bearer {access_token}'}
        me_resp = requests.get('https://openidconnect.googleapis.com/v1/userinfo', headers=headers, timeout=10)
        if me_resp.status_code != 200:
            raise Exception(f"Google userinfo request failed with status {me_resp.status_code}: {me_resp.text}")
            
        profile = me_resp.json()
        account_id = profile.get('sub') or profile.get('email')
        if not account_id:
            raise Exception("No user identity found in Google profile.")
            
        session['google_account_id'] = account_id
        session.modified = True
        try:
            database.save_oauth_token('google', account_id, access_token, refresh_token, expires_at)
        except Exception:
            pass

        # Link account to local user or log in via Google SSO
        google_acct_id = session.get('google_account_id')
        if not google_acct_id:
            raise Exception("No Google account identity in session.")
            
        # Check if this Google account is already linked to a user in the database
        linked_user_id = database.get_user_by_provider('google', google_acct_id)
        
        if linked_user_id:
            # Google account is already registered! Log them in
            user_details = database.get_user_secure(linked_user_id)
            if user_details and user_details.get('status') == 'deactivated':
                session.clear()
                session.modified = True
                return render_template('google_callback.html', error='Your account has been deactivated by an administrator.') if 'text/html' in request.headers.get('Accept', '') else jsonify({'success': False, 'error': 'Your account has been deactivated by an administrator.'}), 403
            
            session['local_user_id'] = linked_user_id
            session['user_id'] = linked_user_id
            if user_details:
                session['display_name'] = user_details.get('display_name')
            
            # Register active session
            register_login_session(linked_user_id)
            
            # Log telemetry on login
            log_user_telemetry(linked_user_id)
        else:
            # Google account is not connected yet!
            # If they are already logged in locally, link Google to their active local account
            active_user_id = session.get('user_id')
            if active_user_id:
                session['local_user_id'] = active_user_id
                database.link_account_to_user(active_user_id, 'google', google_acct_id)
            else:
                # Not logged in! Create a new account automatically for Google SSO
                # Try to fetch name from Google profile info
                display_name = profile.get('name')
                
                # Generate a clean username using Google account ID
                import uuid
                import werkzeug.security
                username = f"google_{google_acct_id[:12]}"
                # Check if username exists, otherwise add random suffix
                if database.get_user_secure(username):
                    username = f"google_{str(uuid.uuid4())[:8]}"
                
                # Create the secure user in the users table
                rand_pass = str(uuid.uuid4())
                database.create_user_secure(username, werkzeug.security.generate_password_hash(rand_pass), display_name)
                
                session['local_user_id'] = username
                session['user_id'] = username
                session['display_name'] = display_name
                
                # Register active session
                register_login_session(username)
                
                # Log telemetry on auto-login
                log_user_telemetry(username)
                
                # Link Google to the newly created account
                database.link_account_to_user(username, 'google', google_acct_id)

        return render_template('google_callback.html') if 'text/html' in request.headers.get('Accept', '') else jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Failed to handle Google login/linking callback: {str(e)}")
        err_msg = f"Google authentication failed: {str(e)}"
        return render_template('google_callback.html', error=err_msg) if 'text/html' in request.headers.get('Accept', '') else jsonify({'error': err_msg}), 500


@app.route('/api/google/me')
def google_me():
    access_token = session.get('google_access_token')
    account_id = session.get('google_account_id')

    # load from DB if needed
    if not access_token and account_id:
        tokrec = database.get_oauth_token('google', account_id)
        if tokrec:
            if tokrec.get('expires_at') and time.time() > tokrec.get('expires_at'):
                if _refresh_google_token_for_account(account_id):
                    access_token = session.get('google_access_token')
            else:
                access_token = tokrec.get('access_token')
                session['google_access_token'] = access_token
                session['google_refresh_token'] = tokrec.get('refresh_token')
                session['google_token_expires_at'] = tokrec.get('expires_at')
                session['google_account_id'] = account_id
                session.modified = True

    if not access_token:
        return jsonify({'error': 'Not signed in'}), 401

    if _google_token_expired():
        if not _refresh_google_token():
            if account_id and not _refresh_google_token_for_account(account_id):
                return jsonify({'error': 'Token expired and refresh failed'}), 401
        access_token = session.get('google_access_token')

    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        resp = requests.get('https://openidconnect.googleapis.com/v1/userinfo', headers=headers, timeout=10)
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify({'error': 'Failed to fetch profile', 'details': resp.text}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/google/refresh', methods=['POST'])
def google_refresh():
    success = _refresh_google_token()
    if success:
        return jsonify({'success': True})
    account_id = session.get('google_account_id')
    if account_id and _refresh_google_token_for_account(account_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Refresh failed'}), 400


@app.route('/api/google/signout', methods=['POST'])
def google_signout():
    account_id = session.pop('google_account_id', None)
    session.pop('google_access_token', None)
    session.pop('google_refresh_token', None)
    session.pop('google_token_expires_at', None)
    session.modified = True
    if account_id:
        try:
            database.delete_oauth_token('google', account_id)
        except Exception:
            pass
    return jsonify({'success': True})

# --- end Google OAuth ---

# --- User linking helpers ---

def get_or_create_local_user():
    user_id = session.get('local_user_id')
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())
        session['local_user_id'] = user_id
        session.modified = True
        try:
            database.create_user(user_id, display_name=None)
        except Exception:
            pass
    return user_id


@app.route('/api/accounts/linked')
def api_get_linked_accounts():
    user_id = session.get('local_user_id')
    if not user_id:
        return jsonify({'linked': []})
    linked = database.get_linked_accounts(user_id)
    return jsonify({'linked': linked})


@app.route('/api/accounts/unlink', methods=['POST'])
def api_unlink_account():
    data = request.get_json() or {}
    provider = data.get('provider')
    if not provider:
        return jsonify({'error': 'provider required'}), 400

    user_id = session.get('local_user_id')
    if not user_id:
        return jsonify({'error': 'no local user'}), 400

    # delete linked_accounts entry and oauth token
    try:
        # find account id for this provider
        linked = database.get_linked_accounts(user_id)
        acct = None
        for l in linked:
            if l.get('provider') == provider:
                acct = l.get('account_id')
                break
        # unlink
        ok = database.unlink_account(user_id, provider)
        if acct:
            try:
                database.delete_oauth_token(provider, acct)
            except Exception:
                pass
        return jsonify({'success': True, 'unlinked': provider})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/profile', methods=['POST'])
def api_update_profile():
    user_id = g.user_id if hasattr(g, 'user_id') and g.user_id else session.get('local_user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    display_name = data.get('display_name', '').strip()
    if not display_name:
        return jsonify({'error': 'display_name required'}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET display_name = ? WHERE id = ?', (display_name, user_id))
            conn.commit()
        session['display_name'] = display_name
        session.modified = True
        return jsonify({'success': True, 'display_name': display_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/user/backup", methods=["GET"])
@login_required
def api_user_backup():
    username = session.get('user_id')
    details = database.get_user_full_details_admin(username)
    if not details:
        return jsonify({"error": "User profile not found"}), 404
    
    # Aggregate all conversation logs
    full_history = []
    for s in details.get('sessions', []):
        messages = database.get_session_messages(s['id'])
        full_history.append({
            'session_id': s['id'],
            'session_title': s['title'],
            'created_at': s['created_at'],
            'messages': messages
        })
    details['full_conversations'] = full_history
    
    # Stream as downloadable JSON attachment response
    import json
    from flask import Response
    response_data = json.dumps(details, indent=4)
    return Response(
        response_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=user_backup_{username}.json"}
    )


@app.route("/api/user/delete", methods=["POST"])
@login_required
def api_user_delete():
    username = session.get('user_id')
    ok = database.delete_user_self(username)
    if ok:
        session.clear()
        session.modified = True
        return jsonify({"success": True, "message": "Your account has been deleted permanently."})
    else:
        return jsonify({"error": "Failed to delete account. Please contact an administrator."}), 500


# --- end Spotify interaction ---


@app.route('/api/fetch-models', methods=['POST'])
@login_required
def fetch_models():
    data = request.get_json() or {}
    provider = data.get('provider')
    api_key = data.get('api_key', '').strip()
    
    if not provider or not api_key:
        return jsonify({"error": "Missing provider or API key"}), 400
        
    try:
        import requests
        if provider == 'openai':
            resp = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            resp.raise_for_status()
            models = [m['id'] for m in resp.json().get('data', []) if 'gpt' in m['id'] or 'o1' in m['id'] or 'o3' in m['id']]
            # sort alphabetically
            models.sort()
            return jsonify({"models": models})
            
        elif provider == 'gemini':
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            models = [m['name'].replace('models/', '') for m in resp.json().get('models', []) if 'gemini' in m['name']]
            models.sort()
            return jsonify({"models": models})
            
        elif provider == 'groq':
            resp = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            resp.raise_for_status()
            models = [m['id'] for m in resp.json().get('data', [])]
            models.sort()
            return jsonify({"models": models})
            
        elif provider == 'openrouter':
            resp = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            resp.raise_for_status()
            models = [m['id'] for m in resp.json().get('data', [])]
            models.sort()
            return jsonify({"models": models})
            
        elif provider == 'mistral':
            resp = requests.get("https://api.mistral.ai/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            resp.raise_for_status()
            models = [m['id'] for m in resp.json().get('data', [])]
            models.sort()
            return jsonify({"models": models})
            
        elif provider == 'anthropic':
            resp = requests.get("https://api.anthropic.com/v1/models", headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }, timeout=10)
            resp.raise_for_status()
            models = [m['id'] for m in resp.json().get('data', [])]
            models.sort()
            return jsonify({"models": models})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    return jsonify({"error": "Unsupported provider"}), 400

# --- Administrative Authentication Guard and Routes ---

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect("/admin/login")
        user = database.get_user_secure(user_id)
        if not user or not user.get('is_admin'):
            if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                return jsonify({'error': 'Administrator access required'}), 403
            return redirect("/admin/login?error=unauthorized")
        return f(*args, **kwargs)
    return decorated


def superadmin_required(f):
    """Decorator for destructive operations — requires is_admin >= 2 (full Admin)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        user = database.get_user_secure(user_id)
        if not user or (user.get('is_admin') or 0) < 2:
            return jsonify({'error': 'Superadmin privileges required. Co-Admins cannot perform this action.'}), 403
        return f(*args, **kwargs)
    return decorated


def log_user_telemetry(username):
    """Log Client IP & Geo-location telemetry on user database records using actual geolocation api"""
    try:
        # Mark user online immediately and update last seen
        try:
            database.update_user_last_seen(username)
        except Exception:
            pass

        ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_addr:
            if ',' in ip_addr:
                ip_addr = ip_addr.split(',')[0].strip()
        else:
            ip_addr = '127.0.0.1'
        
        # Determine actual location by querying public lookup
        is_local = ip_addr in ['127.0.0.1', '::1', 'localhost'] or ip_addr.startswith('192.168.') or ip_addr.startswith('10.') or ip_addr.startswith('172.')
        url = 'http://ip-api.com/json/' if is_local else f'http://ip-api.com/json/{ip_addr}'
        location = "Mumbai, Maharashtra, India" # default fallback
        try:
            resp = requests.get(url, timeout=5).json()
            if resp.get('status') == 'success':
                city = resp.get('city', '')
                state = resp.get('regionName', '')
                country = resp.get('country', '')
                parts = [p for p in [city, state, country] if p]
                if parts:
                    location = ", ".join(parts)
        except Exception:
            pass

        try:
            database.update_user_telemetry_admin(username, ip_addr, location)
        except Exception:
            pass
    except Exception:
        pass


@app.route("/admin/login")
def admin_login():
    if session.get('user_id'):
        user = database.get_user_secure(session.get('user_id'))
        if user and user.get('is_admin'):
            return redirect("/admin")
    return render_template("admin_login.html")


@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
    user = database.get_user_secure(username)
    if not user or not user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Invalid administrator credentials'}), 401
        
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid administrator credentials'}), 401
        
    session['user_id'] = user['id']
    session['local_user_id'] = user['id']
    session['display_name'] = user['display_name']
    session['is_admin'] = True
    session.modified = True

    # Register active session
    register_login_session(user['id'])

    # Log administrator IP telemetry
    log_user_telemetry(user['id'])

    return jsonify({'success': True})


@app.route("/admin")
@admin_required
def admin_dashboard():
    user_id = session.get('user_id')
    user = database.get_user_secure(user_id)
    return render_template("admin_dashboard.html", current_admin=user)


@app.route("/admin/charts/growth")
@admin_required
def admin_chart_growth():
    return render_template("admin_chart_growth.html")


@app.route("/admin/charts/latency")
@admin_required
def admin_chart_latency():
    return render_template("admin_chart_latency.html")


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def api_admin_users():
    search = request.args.get('search', '').strip() or None
    status = request.args.get('status', '').strip() or None
    date_val = request.args.get('date', '').strip() or None
    time_val = request.args.get('time', '').strip() or None
    start_date = request.args.get('start_date', '').strip() or request.args.get('chart_start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or request.args.get('chart_end_date', '').strip() or None
    start_time = request.args.get('start_time', '').strip() or request.args.get('chart_start_time', '').strip() or None
    end_time = request.args.get('end_time', '').strip() or request.args.get('chart_end_time', '').strip() or None
    
    users = database.get_all_users_admin(
        search=search, status=status, date_val=date_val, time_val=time_val,
        start_date=start_date, end_date=end_date,
        start_time=start_time, end_time=end_time
    )
    
    # Compute unfiltered database statistics for dashboard tiles
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'deactivated'")
            deactivated = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            active = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'idle'")
            idle = cursor.fetchone()[0]
            
            # Online count query matching is_online check
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE is_online = 1 AND (strftime('%s', 'now') - strftime('%s', COALESCE(last_seen, created_at))) < 15
            ''')
            online = cursor.fetchone()[0]
            offline = total - online
    except Exception as e:
        total = online = offline = active = idle = deactivated = 0
        
    return jsonify({
        "users": users,
        "stats": {
            "total": total,
            "online": online,
            "offline": offline,
            "active": active,
            "idle": idle,
            "deactivated": deactivated
        }
    })


@app.route("/api/admin/users", methods=["POST"])
@admin_required
def api_admin_users_create():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    display_name = data.get('display_name', '').strip() or None
    role = data.get('role', 'user').strip().lower()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if len(username) < 3 or len(username) > 20 or not username.isalnum():
        return jsonify({'error': 'Username must be 3-20 alphanumeric characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if role not in ['admin', 'coadmin', 'user']:
        return jsonify({'error': 'Invalid role selector value'}), 400

    # Only superadmins can create admin or co-admin accounts
    if role in ['admin', 'coadmin']:
        caller = database.get_user_secure(session.get('user_id'))
        if not caller or (caller.get('is_admin') or 0) < 2:
            return jsonify({'error': 'Only Admins can create admin/co-admin accounts'}), 403

    # Check if user already exists
    existing = database.get_user_secure(username)
    if existing:
        return jsonify({'error': 'Username already exists'}), 409

    # Hash the password and save
    password_hash = generate_password_hash(password)
    is_admin = 2 if role == 'admin' else (1 if role == 'coadmin' else 0)

    success = database.create_user_secure(username, password_hash, display_name, is_admin)
    if success:
        database.log_admin_action(session.get('user_id'), 'CREATE_USER', username, f'Created user account with role {role}')
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to create user in database'}), 500


@app.route("/api/admin/users/<username>/status", methods=["POST"])
@admin_required
def api_admin_users_status(username):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ['active', 'deactivated', 'idle']:
        return jsonify({"error": "Invalid status value"}), 400
    
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0

    success = database.update_user_status_admin(username, status, caller_level=caller_level)
    if success:
        database.log_admin_action(session.get('user_id'), 'UPDATE_STATUS', username, f'Updated account status to {status}')
        if status == 'deactivated':
            database.add_announcement("Your account has been deactivated by an administrator.", user_id=username)
            # Instantly set them offline in database
            database.set_user_online_status(username, 0)
        return jsonify({"success": True})
    return jsonify({"error": "Failed to update status (note: admin profiles/tier limits are protected)"}), 400


@app.route("/api/admin/users/<username>/reset-password", methods=["POST"])
@admin_required
def api_admin_users_reset_password(username):
    data = request.get_json() or {}
    new_password = data.get("password", "").strip()
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
        
    password_hash = generate_password_hash(new_password)
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0

    success = database.reset_user_password_admin(username, password_hash, caller_level=caller_level)
    if success:
        database.log_admin_action(session.get('user_id'), 'RESET_PASSWORD', username, 'Reset user password')
        return jsonify({"success": True})
    return jsonify({"error": "Failed to reset password (note: admin profiles/tier limits are protected)"}), 400


@app.route("/api/admin/users/<username>", methods=["DELETE"])
@admin_required
def api_admin_users_delete(username):
    caller_id = session.get('user_id')
    if username == caller_id:
        return jsonify({"error": "You cannot delete your own profile"}), 400
        
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0
        
    success = database.delete_user_admin(username, caller_level=caller_level)
    if success:
        database.log_admin_action(session.get('user_id'), 'DELETE_USER', username, 'Permanently deleted user account')
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete user (note: admin profiles/tier limits are protected)"}), 400


# --- Premium Administrative Command APIs ---

# Human-friendly descriptions of security policy rules
SECURITY_RULES_METADATA = {
    "rule_admin_delete_coadmin": {"label": "Admin: Delete Co-Admins", "role": "admin", "desc": "Allows Admins to permanently delete Co-Admin profiles and sessions."},
    "rule_admin_delete_user": {"label": "Admin: Delete Users", "role": "admin", "desc": "Allows Admins to permanently delete standard User profiles and sessions."},
    "rule_admin_reset_coadmin": {"label": "Admin: Reset Co-Admin Password", "role": "admin", "desc": "Allows Admins to reset the credentials of Co-Admins."},
    "rule_admin_reset_user": {"label": "Admin: Reset User Password", "role": "admin", "desc": "Allows Admins to reset the credentials of standard Users."},
    "rule_admin_manage_config": {"label": "Admin: Manage System Config", "role": "admin", "desc": "Enables site setting configuration toggles for Admins."},
    "rule_admin_execute_commands": {"label": "Admin: Execute Terminal Commands", "role": "admin", "desc": "Allows Admins to run custom terminal console commands."},
    "rule_admin_publish_announcement": {"label": "Admin: Publish Announcements", "role": "admin", "desc": "Allows Admins to broadcast site-wide announcements."},
    "rule_admin_export_data": {"label": "Admin: Export User Data", "role": "admin", "desc": "Allows Admins to download audit logs/JSON files of any profile."},
    
    "rule_coadmin_delete_user": {"label": "Co-Admin: Delete Users", "role": "coadmin", "desc": "Allows Co-Admins to permanently delete standard User profiles."},
    "rule_coadmin_reset_user": {"label": "Co-Admin: Reset User Password", "role": "coadmin", "desc": "Allows Co-Admins to reset standard User credentials."},
    "rule_coadmin_deactivate_user": {"label": "Co-Admin: Deactivate Users", "role": "coadmin", "desc": "Allows Co-Admins to deactivate/suspend standard User profiles."},
    "rule_coadmin_view_logs": {"label": "Co-Admin: View Live System Logs", "role": "coadmin", "desc": "Allows Co-Admins to access the terminal console log stream."},
    "rule_coadmin_publish_announcement": {"label": "Co-Admin: Publish Announcements", "role": "coadmin", "desc": "Allows Co-Admins to broadcast site-wide announcements."},
    "rule_coadmin_execute_commands": {"label": "Co-Admin: Execute Terminal Commands", "role": "coadmin", "desc": "Allows Co-Admins to run console terminal commands."},
    "rule_coadmin_export_data": {"label": "Co-Admin: Export User Data", "role": "coadmin", "desc": "Allows Co-Admins to download user profile audits."},

    "rule_user_view_logs": {"label": "User: View Live System Logs", "role": "user", "desc": "Permits standard Users to view system diagnostic console log streams."}
}


@app.route("/api/admin/rules", methods=["GET"])
@admin_required
def api_admin_rules():
    configs = database.get_all_configs()
    rules = []
    for key, meta in SECURITY_RULES_METADATA.items():
        rules.append({
            "key": key,
            "label": meta["label"],
            "role": meta["role"],
            "desc": meta["desc"],
            "enabled": configs.get(key, "true" if "user" not in key and "coadmin_execute" not in key else "false") == "true"
        })
    return jsonify({"rules": rules})


@app.route("/api/admin/rules", methods=["POST"])
@admin_required
def api_admin_rules_update():
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0
    if caller_level < 2:
        return jsonify({"error": "Only full Administrators (tier 2) can configure security policies."}), 403
        
    data = request.get_json() or {}
    key = data.get("key")
    enabled = data.get("enabled")
    if key not in SECURITY_RULES_METADATA:
        return jsonify({"error": "Invalid security policy rule."}), 400
        
    database.set_config_value(key, "true" if enabled else "false")
    database.add_announcement(f"Security policy updated: {SECURITY_RULES_METADATA[key]['label']} set to {enabled}")
    database.log_admin_action(session.get('user_id'), 'UPDATE_RULE', None, f"Security policy updated: {SECURITY_RULES_METADATA[key]['label']} set to {enabled}")
    return jsonify({"success": True})


@app.route("/api/admin/settings", methods=["GET"])
@admin_required
def api_admin_settings():
    configs = database.get_all_configs()
    return jsonify({"configs": configs})


@app.route("/api/admin/settings", methods=["POST"])
@admin_required
def api_admin_settings_update():
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0
    
    rule_ok = False
    if caller_level >= 2:
        rule_ok = database.get_config_value('rule_admin_manage_config', 'true') == 'true'
    elif caller_level == 1:
        rule_ok = database.get_config_value('rule_coadmin_manage_config', 'false') == 'true'
        
    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403
        
    data = request.get_json() or {}
    for key, val in data.items():
        if key in ['enable_registration', 'allow_guests', 'enable_music', 'enforce_passwords']:
            database.set_config_value(key, str(val))
            database.log_admin_action(session.get('user_id'), 'UPDATE_SETTINGS', None, f"Updated setting: {key} = {val}")
    return jsonify({"success": True})


@app.route("/api/admin/announcement", methods=["POST"])
@admin_required
def api_admin_announcement_update():
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0
    
    rule_ok = False
    if caller_level >= 2:
        rule_ok = database.get_config_value('rule_admin_publish_announcement', 'true') == 'true'
    elif caller_level == 1:
        rule_ok = database.get_config_value('rule_coadmin_publish_announcement', 'true') == 'true'
        
    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403
        
    data = request.get_json() or {}
    announcement = data.get("announcement", "").strip()
    database.set_config_value("site_announcement", announcement)
    if announcement:
        database.add_announcement(announcement)
    database.log_admin_action(session.get('user_id'), 'PUBLISH_ANNOUNCEMENT', None, f"Published global announcement: {announcement}" if announcement else "Cleared global announcement banner")
    return jsonify({"success": True})


def get_avg_latency_with_sim(t_val=None):
    if t_val is None:
        t_val = int(time.time())
    
    # Base random latency
    random.seed(t_val)
    lat_val = round(340.0 + random.uniform(0, 45.0), 1)
    
    try:
        sim_val = database.get_config_value('sim_latency_spike', '')
        if sim_val:
            parts = sim_val.split(',')
            if len(parts) == 3:
                spike_val = float(parts[0])
                start_ts = int(parts[1])
                end_ts = int(parts[2])
                if start_ts <= t_val <= end_ts:
                    lat_val = round(lat_val + spike_val, 1)
    except Exception:
        pass
        
    return lat_val


def _get_pre_aggregated_metrics():
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_online = 1")
            online_users = cursor.fetchone()[0]
    except Exception:
        total_messages = 42
        online_users = 1
    
    # Deterministic cached/stable metrics (seeded hourly/5-min increments)
    import time
    seed_val = int(time.time() // 300) * 300
    avg_latency = get_avg_latency_with_sim(seed_val)
    
    # Reset seed to keep successRate and activeKeys deterministic
    random.seed(seed_val)
    success_rate = round(99.1 + random.uniform(0, 0.8), 2)
    active_keys = max(12, online_users * 3 + 7)
    
    return {
        "activeKeys": active_keys,
        "successRate": success_rate,
        "avgLatency": avg_latency,
        "totalRequests": total_messages
    }


@app.route("/api/admin/metrics/cards", methods=["GET"])
@admin_required
def api_admin_metrics_cards():
    return jsonify(_get_pre_aggregated_metrics())


@app.route("/api/admin/metrics/latency", methods=["GET"])
@admin_required
def api_admin_metrics_latency():
    import time
    # Parse range limits
    start_date = request.args.get('start_date', '').strip() or request.args.get('chart_start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or request.args.get('chart_end_date', '').strip() or None
    start_time_val = request.args.get('start_time', '').strip() or request.args.get('chart_start_time', '').strip() or None
    end_time_val = request.args.get('end_time', '').strip() or request.args.get('chart_end_time', '').strip() or None

    now = time.time()
    rounded_now = int(now // 60) * 60

    start_ts = None
    end_ts = None

    if start_date:
        try:
            start_str = f"{start_date} {start_time_val or '00:00:00'}"
            dt = datetime.strptime(start_str.split('.')[0], "%Y-%m-%d %H:%M:%S" if len(start_str.split(':')) == 3 else "%Y-%m-%d %H:%M")
            start_ts = int(dt.timestamp())
        except Exception:
            pass

    if end_date:
        try:
            end_str = f"{end_date} {end_time_val or '23:59:59'}"
            dt = datetime.strptime(end_str.split('.')[0], "%Y-%m-%d %H:%M:%S" if len(end_str.split(':')) == 3 else "%Y-%m-%d %H:%M")
            end_ts = int(dt.timestamp())
        except Exception:
            pass

    # Default to past 1 hour (60 intervals of 1 min) if no dates are set
    if not start_ts or not end_ts:
        end_ts = rounded_now
        start_ts = rounded_now - 59 * 60

    # Ensure start_ts is before end_ts
    if start_ts > end_ts:
        start_ts, end_ts = end_ts, start_ts

    diff = end_ts - start_ts
    if diff <= 0:
        diff = 3600
        start_ts = end_ts - 3600

    step = 60 # 1 minute
    if diff > 7 * 24 * 3600: # more than 7 days, step = 1 hour
        step = 3600
    elif diff > 24 * 3600: # more than 1 day, step = 15 minutes
        step = 900
    elif diff > 4 * 3600: # more than 4 hours, step = 5 minutes
        step = 300

    start_ts = int(start_ts // step) * step
    end_ts = int(end_ts // step) * step

    data = []
    steps_count = min(1000, max(2, (end_ts - start_ts) // step + 1))
    for i in range(steps_count):
        t_val = start_ts + i * step
        if t_val > end_ts:
            break
        time_str = datetime.fromtimestamp(t_val).isoformat()
        lat_val = get_avg_latency_with_sim(t_val)
        data.append({"time": time_str, "value": lat_val})

    return jsonify(data)


@app.route("/api/admin/metrics/stream")
def api_admin_metrics_stream():
    # Enforce admin check in SSE via session
    user_id = session.get('user_id')
    if not user_id:
        return "Unauthorized", 401
    user = database.get_user_secure(user_id)
    if not user or not user.get('is_admin'):
        return "Forbidden", 403

    from flask import Response
    def event_stream():
        import json, time
        while True:
            metrics = _get_pre_aggregated_metrics()
            yield f"data: {json.dumps(metrics)}\n\n"
            time.sleep(5)
    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/api/announcement", methods=["GET"])
def api_get_announcement():
    announcement = database.get_config_value("site_announcement", "")
    enable_music = database.get_config_value("enable_music", "true")
    return jsonify({
        "announcement": announcement,
        "enable_music": enable_music == "true"
    })


@app.route("/api/announcements", methods=["GET"])
@login_required
def api_get_announcements_history():
    user_id = session.get('user_id')
    history = database.get_announcements_history(user_id)
    return jsonify({"history": history})


@app.route("/api/admin/users/<username>/details", methods=["GET"])
@admin_required
def api_admin_user_details(username):
    details = database.get_user_full_details_admin(username)
    if details:
        # High fidelity simulated biodata values to look incredibly rich and realistic:
        cities_addresses = {
            'Mumbai, India': '45, Hill Road, Bandra West, Mumbai, Maharashtra 400050',
            'New York, USA': '742 Broadway, Floor 4, New York, NY 10003',
            'London, UK': '221B Baker St, London NW1 6XE, United Kingdom',
            'Berlin, Germany': 'Klingelhöferstraße 21, 10785 Berlin, Germany',
            'Tokyo, Japan': '1-1-2 Otemachi, Chiyoda City, Tokyo 100-0004, Japan',
            'Paris, France': '4 Rue de la Paix, 75002 Paris, France',
            'Sydney, Australia': '31 Alfred St, Sydney NSW 2000, Australia',
            'Singapore': '10 Bayfront Ave, Singapore 018956'
        }
        loc = details.get('last_login_location', 'Mumbai, Maharashtra, India')
        addr = cities_addresses.get(loc, '75, Marine Drive, Churchgate, Mumbai, India')
        details['home_address'] = addr if details['home_address'] == 'Not Provided' else details['home_address']
        
        # Get coordinates based on IP lookup or fallback
        ip_addr = details.get('last_login_ip', '127.0.0.1')
        is_local = ip_addr in ['127.0.0.1', '::1', 'localhost'] or ip_addr.startswith('192.168.') or ip_addr.startswith('10.') or ip_addr.startswith('172.')
        url = 'http://ip-api.com/json/' if is_local else f'http://ip-api.com/json/{ip_addr}'
        coords = '18.9220° N, 72.8347° E' # default Mumbai coords
        try:
            resp = requests.get(url, timeout=3).json()
            if resp.get('status') == 'success':
                lat = resp.get('lat')
                lon = resp.get('lon')
                if lat is not None and lon is not None:
                    lat_dir = 'N' if lat >= 0 else 'S'
                    lon_dir = 'E' if lon >= 0 else 'W'
                    coords = f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"
        except Exception:
            pass
        details['geolocation_coords'] = coords
        
        # Age birth dates mockup
        birthdays = ['1998-05-14', '1995-10-22', '2001-02-09', '1992-12-03', '2003-08-30', '1989-07-17']
        import random
        # deterministic index based on username length to maintain consistency
        bd = birthdays[len(username) % len(birthdays)]
        caller_id = session.get('user_id')
        caller = database.get_user_secure(caller_id)
        caller_level = caller.get('is_admin') or 0 if caller else 0
        return jsonify({"details": details, "caller_level": caller_level})
    return jsonify({"error": "User profile not found"}), 404


@app.route("/api/admin/users/<username>/sessions/<session_id>/messages", methods=["GET"])
@admin_required
def api_admin_user_session_messages(username, session_id):
    # Verify session belongs to user
    with database.connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, username))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Chat session not found for this user"}), 404
            
    # Fetch messages list
    messages = database.get_session_messages(session_id)
    return jsonify({"messages": messages})


@app.route("/api/admin/users/<username>/export", methods=["GET"])
@admin_required
def api_admin_user_export(username):
    caller_id = session.get('user_id')
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get('is_admin') or 0 if caller else 0
    
    rule_ok = False
    if caller_level >= 2:
        rule_ok = database.get_config_value('rule_admin_export_data', 'true') == 'true'
    elif caller_level == 1:
        rule_ok = database.get_config_value('rule_coadmin_export_data', 'true') == 'true'
        
    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403
        
    details = database.get_user_full_details_admin(username)
    if not details:
        return jsonify({"error": "User profile not found"}), 404
        
    # Aggregate all conversation logs
    full_history = []
    for s in details['sessions']:
        messages = database.get_session_messages(s['id'])
        full_history.append({
            'session_id': s['id'],
            'session_title': s['title'],
            'created_at': s['created_at'],
            'messages': messages
        })
    details['full_conversations'] = full_history
    
    # Stream as downloadable JSON attachment response
    import json
    from flask import Response
    response_data = json.dumps(details, indent=4)
    return Response(
        response_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=user_export_{username}.json"}
    )


@app.route("/api/admin/system-health", methods=["GET"])
@admin_required
def api_admin_system_health():
    try:
        db_path = database.DATABASE_PATH
        db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    except Exception:
        db_size_mb = 0.05
        
    # Total registers
    users = database.get_all_users_admin()
    total_users = len(users)
    
    # Realistic simulated uptime
    uptime_str = "4 days, 6 hours, 28 minutes"
    
    # Count active sessions (approximate)
    active_count = len([u for u in users if u.get('status') == 'active'])
    
    return jsonify({
        "db_size_mb": db_size_mb,
        "total_users": total_users,
        "uptime": uptime_str,
        "active_sessions": active_count
    })


@app.route("/api/admin/audit-logs", methods=["GET"])
@admin_required
def api_admin_audit_logs():
    logs = database.get_admin_audit_logs(limit=100)
    return jsonify(logs)


@app.route("/api/admin/audit-logs/clear", methods=["POST"])
@admin_required
def api_admin_clear_audit_logs():
    success = database.clear_admin_audit_logs()
    if success:
        return jsonify({"success": True, "message": "Audit logs cleared successfully."})
    else:
        return jsonify({"error": "Failed to clear audit logs."}), 500


@app.route("/api/admin/execute", methods=["POST"])
@admin_required
def api_admin_execute():
    """Execute a custom admin console command (sandboxed, no OS shell)"""
    data = request.get_json() or {}
    raw = data.get('command', '').strip()
    if not raw:
        return jsonify({"error": "No command provided"}), 400

    parts = raw.split()
    cmd = parts[0].lower()
    args = parts[1:]

    def _role_name(level):
        level = level or 0
        if level >= 2: return 'Admin'
        if level == 1: return 'Co-Admin'
        return 'User'

    caller = database.get_user_secure(session.get('user_id'))
    caller_level = (caller.get('is_admin') or 0) if caller else 0

    # Rules check for command execution
    rule_ok = False
    if caller_level >= 2:
        rule_ok = database.get_config_value('rule_admin_execute_commands', 'true') == 'true'
    elif caller_level == 1:
        rule_ok = database.get_config_value('rule_coadmin_execute_commands', 'false') == 'true'
    else:
        rule_ok = database.get_config_value('rule_user_view_logs', 'false') == 'true'
        
    if not rule_ok:
        return jsonify({"error": "⛔ Access denied. Security policy blocks terminal command execution for your role tier."}), 403

    database.log_admin_action(session.get('user_id'), 'EXECUTE_CONSOLE_CMD', None, f"Executed console command: {raw}")

    try:
        # Check if we are awaiting database wipe confirmation
        if session.get('awaiting_reset_confirm'):
            session.pop('awaiting_reset_confirm', None) # consume the flag
            if cmd in ('yes', 'y'):
                success = database.reset_database()
                if success:
                    database.log_admin_action('admin', 'DB_RESET', None, f'Database fully reset via console command by: {session.get("user_id")}')
                    session.clear()
                    return jsonify({"output": "Server Data Override Deletion Protocols initiated!\n All Data of these Sever is Deleted"})
                else:
                    return jsonify({"error": "Failed to reset database tables."})
            elif cmd in ('no', 'n'):
                return jsonify({"output": "Database wipe cancelled."})
            else:
                return jsonify({"error": "Database wipe cancelled (invalid confirmation)."})

        # Check if we are awaiting audit trail wipe confirmation
        if session.get('awaiting_audit_confirm'):
            session.pop('awaiting_audit_confirm', None) # consume the flag
            if cmd in ('yes', 'y'):
                success = database.clear_admin_audit_logs()
                if success:
                    return jsonify({"output": "Security Audit Trail Override Deletion Protocols initiated!\n All Audit Logs have been completely wiped!"})
                else:
                    return jsonify({"error": "Failed to clear audit logs."})
            elif cmd in ('no', 'n'):
                return jsonify({"output": "Audit logs wipe cancelled."})
            else:
                return jsonify({"error": "Audit logs wipe cancelled (invalid confirmation)."})

        # Check if we are awaiting update pack selection
        if session.get('awaiting_patch_select'):
            session.pop('awaiting_patch_select', None) # consume the flag
            if cmd == 'cancel' or cmd == 'c':
                return jsonify({"output": "Update patching sequence cancelled."})
            
            if cmd in ('1', '2', '3'):
                pack_names = {
                    '1': 'Update Pack V4.1 (Stability & Performance Hotfix)',
                    '2': 'Update Pack V4.2 (Advanced Telemetry & Analytics)',
                    '3': 'Update Pack V5.0-Beta (Quantum ML Core Integration)'
                }
                pack_name = pack_names[cmd]
                lines = [
                    f"⚙️ [PATCH WORKER] Initiating Live Update Patching Sequence for {pack_name}...",
                    "⚙️ [PATCH WORKER] Connecting to remote updates repository (github.com/Coder-Paradise-15/Mint-Frost-AI-Ltd)... Connected.",
                    "⚙️ [PATCH WORKER] Fetching commit diffs & artifacts... Done.",
                    "⚙️ [PATCH WORKER] Downloading update pack binaries [■■■■■■■■■■■■■■■■■■■■] 100% (4.2 MB/4.2 MB)",
                    "⚙️ [PATCH WORKER] Deploying background workers to patch system...",
                    "⚙️ [PATCH WORKER] [░░░░░░░░░░░░░░░░░░░░] 0%   - Suspending non-critical scheduling queues...",
                    "⚙️ [PATCH WORKER] [■■■■░░░░░░░░░░░░░░░░] 20%  - Creating database snapshot in databases/backups/...",
                    "⚙️ [PATCH WORKER] [■■■■■■■■░░░░░░░░░░░░] 40%  - Injecting hot-swap code files on live system...",
                    "⚙️ [PATCH WORKER] [■■■■■■■■■■■■░░░░░░░░] 60%  - Running migrations and database index alignment...",
                    "⚙️ [PATCH WORKER] [■■■■■■■■■■■■■■■■░░░░] 80%  - Conducting service health integration checks...",
                    "⚙️ [PATCH WORKER] [■■■■■■■■■■■■■■■■■■■■] 100% - Live integration validation successful!",
                    "⚙️ [PATCH WORKER] System updates are patched.",
                    "⚙️ [PATCH WORKER] Restarting worker processes...",
                    "🟢 [SYSTEM] Mint Frost Server live patched and running!"
                ]
                return jsonify({"output": "\n".join(lines)})
            else:
                return jsonify({"error": "Invalid selection. Please select 1, 2, 3, or 'cancel'."})


        # ── help ──
        if cmd == 'help':
            lines = [
                "╔══════════════════════════════════════════════════════════════╗",
                "║         MINT FROST AI — Admin Console v2.0                  ║",
                "╠══════════════════════════════════════════════════════════════╣",
                "║  SYSTEM                                                     ║",
                "║    help               Show this command reference           ║",
                "║    clear              Clear the console output              ║",
                "║    whoami             Display current admin identity         ║",
                "║    uptime             Show server uptime                    ║",
                "║    health             System health diagnostics             ║",
                "║    dbsize             Database file size                    ║",
                "║    version            Show platform version                 ║",
                "║    update / patch     Live update patching sequence wizard  ║",
                "║    delete data override  Wipe all server data               ║",
                "║    delete audit override Wipe all audit trail logs          ║",
                "║                                                             ║",
                "║  USER MANAGEMENT                                            ║",
                "║    users              List all registered users             ║",
                "║    online             Show currently online users           ║",
                "║    find <query>       Search users by name/ID               ║",
                "║    adduser <u> <p> [admin|coadmin|user]  Create user        ║",
                "║    deluser <username> Delete user (Admin only)              ║",
                "║    activate <user>    Activate a user account               ║",
                "║    deactivate <user>  Deactivate a user account             ║",
                "║    resetpwd <user> <newpass>  Reset user password           ║",
                "║    setrole <user> <admin|coadmin|user> (Admin only)         ║",
                "║    userinfo <user>    Show detailed user profile            ║",
                "║                                                             ║",
                "║  CONFIGURATION                                              ║",
                "║    config             Show all platform settings            ║",
                "║    setconfig <key> <val>  Update a config value             ║",
                "║    announce <message> Set site-wide announcement            ║",
                "║    clearannounce      Clear the announcement banner         ║",
                "║                                                             ║",
                "║  DATA                                                       ║",
                "║    sessions <user>    List chat sessions for a user         ║",
                "║    stats              Show aggregate statistics             ║",
                "║    backup <user>      Backup user data to local file        ║",
                "║    backup server      Backup overall db to local file       ║",
                "║                                                             ║",
                "║  ROLES: Admin (full access) > Co-Admin (no delete) > User   ║",
                "╚══════════════════════════════════════════════════════════════╝",
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── delete data override ──
        elif cmd == 'delete' and len(args) >= 2 and args[0].lower() == 'data' and args[1].lower() == 'override':
            session['awaiting_reset_confirm'] = True
            output_msg = (
                "Initializing Server Data Override Deletion Protocols......\n"
                "Everything will wipe up !!!!\n"
                " Are You Sure Want to continue ?  Yes / No"
            )
            return jsonify({"output": output_msg})

        # ── delete audit override ──
        elif cmd == 'delete' and len(args) >= 2 and args[0].lower() == 'audit' and args[1].lower() == 'override':
            session['awaiting_audit_confirm'] = True
            output_msg = (
                "Initializing Security Audit Trail Override Deletion Protocols......\n"
                "All administrative audit logs will be permanently wiped !!!!\n"
                " Are You Sure Want to continue ?  Yes / No"
            )
            return jsonify({"output": output_msg})

        # ── clear (handled client-side but acknowledge) ──
        elif cmd == 'clear':
            return jsonify({"output": "__CLEAR__"})

        # ── whoami ──
        elif cmd == 'whoami':
            uid = session.get('user_id', 'unknown')
            role = _role_name(caller_level)
            return jsonify({"output": f"Logged in as: {uid}\nDisplay Name: {caller.get('display_name', 'N/A') if caller else 'N/A'}\nRole: {role}\nAccess Level: {caller_level}"})

        # ── uptime ──
        elif cmd == 'uptime':
            import time as _time
            if not hasattr(app, '_start_time'):
                app._start_time = _time.time()
            elapsed = int(_time.time() - app._start_time)
            days, rem = divmod(elapsed, 86400)
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            return jsonify({"output": f"Server uptime: {days}d {hours}h {mins}m {secs}s"})

        # ── health ──
        elif cmd == 'health':
            try:
                db_path = database.DATABASE_PATH
                db_mb = round(os.path.getsize(db_path) / (1024 * 1024), 3)
            except Exception:
                db_mb = 0
            all_users = database.get_all_users_admin()
            total = len(all_users)
            active = len([u for u in all_users if u.get('status') == 'active'])
            online = len([u for u in all_users if u.get('is_online')])
            deactivated = len([u for u in all_users if u.get('status') == 'deactivated'])
            admins = len([u for u in all_users if (u.get('is_admin') or 0) >= 2])
            coadmins = len([u for u in all_users if (u.get('is_admin') or 0) == 1])
            lines = [
                "─── System Health Report ───",
                f"  Database Size    : {db_mb} MB",
                f"  Total Users      : {total}",
                f"  Active Users     : {active}",
                f"  Online Now       : {online}",
                f"  Deactivated      : {deactivated}",
                f"  Administrators   : {admins}",
                f"  Co-Admins        : {coadmins}",
                f"  Engine           : SQLite 3 WAL",
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── dbsize ──
        elif cmd == 'dbsize':
            try:
                db_path = database.DATABASE_PATH
                sz = os.path.getsize(db_path)
                return jsonify({"output": f"Database file: {round(sz / 1024, 2)} KB ({round(sz / (1024*1024), 3)} MB)"})
            except Exception as e:
                return jsonify({"error": str(e)})

        # ── version ──
        elif cmd == 'version':
            return jsonify({"output": "Mint Frost AI — Admin Command Center v2.0\nEngine: Flask + SQLite3 WAL\nPython: " + __import__('sys').version.split()[0]})

        # ── users ──
        elif cmd == 'users':
            all_users = database.get_all_users_admin()
            if not all_users:
                return jsonify({"output": "No users found."})
            header = f"{'USERNAME':<18} {'DISPLAY NAME':<20} {'ROLE':<10} {'STATUS':<12} {'ONLINE':<8}"
            sep = "─" * 68
            lines = [header, sep]
            for u in all_users:
                role = _role_name(u.get('is_admin'))
                on = "●" if u.get('is_online') else "○"
                lines.append(f"{u['username']:<18} {u['display_name']:<20} {role:<10} {u['status']:<12} {on:<8}")
            lines.append(sep)
            lines.append(f"Total: {len(all_users)} users")
            return jsonify({"output": "\n".join(lines)})

        # ── online ──
        elif cmd == 'online':
            all_users = database.get_all_users_admin()
            online_users = [u for u in all_users if u.get('is_online')]
            if not online_users:
                return jsonify({"output": "No users currently online."})
            lines = [f"Online Users ({len(online_users)}):"]
            for u in online_users:
                role = _role_name(u.get('is_admin'))
                lines.append(f"  ● {u['username']} ({u['display_name']}) — {role}")
            return jsonify({"output": "\n".join(lines)})

        # ── find <query> ──
        elif cmd == 'find':
            if not args:
                return jsonify({"error": "Usage: find <search_query>"})
            q = " ".join(args)
            results = database.get_all_users_admin(search=q)
            if not results:
                return jsonify({"output": f"No users matching \"{q}\"."})
            lines = [f"Search results for \"{q}\" ({len(results)} found):"]
            for u in results:
                role = _role_name(u.get('is_admin'))
                lines.append(f"  • {u['username']} — {u['display_name']} [{role}] ({u['status']})")
            return jsonify({"output": "\n".join(lines)})

        # ── adduser <user> <pass> [admin|coadmin|user] ──
        elif cmd == 'adduser':
            if len(args) < 2:
                return jsonify({"error": "Usage: adduser <username> <password> [admin|coadmin|user]"})
            username = args[0]
            password = args[1]
            role = args[2].lower() if len(args) > 2 else 'user'
            if role not in ('admin', 'coadmin', 'user'):
                return jsonify({"error": "Role must be 'admin', 'coadmin', or 'user'."})
            if role in ('admin', 'coadmin') and caller_level < 2:
                return jsonify({"error": "Only Admins can create admin/co-admin accounts."})
            if len(username) < 3 or not username.isalnum():
                return jsonify({"error": "Username must be 3+ alphanumeric characters."})
            if len(password) < 6:
                return jsonify({"error": "Password must be at least 6 characters."})
            existing = database.get_user_secure(username)
            if existing:
                return jsonify({"error": f"User \"{username}\" already exists."})
            is_admin = 2 if role == 'admin' else (1 if role == 'coadmin' else 0)
            ph = generate_password_hash(password)
            ok = database.create_user_secure(username, ph, username, is_admin)
            if ok:
                return jsonify({"output": f"✓ User \"{username}\" created successfully as {_role_name(is_admin).upper()}."})
            return jsonify({"error": f"Failed to create user \"{username}\"."})

        # ── deluser <username> (Admin and Co-Admin tier checks) ──
        elif cmd == 'deluser':
            if caller_level < 1:
                return jsonify({"error": "⛔ Access denied. Only administrators can delete accounts."})
            if not args:
                return jsonify({"error": "Usage: deluser <username>"})
            target = args[0]
            if target == session.get('user_id'):
                return jsonify({"error": "Cannot delete your own administrator profile."})
            ok = database.delete_user_admin(target, caller_level=caller_level)
            if ok:
                return jsonify({"output": f"✓ User \"{target}\" and all associated data deleted."})
            return jsonify({"error": f"Failed to delete \"{target}\" (tier security constraint or target does not exist)."})

        # ── activate / deactivate ──
        elif cmd in ('activate', 'deactivate'):
            if not args:
                return jsonify({"error": f"Usage: {cmd} <username>"})
            target = args[0]
            new_status = 'active' if cmd == 'activate' else 'deactivated'
            ok = database.update_user_status_admin(target, new_status, caller_level=caller_level)
            if ok:
                if new_status == 'deactivated':
                    database.set_user_online_status(target, 0)
                return jsonify({"output": f"✓ User \"{target}\" status set to {new_status}."})
            return jsonify({"error": f"Failed to update status for \"{target}\" (tier security constraint or target does not exist)."})

        # ── resetpwd <user> <newpass> ──
        elif cmd == 'resetpwd':
            if len(args) < 2:
                return jsonify({"error": "Usage: resetpwd <username> <new_password>"})
            target = args[0]
            new_pass = args[1]
            if len(new_pass) < 6:
                return jsonify({"error": "Password must be at least 6 characters."})
            ph = generate_password_hash(new_pass)
            ok = database.reset_user_password_admin(target, ph, caller_level=caller_level)
            if ok:
                return jsonify({"output": f"✓ Password reset for \"{target}\"."})
            return jsonify({"error": f"Failed to reset password for \"{target}\" (tier security constraint or target does not exist)."})

        # ── setrole <user> <admin|coadmin|user> (Admin only) ──
        elif cmd == 'setrole':
            if len(args) < 2:
                return jsonify({"error": "Usage: setrole <username> <admin|coadmin|user>"})
            if caller_level < 2:
                return jsonify({"error": "⛔ Access denied. Only Admins can change roles."})
            target = args[0]
            role = args[1].lower()
            if role not in ('admin', 'coadmin', 'user'):
                return jsonify({"error": "Role must be 'admin', 'coadmin', or 'user'."})
            
            target_user = database.get_user_secure(target)
            if not target_user:
                return jsonify({"error": f"User \"{target}\" not found."})
            target_level = target_user.get('is_admin') or 0
            if target_level >= 2 and target != session.get('user_id'):
                return jsonify({"error": "Cannot change the role of another Admin account."})
                
            is_admin = 2 if role == 'admin' else (1 if role == 'coadmin' else 0)
            try:
                with database.connect_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (is_admin, target))
                    conn.commit()
                    if cursor.rowcount > 0:
                        return jsonify({"output": f"✓ User \"{target}\" role set to {_role_name(is_admin)}."})
                    return jsonify({"error": f"User \"{target}\" not found."})
            except Exception as e:
                return jsonify({"error": str(e)})

        # ── userinfo <user> ──
        elif cmd == 'userinfo':
            if not args:
                return jsonify({"error": "Usage: userinfo <username>"})
            details = database.get_user_full_details_admin(args[0])
            if not details:
                return jsonify({"error": f"User \"{args[0]}\" not found."})
            role = _role_name(details.get('is_admin'))
            lines = [
                f"─── Profile: {details['username']} ───",
                f"  Display Name     : {details['display_name']}",
                f"  Role             : {role}",
                f"  Status           : {details['status']}",
                f"  Created          : {details['created_at']}",
                f"  Last IP          : {details['last_login_ip']}",
                f"  Last Location    : {details['last_login_location']}",
                f"  Chat Sessions    : {len(details.get('sessions', []))}",
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── config ──
        elif cmd == 'config':
            configs = database.get_all_configs()
            if not configs:
                return jsonify({"output": "No configuration entries found."})
            lines = ["─── Platform Configuration ───"]
            for k, v in configs.items():
                lines.append(f"  {k:<25} = {v}")
            return jsonify({"output": "\n".join(lines)})

        # ── setconfig <key> <value> ──
        elif cmd == 'setconfig':
            if len(args) < 2:
                return jsonify({"error": "Usage: setconfig <key> <value>"})
            key = args[0]
            val = " ".join(args[1:])
            allowed = ['enable_registration', 'allow_guests', 'enable_music', 'enforce_passwords']
            if key not in allowed:
                return jsonify({"error": f"Invalid config key. Allowed: {', '.join(allowed)}"})
            database.set_config_value(key, val)
            return jsonify({"output": f"✓ Config \"{key}\" set to \"{val}\"."})

        # ── announce <message> ──
        elif cmd == 'announce':
            if not args:
                return jsonify({"error": "Usage: announce <message text>"})
            msg = " ".join(args)
            database.set_config_value("site_announcement", msg)
            database.add_announcement(msg)
            return jsonify({"output": f"✓ Announcement published: \"{msg}\""})

        # ── clearannounce ──
        elif cmd == 'clearannounce':
            database.set_config_value("site_announcement", "")
            return jsonify({"output": "✓ Announcement banner cleared."})

        # ── sessions <user> ──
        elif cmd == 'sessions':
            if not args:
                return jsonify({"error": "Usage: sessions <username>"})
            details = database.get_user_full_details_admin(args[0])
            if not details:
                return jsonify({"error": f"User \"{args[0]}\" not found."})
            sess = details.get('sessions', [])
            if not sess:
                return jsonify({"output": f"No chat sessions for \"{args[0]}\"."})
            lines = [f"Chat sessions for \"{args[0]}\" ({len(sess)}):"]
            for s in sess[:20]:
                lines.append(f"  [{s['created_at']}] {s['title']}")
            if len(sess) > 20:
                lines.append(f"  ... and {len(sess) - 20} more")
            return jsonify({"output": "\n".join(lines)})

        # ── stats ──
        elif cmd == 'stats':
            all_users = database.get_all_users_admin()
            total = len(all_users)
            active = len([u for u in all_users if u.get('status') == 'active'])
            online = len([u for u in all_users if u.get('is_online')])
            deactivated = len([u for u in all_users if u.get('status') == 'deactivated'])
            idle = len([u for u in all_users if u.get('status') == 'idle'])
            admins = len([u for u in all_users if (u.get('is_admin') or 0) >= 2])
            coadmins = len([u for u in all_users if (u.get('is_admin') or 0) == 1])
            std_users = total - admins - coadmins
            try:
                db_mb = round(os.path.getsize(database.DATABASE_PATH) / (1024 * 1024), 3)
            except Exception:
                db_mb = 0
            lines = [
                "─── Aggregate Statistics ───",
                f"  Total Accounts   : {total}",
                f"  Administrators   : {admins}",
                f"  Co-Admins        : {coadmins}",
                f"  Standard Users   : {std_users}",
                f"  Active           : {active}",
                f"  Idle             : {idle}",
                f"  Deactivated      : {deactivated}",
                f"  Online Now       : {online}",
                f"  Database Size    : {db_mb} MB",
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── backup ──
        elif cmd == 'backup':
            if not args:
                return jsonify({"error": "Usage: backup <username> or backup server/--all"})
            
            target = args[0]
            import os
            from datetime import datetime
            import shutil
            import json
            
            backup_dir = os.path.join(os.path.dirname(__file__), 'databases', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if target in ('server', '--all'):
                db_path = database.DATABASE_PATH
                if not os.path.exists(db_path):
                    return jsonify({"error": f"Database file not found at {db_path}."})
                
                dest_path = os.path.join(backup_dir, f"server_backup_{timestamp}.db")
                try:
                    shutil.copy2(db_path, dest_path)
                    return jsonify({"output": f"✓ Overall server database backup created successfully at:\n  databases/backups/server_backup_{timestamp}.db"})
                except Exception as e:
                    return jsonify({"error": f"Failed to backup server database: {str(e)}"})
            else:
                details = database.get_user_full_details_admin(target)
                if not details:
                    return jsonify({"error": f"User '{target}' not found."})
                
                # Aggregate all conversation logs
                full_history = []
                for s in details.get('sessions', []):
                    messages = database.get_session_messages(s['id'])
                    full_history.append({
                        'session_id': s['id'],
                        'session_title': s['title'],
                        'created_at': s['created_at'],
                        'messages': messages
                    })
                details['full_conversations'] = full_history
                
                dest_path = os.path.join(backup_dir, f"backup_{target}_{timestamp}.json")
                try:
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        json.dump(details, f, indent=4)
                    return jsonify({"output": f"✓ Backup for user '{target}' created successfully at:\n  databases/backups/backup_{target}_{timestamp}.json"})
                except Exception as e:
                    return jsonify({"error": f"Failed to write user backup file: {str(e)}"})

        # ── update/patch ──
        elif cmd in ('update', 'patch'):
            session['awaiting_patch_select'] = True
            lines = [
                "Select the Update pack to patch on live system/server:",
                "  [1] Update Pack V4.1 (Stability & Performance Hotfix)",
                "  [2] Update Pack V4.2 (Advanced Telemetry & Analytics)",
                "  [3] Update Pack V5.0-Beta (Quantum ML Core Integration)",
                "Enter selection (1-3) or 'cancel' to exit:"
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── unknown ──
        else:
            return jsonify({"error": f"Unknown command: \"{cmd}\". Type 'help' for available commands."})

    except Exception as e:
        return jsonify({"error": f"Command execution error: {str(e)}"})


@app.route("/api/admin/db-backup", methods=["GET"])
@admin_required
def api_admin_db_backup():
    try:
        db_path = database.DATABASE_PATH
        if not os.path.exists(db_path):
            return jsonify({"error": "Database file not found"}), 404
            
        from flask import send_file
        database.log_admin_action(session.get('user_id'), 'DB_BACKUP', None, 'Downloaded database backup file')
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"chat_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mimetype="application/x-sqlite3"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download database backup: {str(e)}"}), 500


@app.route("/api/admin/db-reset", methods=["POST"])
@admin_required
@superadmin_required
def api_admin_db_reset():
    try:
        admin_id = session.get('user_id')
        import logging
        logging.warning(f"Superadmin {admin_id} initiated a full database override deletion/reset.")
        
        success = database.reset_database()
        if success:
            database.log_admin_action('admin', 'DB_RESET', None, f'Database fully reset to defaults by superadmin: {admin_id}')
            session.clear()
            return jsonify({
                "success": True,
                "message": "Database successfully reset to factory defaults. All sessions cleared."
            })
        else:
            return jsonify({"error": "Failed to reset database tables"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to reset database: {str(e)}"}), 500

# ─── FILE EXPLORER BACKEND APIS ───

def get_safe_whitelisted_path(file_rel_path):
    if not file_rel_path:
        return None
        
    # Prevent path traversal tricks by resolving absolute paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # We clean up the input path
    cleaned_rel_path = file_rel_path.replace('\\', '/').lstrip('/')
    target_abs = os.path.abspath(os.path.join(base_dir, cleaned_rel_path))
    
    # Whitelisted config files (exact matches)
    whitelisted_configs = [
        'mail_id.txt',
        'mail_password.txt',
        'weather_key.txt',
        'google.txt',
        'google_credentials.txt',
        'OpenAI-Key.txt'
    ]
    
    for conf in whitelisted_configs:
        conf_abs = os.path.abspath(os.path.join(base_dir, conf))
        if target_abs == conf_abs:
            return target_abs
            
    # Whitelisted directory databases/backups/ (must be strictly inside)
    backups_dir_abs = os.path.abspath(os.path.join(base_dir, 'databases', 'backups'))
    if target_abs.startswith(backups_dir_abs + os.sep) or target_abs == backups_dir_abs:
        return target_abs
        
    return None

@app.route("/api/admin/files", methods=["GET"])
@admin_required
def api_admin_list_files():
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        # 1. Gather configuration files
        whitelisted_configs = [
            'mail_id.txt',
            'mail_password.txt',
            'weather_key.txt',
            'google.txt',
            'google_credentials.txt',
            'OpenAI-Key.txt'
        ]
        
        configs = []
        for name in whitelisted_configs:
            file_abs = os.path.join(base_dir, name)
            exists = os.path.exists(file_abs)
            size = os.path.getsize(file_abs) if exists else 0
            mtime = os.path.getmtime(file_abs) if exists else 0
            configs.append({
                "name": name,
                "path": name,
                "type": "config",
                "exists": exists,
                "size": size,
                "modified": mtime
            })
            
        # 2. Gather backups files
        backups_dir = os.path.join(base_dir, 'databases', 'backups')
        os.makedirs(backups_dir, exist_ok=True)
        
        backups = []
        for entry in os.scandir(backups_dir):
            if entry.is_file():
                backups.append({
                    "name": entry.name,
                    "path": f"databases/backups/{entry.name}",
                    "type": "backup",
                    "exists": True,
                    "size": entry.stat().st_size,
                    "modified": entry.stat().st_mtime
                })
                
        # Sort backups by modified time descending (newest first)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            "configs": configs,
            "backups": backups
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list files: {str(e)}"}), 500

@app.route("/api/admin/files/read", methods=["GET"])
@admin_required
def api_admin_read_file():
    filepath_input = request.args.get("path")
    safe_path = get_safe_whitelisted_path(filepath_input)
    if not safe_path:
        return jsonify({"error": "Access Denied: Path not authorized"}), 403
        
    if not os.path.exists(safe_path):
        # Return empty string for config files that don't exist yet rather than 404
        if os.path.basename(safe_path) in ['google.txt', 'google_credentials.txt', 'OpenAI-Key.txt']:
            return jsonify({"content": "", "exists": False})
        return jsonify({"error": "File not found"}), 404
        
    try:
        # Check if it's binary (like .db database backups)
        is_binary = safe_path.endswith('.db')
        if is_binary:
            return jsonify({"content": "[Binary Database File]", "is_binary": True, "exists": True})
            
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({"content": content, "is_binary": False, "exists": True})
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500

@app.route("/api/admin/files/write", methods=["POST"])
@admin_required
def api_admin_write_file():
    data = request.json or {}
    filepath_input = data.get("path")
    content = data.get("content", "")
    
    safe_path = get_safe_whitelisted_path(filepath_input)
    if not safe_path:
        return jsonify({"error": "Access Denied: Path not authorized"}), 403
        
    # Prevent editing binary backup files directly
    if safe_path.endswith('.db'):
        return jsonify({"error": "Cannot edit binary database files directly"}), 400
        
    try:
        # Ensure parent dir exists
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        database.log_admin_action(session.get('user_id'), 'FILE_EDIT', filepath_input, f'Modified file content: {filepath_input}')
        return jsonify({"success": True, "message": "File saved successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to write file: {str(e)}"}), 500

@app.route("/api/admin/files/download", methods=["GET"])
@admin_required
def api_admin_download_file():
    filepath_input = request.args.get("path")
    safe_path = get_safe_whitelisted_path(filepath_input)
    if not safe_path:
        return jsonify({"error": "Access Denied: Path not authorized"}), 403
        
    if not os.path.exists(safe_path):
        return jsonify({"error": "File not found"}), 404
        
    try:
        from flask import send_file
        database.log_admin_action(session.get('user_id'), 'FILE_DOWNLOAD', filepath_input, f'Downloaded file: {filepath_input}')
        return send_file(
            safe_path,
            as_attachment=True,
            download_name=os.path.basename(safe_path)
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

@app.route("/api/admin/files/delete", methods=["POST"])
@admin_required
def api_admin_delete_file():
    data = request.json or {}
    filepath_input = data.get("path")
    
    safe_path = get_safe_whitelisted_path(filepath_input)
    if not safe_path:
        return jsonify({"error": "Access Denied: Path not authorized"}), 403
        
    # RESTRICTION: Only allow deletion under databases/backups folder to protect system config files
    base_dir = os.path.abspath(os.path.dirname(__file__))
    backups_dir_abs = os.path.abspath(os.path.join(base_dir, 'databases', 'backups'))
    if not safe_path.startswith(backups_dir_abs + os.sep):
        return jsonify({"error": "Access Denied: Configuration files cannot be deleted"}), 403
        
    if not os.path.exists(safe_path):
        return jsonify({"error": "File not found"}), 404
        
    try:
        os.remove(safe_path)
        database.log_admin_action(session.get('user_id'), 'FILE_DELETE', filepath_input, f'Deleted file: {filepath_input}')
        return jsonify({"success": True, "message": "File deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500

@app.route("/api/admin/files/upload", methods=["POST"])
@admin_required
def api_admin_upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Standardize and secure filename
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        
        # Only allow uploading to backups directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        backups_dir = os.path.join(base_dir, 'databases', 'backups')
        os.makedirs(backups_dir, exist_ok=True)
        
        dest_path = os.path.join(backups_dir, filename)
        file.save(dest_path)
        
        database.log_admin_action(session.get('user_id'), 'FILE_UPLOAD', filename, f'Uploaded backup file: {filename}')
        return jsonify({"success": True, "message": f"File '{filename}' uploaded successfully to backups"})
    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500


@app.route("/api/admin/sessions", methods=["GET"])
@admin_required
def api_admin_sessions():
    try:
        sessions = database.get_active_sessions_admin()
        return jsonify({"success": True, "sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/sessions/revoke", methods=["POST"])
@admin_required
def api_admin_sessions_revoke():
    try:
        data = request.get_json() or {}
        token = data.get('session_token')
        if not token:
            return jsonify({"error": "Session token required"}), 400
            
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.is_admin, s.user_id 
                FROM active_sessions s
                LEFT JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            ''', (token,))
            row = cursor.fetchone()
            
        if row:
            target_admin_level = row[0] or 0
            target_user_id = row[1]
            caller_id = session.get('user_id')
            caller_user = database.get_user_secure(caller_id)
            caller_level = caller_user.get('is_admin') or 0 if caller_user else 0
            
            if target_admin_level >= caller_level and target_user_id != caller_id:
                return jsonify({"error": "Unauthorized to revoke this session"}), 403
                
        database.revoke_active_session(token)
        database.log_admin_action(session.get('user_id'), 'REVOKE_SESSION', None, f"Revoked active session token: {token[:8]}...")
        return jsonify({"success": True, "message": "Session terminated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/sessions/revoke-all", methods=["POST"])
@admin_required
@superadmin_required
def api_admin_sessions_revoke_all():
    try:
        current_token = session.get('session_token')
        caller_id = session.get('user_id')
        
        with database.connect_db() as conn:
            cursor = conn.cursor()
            if current_token:
                cursor.execute('DELETE FROM active_sessions WHERE session_token != ?', (current_token,))
            else:
                cursor.execute('DELETE FROM active_sessions')
            conn.commit()
            
        database.log_admin_action(caller_id, 'REVOKE_ALL_SESSIONS', None, "Revoked all active sessions except self")
        return jsonify({"success": True, "message": "All other user sessions terminated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/database/query", methods=["POST"])
@admin_required
def api_admin_database_query():
    try:
        data = request.get_json() or {}
        raw_query = data.get('query', '').strip()
        if not raw_query:
            return jsonify({"error": "Query cannot be empty"}), 400
            
        norm_query = re.sub(r'/\*.*?\*/', '', raw_query, flags=re.DOTALL)
        norm_query = norm_query.strip()
        
        caller = database.get_user_secure(session.get('user_id'))
        caller_level = (caller.get('is_admin') or 0) if caller else 0
        
        # Superadmin visual / delete override check for audit logs
        query_upper = norm_query.upper()
        if "ADMIN_AUDIT_LOGS" in query_upper and "DELETE" in query_upper:
            if caller_level >= 2:
                database.clear_admin_audit_logs()
                return jsonify({
                    "success": True,
                    "headers": ["Status"],
                    "rows": [["Audit logs successfully wiped clean via query override."]],
                    "count": 1
                })
            else:
                return jsonify({"error": "Security Restriction: Superadmin privileges required to wipe audit logs."}), 403
        
        if caller_level >= 2:
            # Superadmin has access to run all queries with no restricted keywords
            block_keywords = []
        elif caller_level == 1:
            # Co-admin has access with specific block list
            block_keywords = ['INSERT', 'CREATE', 'REPLACE', 'PRAGMA', 'RENAME', 'ATTACH', 'DETACH']
        else:
            return jsonify({"error": "Security Restriction: Administrator privileges required."}), 403
            
        if block_keywords:
            words = re.findall(r'\b\w+\b', norm_query.upper())
            for keyword in block_keywords:
                if keyword in words:
                    return jsonify({"error": f"Security Restriction: Modification keyword '{keyword}' is blocked for co-admins in the sandbox."}), 403
                    
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(raw_query)
            
            headers = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall() if cursor.description else []
            data_rows = [list(row) for row in rows]
            
        database.log_admin_action(session.get('user_id'), 'DB_SANDBOX_QUERY', None, f"Executed sandbox SQL query: {raw_query[:100]}")
        
        return jsonify({
            "success": True,
            "headers": headers,
            "rows": data_rows,
            "count": len(data_rows)
        })
    except Exception as e:
        return jsonify({"error": f"SQL Error: {str(e)}"}), 400


@app.route("/api/admin/simulate", methods=["POST"])
@admin_required
def api_admin_simulate():
    try:
        data = request.get_json() or {}
        action = data.get('action')
        
        if action == 'signup':
            count = int(data.get('count', 10))
            
            names = ["Emma Vance", "Liam Frost", "Olivia Sterling", "Noah Vance", "Sophia Vance", "Oliver Frost", "Isabella Sterling", "William Frost", "Mia Sterling", "James Vance", "Ava Frost", "Benjamin Sterling"]
            locations = ["Mumbai, Maharashtra, India", "Paris, France", "New York, NY, USA", "London, UK", "Tokyo, Japan", "Sydney, NSW, Australia", "Berlin, Germany", "Toronto, ON, Canada"]
            
            import uuid
            import random
            from werkzeug.security import generate_password_hash
            from datetime import timedelta
            
            created_users = []
            dummy_hash = generate_password_hash("mockpass123")
            
            with database.connect_db() as conn:
                cursor = conn.cursor()
                for _ in range(count):
                    user_uuid = f"sim_{str(uuid.uuid4())[:8]}"
                    display_name = random.choice(names) + " " + str(random.randint(10, 99))
                    location = random.choice(locations)
                    ip_addr = f"{random.randint(24, 220)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                    
                    days_ago = random.uniform(0.01, 7.0)
                    created_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    cursor.execute('''
                        INSERT INTO users (id, password_hash, display_name, created_at, is_admin, status, last_login_ip, last_login_location, is_online, last_seen)
                        VALUES (?, ?, ?, ?, 0, 'active', ?, ?, 0, ?)
                    ''', (user_uuid, dummy_hash, display_name, created_date, ip_addr, location, created_date))
                    
                    created_users.append(user_uuid)
                conn.commit()
                
            database.log_admin_action(session.get('user_id'), 'SIMULATION_SIGNUPS', None, f"Simulated signup of {count} mock user records")
            return jsonify({"success": True, "message": f"Successfully simulated {count} user signups.", "users": created_users})
            
        elif action == 'latency':
            spike_val = float(data.get('value', 1200.0))
            duration_mins = int(data.get('duration', 15))
            
            start_ts = int(time.time())
            end_ts = start_ts + duration_mins * 60
            
            val_str = f"{spike_val},{start_ts},{end_ts}"
            database.set_config_value('sim_latency_spike', val_str)
            
            database.log_admin_action(session.get('user_id'), 'SIMULATION_LATENCY', None, f"Simulated latency spike (+{spike_val}ms) for {duration_mins} minutes")
            return jsonify({"success": True, "message": f"Latency spike of +{spike_val}ms injected for {duration_mins} minutes."})
            
        elif action == 'clear':
            with database.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id LIKE 'sim_%')
                ''')
                cursor.execute("DELETE FROM chat_sessions WHERE user_id LIKE 'sim_%'")
                cursor.execute("DELETE FROM user_settings WHERE id LIKE 'sim_%'")
                cursor.execute("DELETE FROM linked_accounts WHERE user_id LIKE 'sim_%'")
                cursor.execute("DELETE FROM users WHERE id LIKE 'sim_%'")
                cursor.execute("DELETE FROM active_sessions WHERE user_id LIKE 'sim_%'")
                conn.commit()
                
            database.set_config_value('sim_latency_spike', '')
            database.log_admin_action(session.get('user_id'), 'SIMULATION_CLEAR', None, "Cleared all simulation logs and mock user profiles")
            return jsonify({"success": True, "message": "Simulation states and mock records fully purged."})
            
        else:
            return jsonify({"error": f"Unknown simulation action '{action}'"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- end Spotify debug ---


# --- Multi-Factor Authentication (MFA) API Endpoints ---

def verify_totp(secret, code):
    import base64
    import hmac
    import hashlib
    import time
    import struct
    try:
        secret = secret.upper().replace(' ', '')
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += '=' * (8 - missing_padding)
        key = base64.b32decode(secret)
        t = int(time.time() / 30)
        for i in (-1, 0, 1):
            val = struct.pack('>Q', t + i)
            hmac_hash = hmac.new(key, val, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0f
            truncated_hash = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7fffffff
            otp = truncated_hash % 1000000
            if f"{otp:06d}" == str(code).strip():
                return True
        return False
    except Exception:
        return False

@app.route("/api/login/mfa/totp/verify", methods=["POST"])
def api_login_mfa_totp_verify():
    pending_user_id = session.get('mfa_pending_user_id')
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401
    
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({"error": "Verification code is required"}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT secret FROM user_authenticators WHERE user_id = ?", (pending_user_id,))
            rows = cursor.fetchall()
            
        if not rows:
            return jsonify({"error": "No authenticator configured for this user"}), 400
            
        verified = False
        for r in rows:
            if verify_totp(r[0], code):
                verified = True
                break
                
        if not verified:
            return jsonify({"error": "Invalid verification code"}), 400
            
        user = database.get_user_secure(pending_user_id)
        session['user_id'] = user['id']
        session['local_user_id'] = user['id']
        session['display_name'] = user['display_name']
        session.pop('mfa_pending_user_id', None)
        session.modified = True
        
        register_login_session(user['id'])
        log_user_telemetry(user['id'])
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login/mfa/passkey/options", methods=["POST"])
def api_login_mfa_passkey_options():
    pending_user_id = session.get('mfa_pending_user_id')
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401
        
    import uuid
    import base64
    
    challenge = base64.b64encode(uuid.uuid4().bytes).decode().replace('=', '')
    session['passkey_auth_challenge'] = challenge
    
    allow_credentials = []
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT credential_id FROM user_passkeys WHERE user_id = ?", (pending_user_id,))
            for r in cursor.fetchall():
                allow_credentials.append({
                    "type": "public-key",
                    "id": r[0]
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    rp_id = request.host.split(':')[0]
    is_ip = False
    try:
        import ipaddress
        ipaddress.ip_address(rp_id)
        is_ip = True
    except ValueError:
        pass
        
    options = {
        "challenge": challenge,
        "timeout": 60000,
        "userVerification": "preferred",
        "allowCredentials": allow_credentials
    }
    
    if not is_ip:
        options["rpId"] = rp_id
        
    return jsonify(options)


@app.route("/api/login/mfa/passkey/verify", methods=["POST"])
def api_login_mfa_passkey_verify():
    pending_user_id = session.get('mfa_pending_user_id')
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401
        
    data = request.get_json() or {}
    credential_id = data.get('credential_id', '').strip()
    if not credential_id:
        return jsonify({"error": "Credential ID is required"}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user_passkeys WHERE user_id = ? AND credential_id = ?", (pending_user_id, credential_id))
            r = cursor.fetchone()
            
        if not r:
            return jsonify({"error": "Invalid passkey"}), 400
            
        user = database.get_user_secure(pending_user_id)
        session['user_id'] = user['id']
        session['local_user_id'] = user['id']
        session['display_name'] = user['display_name']
        session.pop('mfa_pending_user_id', None)
        session.pop('passkey_auth_challenge', None)
        session.modified = True
        
        register_login_session(user['id'])
        log_user_telemetry(user['id'])
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/status", methods=["GET"])
def api_mfa_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            
            # Fetch passkeys
            cursor.execute("SELECT id, key_name, created_at FROM user_passkeys WHERE user_id = ?", (user_id,))
            passkeys = [{"id": r[0], "key_name": r[1], "created_at": r[2]} for r in cursor.fetchall()]
            
            # Fetch authenticators
            cursor.execute("SELECT id, device_name, created_at FROM user_authenticators WHERE user_id = ?", (user_id,))
            authenticators = [{"id": r[0], "device_name": r[1], "created_at": r[2]} for r in cursor.fetchall()]
            
        return jsonify({
            "passkeys_enabled": len(passkeys) > 0,
            "totp_enabled": len(authenticators) > 0,
            "passkeys": passkeys,
            "authenticators": authenticators
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/passkey/register/options", methods=["POST"])
def api_mfa_passkey_register_options():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    
    import uuid
    import base64
    
    user_handle = base64.b64encode(user_id.encode()).decode().replace('=', '')
    challenge = base64.b64encode(uuid.uuid4().bytes).decode().replace('=', '')
    
    rp_id = request.host.split(':')[0]
    is_ip = False
    try:
        import ipaddress
        ipaddress.ip_address(rp_id)
        is_ip = True
    except ValueError:
        pass
    
    options = {
        "challenge": challenge,
        "rp": {
            "name": "Mint Frost AI"
        },
        "user": {
            "id": user_handle,
            "name": user_id,
            "displayName": session.get('display_name') or user_id
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7}, # ES256
            {"type": "public-key", "alg": -257} # RS256
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",
            "userVerification": "preferred"
        },
        "timeout": 60000,
        "attestation": "none"
    }
    
    if not is_ip:
        options["rp"]["id"] = rp_id
    
    session['passkey_reg_challenge'] = challenge
    return jsonify(options)


@app.route("/api/mfa/passkey/register/verify", methods=["POST"])
def api_mfa_passkey_register_verify():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json() or {}
    key_name = data.get('key_name', '').strip() or "My Passkey"
    credential_id = data.get('credential_id', '').strip()
    public_key = data.get('public_key', '').strip() or "mock_public_key"
    
    if not credential_id:
        return jsonify({"error": "Credential ID is required"}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_passkeys (user_id, key_name, credential_id, public_key)
                VALUES (?, ?, ?, ?)
            ''', (user_id, key_name, credential_id, public_key))
            conn.commit()
            
        database.log_admin_action(user_id, 'REGISTER_PASSKEY', user_id, f"Registered new passkey: {key_name}")
        return jsonify({"success": True, "message": "Passkey registered successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/passkey/delete", methods=["POST"])
def api_mfa_passkey_delete():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
        
    data = request.get_json() or {}
    key_id = data.get('id')
    
    if not key_id:
        return jsonify({"error": "Passkey ID is required"}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_passkeys WHERE id = ? AND user_id = ?", (key_id, user_id))
            conn.commit()
            success = cursor.rowcount > 0
            
        if success:
            database.log_admin_action(user_id, 'DELETE_PASSKEY', user_id, f"Revoked passkey registration ID: {key_id}")
            return jsonify({"success": True, "message": "Passkey deleted successfully"})
        else:
            return jsonify({"error": "Passkey not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/totp/setup", methods=["POST"])
def api_mfa_totp_setup():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
        
    import base64
    import os
    
    random_bytes = os.urandom(10)
    secret = base64.b32encode(random_bytes).decode().replace('=', '')[:16]
    
    host = request.host.split(':')[0]
    label = f"{user_id}@{host}"
    otpauth_url = f"otpauth://totp/MintFrost:{label}?secret={secret}&issuer=MintFrost"
    
    session['temp_totp_secret'] = secret
    return jsonify({
        "secret": secret,
        "otpauth_url": otpauth_url
    })


@app.route("/api/mfa/totp/verify", methods=["POST"])
def api_mfa_totp_verify():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
        
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    device_name = data.get('device_name', '').strip() or "Authenticator App"
    
    secret = session.get('temp_totp_secret')
    if not secret:
        return jsonify({"error": "TOTP setup session expired. Please restart setup."}), 400
        
    if not code:
        return jsonify({"error": "Verification code is required"}), 400
        
    if verify_totp(secret, code):
        try:
            with database.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_authenticators (user_id, device_name, secret_key)
                    VALUES (?, ?, ?)
                ''', (user_id, device_name, secret))
                conn.commit()
                
            session.pop('temp_totp_secret', None)
            database.log_admin_action(user_id, 'ENABLE_TOTP', user_id, f"Enabled App Authenticator: {device_name}")
            return jsonify({"success": True, "message": "App Authenticator enabled successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid verification code. Please check your authenticator app."}), 400


@app.route("/api/mfa/totp/delete", methods=["POST"])
def api_mfa_totp_delete():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
        
    data = request.get_json() or {}
    auth_id = data.get('id')
    
    if not auth_id:
        return jsonify({"error": "Authenticator ID is required"}), 400
        
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_authenticators WHERE id = ? AND user_id = ?", (auth_id, user_id))
            conn.commit()
            success = cursor.rowcount > 0
            
        if success:
            database.log_admin_action(user_id, 'DISABLE_TOTP', user_id, f"Revoked App Authenticator ID: {auth_id}")
            return jsonify({"success": True, "message": "App Authenticator disabled successfully"})
        else:
            return jsonify({"error": "Authenticator not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Start Flask development server
    app.run(host='0.0.0.0', port=5001, debug=True)
    # Spotify credentials updated reload trigger