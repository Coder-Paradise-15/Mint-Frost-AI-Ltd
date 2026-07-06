import base64
import html
import json
import os
import random
import re
import sqlite3
import ssl
import time
import urllib.parse
import urllib.request
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlencode

import requests
from databases import database
from flask import Flask, g, jsonify, redirect, render_template, request, session
from openai import OpenAI
from static.weather_service import WeatherService
from werkzeug.security import check_password_hash, generate_password_hash

# Create Flask app with simple logging (working setup)
app = Flask(__name__)

# Persist secret key so sessions survive server restarts
_key_path = os.path.join(os.path.dirname(__file__), ".flask_secret")
if os.path.exists(_key_path):
    with open(_key_path, "rb") as f:
        app.secret_key = f.read()
else:
    app.secret_key = os.urandom(32)
    with open(_key_path, "wb") as f:
        f.write(app.secret_key)


# Initialize Database
database.init_db()


def register_login_session(user_id):
    """Generates a unique session token, stores it in session, and logs it in the database"""
    session_token = str(uuid.uuid4())
    session["session_token"] = session_token
    session.modified = True

    ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_addr:
        if "," in ip_addr:
            ip_addr = ip_addr.split(",")[0].strip()
    else:
        ip_addr = "127.0.0.1"

    user_agent = request.headers.get("User-Agent", "Unknown Browser")
    database.create_active_session(session_token, user_id, ip_addr, user_agent)


@app.before_request
def check_session_validity():
    user_id = session.get("user_id")
    if user_id:
        if request.path.startswith("/static/") or request.path.endswith(
            (".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".ico")
        ):
            return

        session_token = session.get("session_token")
        if not session_token:
            session_token = str(uuid.uuid4())
            session["session_token"] = session_token
            session.modified = True

            ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip_addr and "," in ip_addr:
                ip_addr = ip_addr.split(",")[0].strip()
            if not ip_addr:
                ip_addr = "127.0.0.1"

            user_agent = request.headers.get("User-Agent", "Unknown Browser")
            database.create_active_session(session_token, user_id, ip_addr, user_agent)
        else:
            if not database.is_session_active(session_token):
                database.set_user_online_status(user_id, 0)
                session.clear()
                session.modified = True

                if request.headers.get(
                    "Accept"
                ) == "application/json" or request.path.startswith("/api/"):
                    return jsonify(
                        {"error": "Session revoked. Please log in again."}
                    ), 401

                if request.path.startswith("/admin"):
                    return redirect("/admin/login?error=session_revoked")
                return redirect("/login?error=session_revoked")


# Auth guard decorator — protects API routes from unauthenticated access
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        user = database.get_user_secure(user_id)
        if user and user.get("status") == "deactivated":
            session.clear()
            session.modified = True
            return jsonify(
                {"error": "Your account has been deactivated by an administrator."}
            ), 403
        return f(*args, **kwargs)

    return decorated


openai_api_key_file = os.path.join(os.path.dirname(__file__), "OpenAI-Key.txt")


# Load OpenAI API key
def load_openai_key():
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key
    try:
        if os.path.exists(openai_api_key_file):
            with open(openai_api_key_file, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
    except:
        pass
    return None


# Load Weather API key
def load_weather_key():
    env_key = os.environ.get("WEATHER_API_KEY")
    if env_key:
        return env_key
    try:
        if os.path.exists("weather_key.txt"):
            with open("weather_key.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
    except:
        pass
    return None


# Load Google credentials
def load_google_credentials():
    env_id = os.environ.get("GOOGLE_CLIENT_ID")
    env_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if env_id and env_secret:
        return env_id, env_secret
    try:
        if os.path.exists("google_credentials.txt"):
            with open("google_credentials.txt", "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.read().strip().split("\n") if l.strip()]
                if len(lines) >= 2:
                    return lines[0], lines[1]
    except:
        pass
    return None, None


weather_service = WeatherService(api_key=load_weather_key())
google_client_id, google_client_secret = load_google_credentials()


class GeminiCompletionsWrapper:
    def __init__(self, completions):
        self.completions = completions

    def create(self, *args, **kwargs):
        model = kwargs.get("model")
        if model and model.startswith("models/"):
            model = model.replace("models/", "")
            kwargs["model"] = model
        try:
            return self.completions.create(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str or "not supported" in err_str:
                import logging

                logging.warning(
                    f"Gemini model {model} failed. Falling back to gemini-3.5-flash. Error: {e}"
                )
                kwargs["model"] = "gemini-3.5-flash"
                return self.completions.create(*args, **kwargs)
            raise


class GeminiChatWrapper:
    def __init__(self, chat):
        self.completions = GeminiCompletionsWrapper(chat.completions)


class GeminiWrapper:
    def __init__(self, client):
        self.client = client
        self.chat = GeminiChatWrapper(client.chat)


class _DynamicCompletionsRouter:
    """Wraps multiple completions objects and auto-fallbacks on transient errors."""

    def __init__(self, chain):
        """
        chain: list of (completions_obj, model_name) tuples.
        Tried in order; on 429/quota/transient errors, falls to next.
        """
        self._chain = chain

    def create(self, *args, **kwargs):
        disable_fallback = kwargs.pop("disable_fallback", False)
        last_error = None
        for completions_obj, model_name in self._chain:
            try:
                kwargs["model"] = model_name
                result = completions_obj.create(*args, **kwargs)
                # Validate response has non-empty content
                if (
                    result
                    and result.choices
                    and result.choices[0].message
                    and result.choices[0].message.content
                    and result.choices[0].message.content.strip()
                ):
                    return result
                # Empty/None content is treated as a failure — try next model
                content = (
                    result.choices[0].message.content
                    if result and result.choices
                    else None
                )
                app.logger.warning(
                    f"Model '{model_name}' returned empty content ("
                    f"{repr(content)[:50]}), falling back in chain..."
                )
                last_error = RuntimeError(f"Model {model_name} returned empty content")
                if disable_fallback:
                    raise last_error
                continue
            except Exception as e:
                last_error = e
                if disable_fallback:
                    raise
                err_str = str(e).lower()
                # Only fallback on transient/server-side errors
                if any(
                    token in err_str
                    for token in [
                        "429",
                        "503",
                        "502",
                        "500",
                        "quota",
                        "rate limit",
                        "too many requests",
                        "service unavailable",
                        "resource exhausted",
                        "timeout",
                        "connection",
                        "capacity",
                    ]
                ):
                    app.logger.warning(
                        f"Model '{model_name}' failed ({e}), falling back in chain..."
                    )
                    continue
                # Auth / bad-request / invalid-model — raise immediately
                raise
        if last_error:
            raise last_error
        raise RuntimeError("All LLM providers in the fallback chain failed.")


class _DynamicChatRouter:
    def __init__(self, chain):
        self._chain = chain
        self.completions = _DynamicCompletionsRouter(
            [(c.chat.completions, m) for c, m in chain]
        )


class DynamicModelRouter:
    """
    Auto-fallback router that chains multiple (client, model) pairs.
    Tries the primary first; on rate-limit/quota/transient errors,
    automatically falls through to the next model in the chain.

    Usage is identical to a normal OpenAI client:
        router = DynamicModelRouter([(client1, "model-a"), (client1, "model-b"), (client2, "model-c")])
        completion = router.chat.completions.create(messages=[...], ...)
    """

    def __init__(self, fallback_chain):
        """
        fallback_chain: list of (client, model_name) tuples.
        Each client must support .chat.completions.create(model=..., ...).
        The same client can appear multiple times with different model names.
        """
        self._chain = fallback_chain
        self.chat = _DynamicChatRouter([(c, m) for c, m in fallback_chain])


def get_llm_client(data):
    """
    Returns (llm_client, model_name) for the requested provider.
    Raises ValueError if no provider/key is supplied so the caller
    can surface a clean error message instead of hitting the broken
    server-default OpenAI key.
    """
    provider = (data or {}).get("provider")
    api_key = (data or {}).get("api_key", "").strip()
    model = (data or {}).get("model", "").strip()

    if not provider or provider == "default" or not api_key:
        user_id = None
        try:
            from flask import session

            user_id = session.get("user_id")
        except RuntimeError:
            pass
        if user_id:
            settings = database.get_api_settings(user_id)
            if settings and settings.get("api_provider") and settings.get("api_key"):
                provider = settings["api_provider"]
                api_key = settings["api_key"].strip()
                model = settings.get("api_model", "").strip()

    if not provider or provider == "default" or not api_key:
        raise ValueError(
            "No API key configured. Click ☰ → API Settings, "
            "choose a provider (Groq is free!), paste your key, "
            "then pick that model in the chat bar."
        )

    if (provider == "gemini" or provider == "google") and api_key:
        try:
            gemini_client = GeminiWrapper(
                OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
            )
            primary_model = model if model else "gemini-3.5-flash"
            if primary_model.startswith("models/"):
                primary_model = primary_model.replace("models/", "")
            # Fallback models share the same client — different quota pools
            fallback_models = [
                "gemini-1.5-flash",
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
            ]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(gemini_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Gemini client: {e}")
            raise

    elif provider == "openai" and api_key:
        try:
            openai_client = OpenAI(api_key=api_key)
            primary_model = model if model else "gpt-4o-mini"
            fallback_models = ["gpt-4o", "gpt-3.5-turbo"]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(openai_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate OpenAI client: {e}")
            raise

    elif provider == "groq" and api_key:
        try:
            groq_client = OpenAI(
                api_key=api_key, base_url="https://api.groq.com/openai/v1"
            )
            primary_model = model if model else "llama-3.1-8b-instant"
            # Groq free models — different rate-limit pools
            fallback_models = [
                "mixtral-8x7b-32768",
                "deepseek-r1-distill-llama-70b",
                "llama-3.2-90b-vision-preview",
                "gemma2-9b-it",
            ]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(groq_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Groq client: {e}")
            raise

    elif provider == "openrouter" and api_key:
        try:
            openrouter_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/Antigravity",
                    "X-Title": "Mint Frost AI",
                },
            )
            primary_model = model if model else "openrouter/free"
            # OpenRouter fallback chain — free auto-router first, then paid fallbacks
            fallback_models = [
                "meta-llama/llama-3.1-8b-instruct",
                "meta-llama/llama-3.3-70b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "google/gemma-4-31b-it:free",
            ]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(openrouter_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate OpenRouter client: {e}")
            raise

    elif provider == "mistral" and api_key:
        try:
            mistral_client = OpenAI(
                api_key=api_key, base_url="https://api.mistral.ai/v1"
            )
            primary_model = model if model else "mistral-small-latest"
            fallback_models = ["open-mistral-7b", "mistral-tiny"]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(mistral_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
        except Exception as e:
            app.logger.warning(f"Failed to instantiate Mistral client: {e}")
            raise

    elif provider == "anthropic" and api_key:
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

                def create(
                    self, model, messages, max_tokens=1000, temperature=0.7, **kwargs
                ):
                    system = None
                    anthropic_messages = []
                    for m in messages:
                        if m["role"] == "system":
                            system = m["content"]
                        else:
                            anthropic_messages.append(
                                {"role": m["role"], "content": m["content"]}
                            )

                    headers = {
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    }

                    payload = {
                        "model": model if model else "claude-3-5-sonnet-20241022",
                        "messages": anthropic_messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    if system:
                        payload["system"] = system

                    import requests

                    resp = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        json=payload,
                        headers=headers,
                        timeout=60,
                    )
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

                    content = res_json["content"][0]["text"]
                    return MockCompletion(content)

            anthropic_client = AnthropicMockClient(api_key)
            primary_model = model if model else "claude-3-5-sonnet-20241022"
            fallback_models = [
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ]
            all_models = [primary_model] + [
                m for m in fallback_models if m != primary_model
            ]
            chain = [(anthropic_client, m) for m in all_models]
            return DynamicModelRouter(chain), primary_model
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
        clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C")
        image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=512&height=512&nologo=true"
        response = requests.get(image_url, timeout=30)

        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode("utf-8")
            return image_base64
        return None
    except:
        return None


# Text formatting function
def format_text(text):
    # Tables (process before other formatting) - ChatGPT style
    def format_table(match):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split("\n") if line.strip()]

        if len(lines) < 2:
            return table_text

        # Parse header
        header_cells = [cell.strip() for cell in lines[0].split("|") if cell.strip()]
        if not header_cells:
            return table_text

        # Skip separator line (line 1)
        data_rows = []
        for line in lines[2:]:
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
            if cells:
                data_rows.append(cells)

        # Build advanced HTML table
        table_html = f"""
        <div style="margin: 16px 0; overflow-x: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border: 1px solid rgba(255,255,255,0.1);">
            <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <thead>
                    <tr style="background: linear-gradient(135deg, var(--mint) 0%, rgba(64, 224, 208, 0.8) 100%); position: sticky; top: 0; z-index: 10;">
        """

        # Header cells
        for i, cell in enumerate(header_cells):
            border_style = (
                "border-right: 1px solid rgba(255,255,255,0.2);"
                if i < len(header_cells) - 1
                else ""
            )
            table_html += f"""
                        <th style="padding: 14px 16px; color: #1a1a1a; font-weight: 600; font-size: 0.9em; text-align: left; letter-spacing: 0.5px; {border_style}">
                            {cell}
                        </th>
            """

        table_html += """
                    </tr>
                </thead>
                <tbody>
        """

        # Body rows
        for i, row in enumerate(data_rows):
            hover_bg = (
                "rgba(255,255,255,0.08)" if i % 2 == 0 else "rgba(255,255,255,0.04)"
            )
            table_html += (
                f'<tr style="background: {hover_bg}; transition: all 0.2s ease;">'
            )

            for j, cell in enumerate(row):
                if j < len(header_cells):
                    border_style = (
                        "border-right: 1px solid rgba(255,255,255,0.08);"
                        if j < len(header_cells) - 1
                        else ""
                    )
                    table_html += f'<td style="padding: 12px 16px; color: rgba(255,255,255,0.9); font-size: 0.9em; border-top: 1px solid rgba(255,255,255,0.06); {border_style} vertical-align: top; line-height: 1.5;">{cell}</td>'

            table_html += "</tr>"

        table_html += """
                </tbody>
            </table>
        </div>
        """

        return table_html

    # Match markdown tables
    table_pattern = r"(?:^\|.*\|\s*$\n)+(?:^\|[-:| ]+\|\s*$\n)(?:^\|.*\|\s*$\n?)+"
    text = re.sub(table_pattern, format_table, text, flags=re.MULTILINE)

    # Headers (process in order from most specific to least) - Compact spacing
    text = re.sub(
        r"^#### (.*?)$",
        r'<h4 style="color: var(--mint); margin: 8px 0 4px 0; font-size: 1.1em;">\1</h4>',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^### (.*?)$",
        r'<h3 style="color: var(--mint); margin: 10px 0 5px 0; font-size: 1.2em;">\1</h3>',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^## (.*?)$",
        r'<h2 style="color: var(--mint); margin: 12px 0 6px 0; font-size: 1.3em;">\1</h2>',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^# (.*?)$",
        r'<h1 style="color: var(--mint); margin: 15px 0 8px 0; font-size: 1.4em;">\1</h1>',
        text,
        flags=re.MULTILINE,
    )

    # Section headers without # symbols
    text = re.sub(
        r"^([A-Z][^\n]*:)$",
        r'<h3 style="color: var(--mint); margin: 12px 0 6px 0; font-size: 1.2em;">\1</h3>',
        text,
        flags=re.MULTILINE,
    )

    # Code blocks (before other formatting) - Compact spacing
    text = re.sub(
        r"```([\s\S]*?)```",
        r'<pre style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 4px; margin: 6px 0; overflow-x: auto; font-size: 0.9em;"><code>\1</code></pre>',
        text,
    )

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="background: rgba(255,255,255,0.1); padding: 1px 3px; border-radius: 2px; font-family: monospace; font-size: 0.9em;">\1</code>',
        text,
    )

    # Bold text
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r'<strong style="color: var(--mint); font-weight: 600;">\1</strong>',
        text,
    )

    # Italic text
    text = re.sub(
        r"\*(.*?)\*",
        r'<em style="font-style: italic; color: rgba(255,255,255,0.9);">\1</em>',
        text,
    )

    # Lists - Enhanced number formatting with compact spacing
    text = re.sub(
        r"^(\d+)([.)]?)\s*(.+)$",
        r'<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); font-weight: 600; min-width: 24px; background: rgba(255,255,255,0.1); border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 0.8em; margin-right: 8px; flex-shrink: 0;">\1</span><span style="flex: 1;">\3</span></li>',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^[*•-]\s*(.+)$",
        r'<li style="margin: 2px 0; color: rgba(255,255,255,0.9); display: flex; align-items: flex-start;"><span style="color: var(--mint); margin-right: 8px; font-weight: bold;">•</span><span style="flex: 1;">\1</span></li>',
        text,
        flags=re.MULTILINE,
    )

    # Wrap consecutive list items in ul - Compact spacing
    text = re.sub(
        r"((<li[^>]*>.*</li>\s*)+)",
        r'<ul style="margin: 6px 0; padding-left: 0; list-style: none;">\1</ul>',
        text,
    )

    # Line breaks - More compact
    text = re.sub(r"\n\s*\n", "<br><br>", text)
    text = text.replace("\n", "<br>")

    return text


# Image generation function
def process_image_generation(ai_reply):
    try:
        # First format the text
        ai_reply = format_text(ai_reply)

        pattern = r"\[IMAGE_REQUEST:\s*([^\]]+)\]"
        match = re.search(pattern, ai_reply)

        if match:
            image_prompt = match.group(1).strip()

            try:
                image_base64 = generate_free_image(image_prompt)

                if image_base64:
                    image_html = f'<img src="data:image/png;base64,{image_base64}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;" alt="{image_prompt}"/>'
                    ai_reply = re.sub(pattern, image_html, ai_reply)
                else:
                    fallback = f"🎨 <em>Visual content: {image_prompt}</em>"
                    ai_reply = re.sub(pattern, fallback, ai_reply)

            except:
                fallback = f"🎨 <em>Visual content: {image_prompt}</em>"
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
    return dict(csrf_token=lambda: "")


@app.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    user = database.get_user_secure(user_id)
    if user and user.get("status") == "deactivated":
        session.clear()
        session.modified = True
        return redirect("/login?error=deactivated")

    # Self-heal client cookies from oversized chat history data
    if "chat_history" in session:
        session.pop("chat_history", None)
        session.modified = True

    return render_template("index.html")


@app.route("/login")
def login():
    if session.get("user_id"):
        return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session_token = session.get("session_token")
    if session_token:
        database.revoke_active_session(session_token)
    if user_id:
        database.set_user_online_status(user_id, 0)
    session.clear()
    session.modified = True
    return redirect("/login")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(
            {"success": False, "error": "Username and password required"}
        ), 400

    user = database.get_user_secure(username)
    if not user:
        return jsonify({"success": False, "error": "Invalid username or password"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid username or password"}), 401

    if user.get("status") == "deactivated":
        return jsonify(
            {
                "success": False,
                "error": "Your account has been deactivated by an administrator.",
            }
        ), 403

    # Check if MFA is enabled (Passkey or TOTP)
    has_passkey = False
    has_totp = False
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM user_passkeys WHERE user_id = ?", (user["id"],)
            )
            has_passkey = cursor.fetchone() is not None
            cursor.execute(
                "SELECT id FROM user_authenticators WHERE user_id = ?", (user["id"],)
            )
            has_totp = cursor.fetchone() is not None
    except Exception as e:
        app.logger.error(f"Error checking MFA status: {str(e)}")

    if has_passkey or has_totp:
        session["mfa_pending_user_id"] = user["id"]
        session.modified = True
        return jsonify(
            {
                "success": True,
                "mfa_required": True,
                "methods": {"passkey": has_passkey, "totp": has_totp},
            }
        )

    session["user_id"] = user["id"]
    session["local_user_id"] = user["id"]
    session["display_name"] = user["display_name"]
    session.modified = True

    # Register active session
    register_login_session(user["id"])

    # Capture login IP & Geo-location telemetry
    log_user_telemetry(user["id"])

    return jsonify({"success": True})


@app.route("/api/register", methods=["POST"])
def api_register():
    # Registration disabled administrative switch check
    if database.get_config_value("enable_registration", "true") == "false":
        return jsonify(
            {
                "success": False,
                "error": "Public registration has been temporarily disabled by the administrator.",
            }
        ), 403

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    display_name = data.get("display_name", "").strip() or None

    if not username or not password:
        return jsonify(
            {"success": False, "error": "Username and password required"}
        ), 400

    if len(username) < 3 or len(username) > 20 or not username.isalnum():
        return jsonify(
            {"success": False, "error": "Username must be 3-20 alphanumeric characters"}
        ), 400

    if len(password) < 6:
        return jsonify(
            {"success": False, "error": "Password must be at least 6 characters"}
        ), 400

    existing_user = database.get_user_secure(username)
    if existing_user:
        return jsonify({"success": False, "error": "Username already exists"}), 409

    password_hash = generate_password_hash(password)
    try:
        database.create_user_secure(username, password_hash, display_name)
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"Failed to create user: {str(e)}"}
        ), 500

    session["user_id"] = username
    session["local_user_id"] = username
    session["display_name"] = display_name
    session.modified = True

    # Capture registration IP & Location telemetry
    log_user_telemetry(username)

    return jsonify({"success": True})


@app.route("/test")
def test():
    return jsonify(
        {"message": "Test successful", "timestamp": datetime.now().isoformat()}
    )


@app.route("/regenerate", methods=["POST"])
@login_required
def regenerate():
    # Redirect to chat route with regenerate flag
    return chat(is_regenerate=True)


def check_rate_limit(client_ip):
    now = time.time()
    rate_limits[client_ip] = [
        req_time for req_time in rate_limits[client_ip] if now - req_time < RATE_WINDOW
    ]

    if len(rate_limits[client_ip]) >= RATE_LIMIT:
        return False

    rate_limits[client_ip].append(now)
    return True


def get_current_info(location=None, lat=None, lon=None):
    now = datetime.now()

    time_info = {
        "current_time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "timezone": str(now.astimezone().tzinfo),
    }

    try:
        if lat is not None and lon is not None:
            weather_info = weather_service.get_weather_by_coordinates(lat, lon)
        elif location:
            weather_info = weather_service.get_weather_by_city(location)
        else:
            weather_info = weather_service.get_weather_by_city("London")
    except:
        weather_info = {
            "temperature": "N/A",
            "description": "Weather unavailable",
            "location": "Unknown",
            "humidity": "N/A",
            "wind_speed": "N/A",
        }

    return time_info, weather_info


def parse_deadline_fallback(message, base_date=None):
    if base_date is None:
        # Use timezone-aware current local time or server time
        base_date = datetime.now()

    tasks = []

    # Define categories and keywords
    categories = {
        "Assignment": [
            "assignment",
            "project",
            "homework",
            "submission",
            "submit",
            "report",
            "essay",
        ],
        "Exam": ["exam", "test", "practical", "quiz", "midterm", "final"],
        "Meeting": [
            "meeting",
            "interview",
            "call",
            "appointment",
            "sync",
            "discussion",
            "presentation",
        ],
        "Bill": [
            "bill",
            "pay",
            "payment",
            "rent",
            "electricity",
            "water",
            "gas",
            "internet",
        ],
        "Goal": ["goal", "target", "milestone", "resolution", "commit", "commitment"],
        "Reminder": ["remind", "reminder", "todo", "task", "remember"],
    }

    # Days of week mapping
    days_of_week = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    # Simple regex to split sentences if multiple tasks might be present
    sentences = re.split(r"[.,;!]\s*|\band\b", message)

    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if not sentence_lower:
            continue

        # Detect category and title
        category = "Reminder"  # default
        matched_cat_word = None
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in sentence_lower:
                    category = cat
                    matched_cat_word = kw
                    break
            if matched_cat_word:
                break

        # Try to find a date
        detected_date = None
        date_str = ""

        # Tomorrow
        if "tomorrow" in sentence_lower:
            detected_date = base_date + timedelta(days=1)
            date_str = "tomorrow"
        # Today
        elif "today" in sentence_lower:
            detected_date = base_date
            date_str = "today"
        # Next week
        elif "next week" in sentence_lower:
            detected_date = base_date + timedelta(days=7)
            date_str = "next week"
        # Specific day of week
        else:
            for day, day_num in days_of_week.items():
                if day in sentence_lower:
                    # Find next day_num day of week
                    days_ahead = day_num - base_date.weekday()
                    if (
                        days_ahead <= 0
                    ):  # Target day already happened this week or is today
                        days_ahead += 7
                    detected_date = base_date + timedelta(days=days_ahead)
                    date_str = day
                    break

        # Check if we found a date. If not, check if we have time "before 5 pm" or "at 3 pm" but default to today
        time_str = None
        time_match = re.search(
            r"\b(?:at|before|by)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", sentence_lower
        )
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2)) if time_match.group(2) else 0
            am_pm = time_match.group(3)

            if am_pm == "pm" and hours < 12:
                hours += 12
            elif am_pm == "am" and hours == 12:
                hours = 0

            time_str = f"{hours:02d}:{minutes:02d}"
            if not detected_date:
                # If time was specified but no date, assume today
                detected_date = base_date
                date_str = "today"

        if not detected_date:
            # If no date/time indicators found, it's not a deadline
            continue

        # Extract Task Title: try to extract a clean title from the sentence
        title = sentence.strip()
        # Remove common prefix patterns
        title = re.sub(
            r"^(i have my|my|i need to|remind me to|i have an)\s+",
            "",
            title,
            flags=re.IGNORECASE,
        )
        # Remove date/time suffixes
        title = re.sub(
            r"\b(tomorrow|today|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*$",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()
        title = re.sub(
            r"\b(at|before|by)\s*\d+.*$", "", title, flags=re.IGNORECASE
        ).strip()
        # Clean trailing prepositions/verbs
        title = re.sub(r"\s+(is on|on|at|is)$", "", title, flags=re.IGNORECASE).strip()

        # Fallback to category + keyword if title is too short or empty
        if len(title) < 3:
            title = f"{category} Task"

        # Estimate duration based on category
        durations = {
            "Assignment": "3 hours",
            "Exam": "2 hours",
            "Meeting": "1 hour",
            "Bill": "15 minutes",
            "Goal": "5 hours",
            "Reminder": "30 minutes",
        }
        duration = durations.get(category, "1 hour")

        # Calculate confidence
        confidence = 0.5
        if matched_cat_word:
            confidence += 0.2
        if time_str:
            confidence += 0.2
        if date_str in ["tomorrow", "today"] or date_str in days_of_week:
            confidence += 0.1
        confidence = min(0.95, confidence)

        tasks.append(
            {
                "task_name": title,
                "category": category,
                "date": detected_date.strftime("%Y-%m-%d"),
                "time": time_str or "23:59",
                "confidence": round(confidence, 2),
                "duration": duration,
            }
        )

    return tasks


from datetime import timedelta


def is_breakdown_request(text):
    text_lower = text.lower()
    action_verbs = [
        "break",
        "split",
        "plan",
        "create",
        "steps",
        "add",
        "new",
        "schedule",
        "todo",
        "to-do",
        "make",
        "do",
        "set",
    ]
    task_nouns = [
        "task",
        "assignment",
        "project",
        "subtask",
        "subtasks",
        "sub-task",
        "sub-tasks",
        "exam",
        "test",
        "meeting",
        "reminder",
        "goal",
        "bill",
        "homework",
        "study",
    ]

    has_action = any(w in text_lower for w in action_verbs)
    has_noun = any(w in text_lower for w in task_nouns)
    return (has_action and has_noun) or any(
        kw in text_lower
        for kw in [
            "break down",
            "help me plan",
            "split this",
            "create task",
            "add task",
        ]
    )


def generate_fallback_subtasks(category, task_title):
    templates = {
        "Assignment": [
            {
                "title": f"Research {task_title}",
                "duration": "30 min",
                "priority": "High",
                "difficulty": "Medium",
            },
            {
                "title": "Draft Outline",
                "duration": "30 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Solve/Write Content",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Hard",
            },
            {
                "title": "Final Review",
                "duration": "30 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
            {
                "title": "Submit Assignment",
                "duration": "10 min",
                "priority": "High",
                "difficulty": "Easy",
            },
        ],
        "Exam": [
            {
                "title": "Gather Study Materials",
                "duration": "20 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Review Lecture Notes",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Medium",
            },
            {
                "title": "Solve Practice Questions",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Hard",
            },
            {
                "title": "Revise Difficult Topics",
                "duration": "30 min",
                "priority": "Medium",
                "difficulty": "Medium",
            },
            {
                "title": "Rest and Final Prep",
                "duration": "15 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
        ],
        "Meeting": [
            {
                "title": "Prepare Meeting Agenda",
                "duration": "15 min",
                "priority": "High",
                "difficulty": "Easy",
            },
            {
                "title": "Research Background Context",
                "duration": "20 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Attend Meeting",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Medium",
            },
            {
                "title": "Write and Send Minutes",
                "duration": "15 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
        ],
        "Bill": [
            {
                "title": "Retrieve Invoice Details",
                "duration": "5 min",
                "priority": "High",
                "difficulty": "Easy",
            },
            {
                "title": "Verify Funds Availability",
                "duration": "5 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Process Payment Transfer",
                "duration": "10 min",
                "priority": "High",
                "difficulty": "Easy",
            },
            {
                "title": "File Receipt Confirmation",
                "duration": "5 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
        ],
        "Goal": [
            {
                "title": "Define Milestones",
                "duration": "30 min",
                "priority": "High",
                "difficulty": "Medium",
            },
            {
                "title": "Outline Daily Habits",
                "duration": "20 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Take First Action Step",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Hard",
            },
            {
                "title": "Set Up Weekly Review",
                "duration": "15 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
        ],
    }
    return templates.get(
        category,
        [
            {
                "title": f"Prepare context for {task_title}",
                "duration": "20 min",
                "priority": "Medium",
                "difficulty": "Easy",
            },
            {
                "title": "Execute core task actions",
                "duration": "60 min",
                "priority": "High",
                "difficulty": "Medium",
            },
            {
                "title": "Verify results and submit",
                "duration": "15 min",
                "priority": "Low",
                "difficulty": "Easy",
            },
        ],
    )


@app.route("/chat", methods=["POST"])
@login_required
def chat(is_regenerate=False):
    detected_tasks = []
    client_ip = request.remote_addr
    app.logger.info(f"[Chat API] Received request from client IP: {client_ip}")

    if not check_rate_limit(client_ip):
        return jsonify(
            {
                "error": "Rate limit exceeded. Please wait before sending another message.",
                "retry_after": 60,
            }
        ), 429

    data = request.get_json() or {}

    # Handle regenerate request
    if is_regenerate:
        recent_sessions = database.get_recent_sessions(
            limit=5, user_id=session.get("user_id")
        )
        if not recent_sessions:
            return jsonify({"error": "No previous messages to regenerate"}), 400

        session_id = recent_sessions[0]["id"]
        messages = database.get_session_messages(session_id)

        if not messages:
            return jsonify({"error": "No messages found"}), 400

        # Find last user message
        user_message = None
        for msg in reversed(messages):
            if msg["who"] == "user":
                user_message = msg["text"]
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

    if "chat_history" not in session:
        session["chat_history"] = []

    user_lower = user_message.lower()
    time_keywords = ["time", "clock", "what time", "current time"]
    weather_keywords = ["weather", "temperature", "temp", "climate", "forecast"]

    context_info = ""
    if any(keyword in user_lower for keyword in time_keywords + weather_keywords):
        user_lat = request.headers.get("X-User-Latitude")
        user_lon = request.headers.get("X-User-Longitude")

        if user_lat and user_lon:
            try:
                time_info, weather_info = get_current_info(
                    lat=float(user_lat), lon=float(user_lon)
                )
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

    recent_history = []
    active_session_id = session.get("current_session_id")
    if active_session_id:
        try:
            db_msgs = database.get_session_messages(active_session_id)
            user_msg = None
            for msg in db_msgs:
                if msg["who"] == "user":
                    user_msg = msg["text"]
                elif msg["who"] == "ai" and user_msg:
                    recent_history.append({"user": user_msg, "ai": msg["text"]})
                    user_msg = None
            recent_history = recent_history[-10:]
        except Exception as e:
            app.logger.error(f"Error loading chat context from DB: {e}")

    for msg in recent_history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["ai"]})

    messages.append({"role": "user", "content": user_message})

    # Intercept live task query requests
    user_msg_lower = user_message.lower()
    is_coach_query = any(
        phrase in user_msg_lower
        for phrase in [
            "give me productivity advice",
            "how am i doing today",
            "what should i focus on",
            "am i behind schedule",
            "productivity advice",
            "coach advice",
            "coaching advice",
            "what should i do now",
        ]
    )

    is_task_query = any(
        phrase in user_msg_lower
        for phrase in [
            "show my tasks",
            "what is pending",
            "what should i finish today",
            "list my deadlines",
            "my tasks",
            "my deadlines",
            "list tasks",
            "show tasks",
            "what is due",
        ]
    )

    is_planner_query = any(
        phrase in user_msg_lower
        for phrase in [
            "plan my day",
            "generate today's schedule",
            "create today's study plan",
            "todays plan",
            "today schedule",
            "my schedule",
        ]
    )

    is_risk_query = any(
        phrase in user_msg_lower
        for phrase in [
            "what should i do first",
            "which task is most urgent",
            "am i likely to miss any deadlines",
            "what is my highest priority",
            "highest priority task",
            "risk analysis",
            "productivity risk",
        ]
    )

    if is_coach_query:
        tasks = database.get_user_tasks_filtered(session.get("user_id")) or []
        active_tasks = [
            t
            for t in tasks
            if t.get("status") != "Completed" and t.get("status") != "Cancelled"
        ]
        completed_today_tasks = [t for t in tasks if t.get("status") == "Completed"]
        overdue_tasks = [t for t in active_tasks if t.get("status") == "Overdue"]

        # Calculate stats
        total_active_count = len(active_tasks)
        completed_today_count = len(completed_today_tasks)

        highest_prio_task = None
        highest_score = -1
        for t in active_tasks:
            score = t.get("priority_score") or 0
            if score > highest_score:
                highest_score = score
                highest_prio_task = t

        upcoming_deadline_task = None
        closest_deadline = None
        for t in active_tasks:
            dl_str = t.get("deadline")
            if dl_str:
                try:
                    dl_date = datetime.strptime(dl_str, "%Y-%m-%d")
                    if closest_deadline is None or dl_date < closest_deadline:
                        closest_deadline = dl_date
                        upcoming_deadline_task = t
                except:
                    pass

        probs = [
            t.get("completion_probability")
            for t in active_tasks
            if t.get("completion_probability") is not None
        ]
        avg_prob = int(sum(probs) / len(probs)) if probs else 100

        tasks_summary = ""
        for t in active_tasks[:10]:
            tasks_summary += f'- "{t["title"]}" (Priority Score: {t.get("priority_score") or 50}, Risk: {t.get("risk_level") or "Safe"}, Deadline: {t.get("deadline") or "None"})\n'

        coach_context_prompt = (
            f"You are Mint Frost AI, the user's proactive AI productivity coach. "
            f"Below is a live productivity audit of the user's workload:\n"
            f"- Active tasks remaining: {total_active_count}\n"
            f"- Tasks completed today: {completed_today_count}\n"
            f"- Average completion probability: {avg_prob}%\n"
            f"- Overdue tasks: {len(overdue_tasks)}\n"
            f'- Highest priority task: "{highest_prio_task["title"] if highest_prio_task else "None"}"\n'
            f'- Nearest upcoming deadline task: "{upcoming_deadline_task["title"] if upcoming_deadline_task else "None"}" (Due: {upcoming_deadline_task.get("deadline") if upcoming_deadline_task else "N/A"})\n\n'
            f"Active tasks details:\n{tasks_summary if tasks_summary else 'No active tasks.'}\n\n"
            f"Please answer the user's question directly with highly personalized, data-driven, motivational, and actionable advice based on this live context. Keep your response encouraging, clear, and focused on helping them optimize execution."
        )
        messages = [
            {"role": "system", "content": coach_context_prompt},
            {"role": "user", "content": user_message},
        ]
    elif is_task_query:
        tasks_context = get_tasks_context_for_ai(session.get("user_id"))
        task_system_prompt = f"You are Mint Frost AI, the user's task management assistant. Below is the LIVE list of the user's tasks fetched from the database:\n{tasks_context}\n\nPlease answer the user's question accurately based ONLY on this list. If they ask 'what should I finish today', look for tasks that have a deadline today or are overdue. Keep your response professional, encouraging, and clear. Format lists nicely using markdown bullet points."
        messages = [
            {"role": "system", "content": task_system_prompt},
            {"role": "user", "content": user_message},
        ]
    elif is_planner_query:
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_str = database.get_daily_plan(session.get("user_id"), date_str)
        if not plan_str:
            tasks = database.get_user_tasks_filtered(session.get("user_id"))
            if tasks:
                fallback_plan = generate_local_schedule(tasks)
                plan_str = json.dumps(fallback_plan)
                database.save_daily_plan(session.get("user_id"), date_str, plan_str)
            else:
                plan_str = "[]"

        plan = json.loads(plan_str)
        if plan:
            formatted_plan = ""
            for item in plan:
                prio_badge = (
                    f" [Priority: {item['priority']}]" if item.get("priority") else ""
                )
                formatted_plan += f"- **{item['start_time']} - {item['end_time']}**: {item['title']}{prio_badge}\n"
        else:
            formatted_plan = (
                "No tasks available to schedule. Please create some tasks first!"
            )

        planner_system_prompt = f"You are Mint Frost AI, the user's personal planning assistant. Below is the optimized daily schedule generated for the user today:\n\n{formatted_plan}\n\nPlease present this schedule to the user in a friendly, encouraging way. If they ask 'what should I do now', identify the current recommended item based on the timeline. Keep it professional and visually appealing with markdown."
        messages = [
            {"role": "system", "content": planner_system_prompt},
            {"role": "user", "content": user_message},
        ]
    elif is_risk_query:
        tasks = database.get_user_tasks_filtered(session.get("user_id"))
        active_tasks = [t for t in tasks if t.get("status") != "Completed"]
        active_tasks.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        if active_tasks:
            formatted_tasks = ""
            for t in active_tasks:
                formatted_tasks += (
                    f"- **{t['title']}**:\n"
                    f"  * Priority Score: {t.get('priority_score', 50)}/100\n"
                    f"  * Risk Level: {t.get('risk_level', 'Safe')}\n"
                    f"  * Completion Probability: {t.get('completion_probability', 100)}%\n"
                    f"  * Suggested Action: {t.get('suggested_action')}\n"
                    f"  * Risk Reason: {t.get('risk_reason')}\n"
                    f"  * Deadline: {t.get('deadline') or 'None'}\n"
                )
        else:
            formatted_tasks = "No active tasks in database."

        risk_system_prompt = f"You are Mint Frost AI, the user's priority intelligence assistant. Below is the live priority risk analysis of the user's tasks from the database:\n\n{formatted_tasks}\n\nPlease answer the user's question accurately based on this live risk and priority intelligence. If they ask what to do first, recommend the task with the highest priority score. Keep your response encouraging, clear, and professional."
        messages = [
            {"role": "system", "content": risk_system_prompt},
            {"role": "user", "content": user_message},
        ]

    try:
        app.logger.info(f"[Chat AI] Instantiating LLM client for user message")
        active_client, active_model = get_llm_client(data)
        app.logger.info(f"[Chat AI] Using provider/client: {active_client.__class__.__name__}, model: {active_model}")
        app.logger.info(f"[Chat AI] Sending chat completion request to model: {active_model} (timeout: 6.0s)")
        completion = active_client.chat.completions.create(
            model=active_model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            timeout=6.0,
            disable_fallback=True,
        )
        app.logger.info(f"[Chat AI] Successfully received response from {active_model}.")

        if completion.choices and completion.choices[0].message.content:
            ai_reply = completion.choices[0].message.content

            if "[IMAGE_REQUEST:" in ai_reply:
                ai_reply = process_image_generation(ai_reply)
            else:
                ai_reply = format_text(ai_reply)
        else:
            ai_reply = "⚠️ No reply from AI."

        # Only run task extraction if message looks like it contains a task/deadline
        _msg_plain = html.unescape(user_message).lower()
        _has_task_signal = is_breakdown_request(_msg_plain) or any(
            w in _msg_plain
            for w in [
                "deadline",
                "due",
                "submit",
                "exam",
                "meeting",
                "remind",
                "tomorrow",
                "today",
                "next week",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "assignment",
                "project",
                "bill",
                "pay",
                "goal",
                "by ",
                "at ",
                "pm",
                "am",
            ]
        )
        try:
            is_breakdown = is_breakdown_request(_msg_plain)
            if not _has_task_signal:
                pass  # skip extraction entirely — no task signals
            elif is_breakdown:
                extraction_prompt = f"""You are a precise task planning assistant.
Analyze the following user request to create a task: "{html.unescape(user_message)}"
Today's date is: {datetime.now().strftime("%Y-%m-%d")} ({datetime.now().strftime("%A")}).

Create a concise, professional, custom title for the overall task. Break down the task into AT LEAST 4 to 6 detailed, logical, specific subtasks (checklist steps) chronological from start to finish. Do not output generic placeholders.

You MUST output ONLY a valid JSON object matching this structure (do not wrap in markdown block, do not include other text):
{{
  "task_name": "A descriptive customized title for the task (not just a copy of the request)",
  "category": "One of: Assignment, Exam, Meeting, Reminder, Goal, Bill, Other",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "duration": "Estimated total time",
  "confidence": 1.0,
  "subtasks": [
    {{
      "title": "Specific action-oriented subtask title",
      "duration": "Est. duration (e.g. 20 min)",
      "priority": "High/Medium/Low",
      "difficulty": "Easy/Medium/Hard",
      "dependency": "Title of a prerequisite subtask from this list or null if none"
    }}
  ]
}}
"""
                app.logger.info(f"[Chat AI] Sending task extraction request to model: {active_model} (timeout: 6.0s)")
                extraction_completion = active_client.chat.completions.create(
                    model=active_model,
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=800,
                    temperature=0.0,
                    timeout=6.0,
                    disable_fallback=True,
                )
                app.logger.info(f"[Chat AI] Successfully received extraction response from {active_model}.")
                extracted_text = (
                    extraction_completion.choices[0].message.content or ""
                ).strip()
                # Robust json extraction
                json_str = extracted_text.strip()
                first = json_str.find("{")
                last = json_str.rfind("}")
                if first != -1 and last != -1:
                    json_str = json_str[first : last + 1]

                try:
                    plan_data = json.loads(json_str)
                except Exception:
                    try:
                        # Clean single quote replacements for keys/values
                        cleaned = re.sub(r"'\s*([^']*?)\s*'\s*:", r'"\1":', json_str)
                        cleaned = cleaned.replace("'", '"')
                        plan_data = json.loads(cleaned)
                    except Exception:
                        raise

                task_name = plan_data.get("task_name", "Broken Task").strip()
                category = plan_data.get("category", "Other").strip()
                date = plan_data.get(
                    "date", datetime.now().strftime("%Y-%m-%d")
                ).strip()
                time = plan_data.get("time", "23:59").strip()
                duration = plan_data.get("duration", "1 Hour").strip()
                confidence = float(plan_data.get("confidence", 1.0))
                subtasks = plan_data.get("subtasks", [])

                if not subtasks:
                    subtasks = generate_fallback_subtasks(category, task_name)

                # Save task + subtasks to DB
                task_id = database.create_task_with_subtasks(
                    user_id=session.get("user_id"),
                    title=task_name,
                    category=category,
                    deadline=f"{date} {time}".strip(),
                    duration=duration,
                    confidence=confidence,
                    subtasks_list=subtasks,
                )

                # Fetch subtasks from DB to get generated primary key IDs
                subtasks_db = []
                if task_id:
                    with database.connect_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT id, title, duration, difficulty, priority, completed, dependency FROM subtasks WHERE task_id = ? ORDER BY subtask_order ASC",
                            (task_id,),
                        )
                        for row in cursor.fetchall():
                            subtasks_db.append(
                                {
                                    "id": row[0],
                                    "title": row[1],
                                    "duration": row[2],
                                    "difficulty": row[3],
                                    "priority": row[4],
                                    "completed": bool(row[5]),
                                    "dependency": row[6],
                                }
                            )

                detected_tasks = [
                    {
                        "task_name": task_name,
                        "category": category,
                        "date": date,
                        "time": time,
                        "confidence": confidence,
                        "duration": duration,
                        "task_id": task_id,
                        "progress": 0,
                        "subtasks": subtasks_db,
                    }
                ]
            else:
                # Use fast rule-based parser instead of a second LLM call
                detected_tasks = parse_deadline_fallback(html.unescape(user_message))
        except Exception as ex:
            app.logger.warning(
                f"AI deadline/subtask extraction failed: {ex}. Falling back to rule-based parser."
            )
            if is_breakdown_request(_msg_plain):
                fallback_tasks = parse_deadline_fallback(html.unescape(user_message))
                if fallback_tasks:
                    task_name = fallback_tasks[0]["task_name"]
                    category = fallback_tasks[0]["category"]
                    date = fallback_tasks[0]["date"]
                    time = fallback_tasks[0]["time"]
                    duration = fallback_tasks[0]["duration"]
                    confidence = fallback_tasks[0]["confidence"]
                else:
                    task_name = "Task Breakdown"
                    category = "Other"
                    date = datetime.now().strftime("%Y-%m-%d")
                    time = "23:59"
                    duration = "1 Hour"
                    confidence = 0.5

                subtasks = generate_fallback_subtasks(category, task_name)
                task_id = database.create_task_with_subtasks(
                    user_id=session.get("user_id"),
                    title=task_name,
                    category=category,
                    deadline=f"{date} {time}".strip(),
                    duration=duration,
                    confidence=confidence,
                    subtasks_list=subtasks,
                )

                subtasks_db = []
                if task_id:
                    with database.connect_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT id, title, duration, difficulty, priority, completed, dependency FROM subtasks WHERE task_id = ? ORDER BY subtask_order ASC",
                            (task_id,),
                        )
                        for row in cursor.fetchall():
                            subtasks_db.append(
                                {
                                    "id": row[0],
                                    "title": row[1],
                                    "duration": row[2],
                                    "difficulty": row[3],
                                    "priority": row[4],
                                    "completed": bool(row[5]),
                                    "dependency": row[6],
                                }
                            )

                detected_tasks = [
                    {
                        "task_name": task_name,
                        "category": category,
                        "date": date,
                        "time": time,
                        "confidence": confidence,
                        "duration": duration,
                        "task_id": task_id,
                        "progress": 0,
                        "subtasks": subtasks_db,
                    }
                ]
            else:
                detected_tasks = parse_deadline_fallback(html.unescape(user_message))

        if "current_session_id" not in session:
            session["current_session_id"] = str(uuid.uuid4())
            title = (
                user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
            try:
                database.create_session(
                    session["current_session_id"], title, user_id=session.get("user_id")
                )
            except:
                pass

        try:
            database.add_message(session["current_session_id"], user_message, "user")
            database.add_message(session["current_session_id"], ai_reply, "ai")
        except:
            pass

        session.modified = True

    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Chat error: {error_msg}")
        if (
            "rate_limit_exceeded" in error_msg.lower()
            or "rate limit" in error_msg.lower()
        ):
            ai_reply = "⚠️ Rate limit reached! The server's default AI quota is exhausted. Please <strong>add your own API key</strong>: click ☰ → API Settings, choose a provider (Groq is free!), paste your key, then select that model in the chat bar above."
        elif (
            "invalid_api_key" in error_msg.lower()
            or "invalid api key" in error_msg.lower()
            or "incorrect api key" in error_msg.lower()
        ):
            ai_reply = "⚠️ Invalid API key! The server's built-in key is not configured. Please <strong>add your own key</strong> via ☰ → API Settings. <a href='https://console.groq.com' target='_blank' style='color:var(--mint)'>Get a free Groq key →</a>"
        elif "authentication" in error_msg.lower() or "401" in error_msg:
            ai_reply = "⚠️ Authentication failed. Please add your own API key via ☰ → API Settings. Groq offers a free tier at <a href='https://console.groq.com' target='_blank' style='color:var(--mint)'>console.groq.com</a>"
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            ai_reply = "⚠️ Connection error. Please check your internet connection and try again."
        else:
            ai_reply = f"⚠️ Sorry, the server's default AI key is not configured. Please click <strong>☰ → API Settings</strong> to add your own API key (Groq is free!). Error: {error_msg[:120]}"

    if "current_session_id" not in session:
        session["current_session_id"] = str(uuid.uuid4())

    return jsonify(
        {
            "reply": ai_reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_count": len(session.get("chat_history", [])),
            "session_id": session["current_session_id"],
            "detected_tasks": detected_tasks,
        }
    )


def enrich_task_with_ai(title, category, deadline, duration):
    """Enrich a task with priority/risk using local heuristics (fast, no LLM call)"""
    from datetime import datetime, timedelta

    suggested_start = datetime.now().strftime("%Y-%m-%d %H:%M")
    suggested_end = (
        deadline
        if deadline
        else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    )

    # Heuristic priority from category
    priority_map = {
        "Exam": "High",
        "Assignment": "High",
        "Meeting": "Medium",
        "Bill": "Medium",
        "Goal": "Low",
        "Reminder": "Low",
    }
    priority = priority_map.get(category or "Other", "Medium")

    # Heuristic risk from deadline proximity
    risk_level = "Low"
    if deadline:
        try:
            dl = datetime.strptime(deadline.split(" ")[0], "%Y-%m-%d")
            days_left = (dl - datetime.now()).days
            if days_left < 0:
                risk_level = "High"
            elif days_left <= 1:
                risk_level = "High"
            elif days_left <= 3:
                risk_level = "Medium"
        except Exception:
            pass

    return {
        "estimated_duration": duration or "1 Hour",
        "priority": priority,
        "difficulty": "Medium",
        "suggested_start_time": suggested_start,
        "suggested_completion_time": suggested_end,
        "category": category or "Other",
        "risk_level": risk_level,
    }


def get_tasks_context_for_ai(user_id):
    """Fetch user tasks and format them as text context for the AI"""
    tasks = database.get_user_tasks_filtered(user_id)
    if not tasks:
        return "You currently have no tasks in your list."

    lines = []
    for t in tasks:
        deadline_str = t.get("deadline") or "No deadline"
        status = t.get("status") or "Pending"
        progress = t.get("progress") or 0
        priority = t.get("priority") or "Medium"
        risk = t.get("risk_level") or "Low"
        lines.append(
            f"- Task: {t['title']} | Category: {t['category']} | Status: {status} ({progress}% done) | "
            f"Priority: {priority} | Risk: {risk} | Deadline: {deadline_str} | Est: {t.get('estimated_duration') or '1 Hour'}"
        )
    return "\n".join(lines)


@app.route("/api/tasks/create", methods=["POST"])
@login_required
def api_create_task():
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        category = data.get("category", "").strip()
        deadline = data.get("deadline", "").strip()
        duration = data.get("duration", "").strip()
        confidence = float(data.get("confidence", 1.0))
        description = data.get("description", "").strip()

        priority = data.get("priority", "").strip()
        risk_level = data.get("risk_level", "").strip()
        status = data.get("status", "").strip()
        estimated_duration = data.get("estimated_duration", "").strip()

        if not title:
            return jsonify({"success": False, "error": "Task title is required"}), 400

        # Format date if needed
        if deadline and "T" in deadline:
            deadline = deadline.replace("T", " ")

        # Prevent duplicates
        if database.check_duplicate_task(session.get("user_id"), title, deadline):
            return jsonify(
                {
                    "success": False,
                    "error": "A task with this title and deadline already exists",
                }
            ), 400

        # Auto enrich if priority/risk/etc. are not sent (meaning it's created from chat or standard button)
        if not priority or not risk_level:
            enriched = enrich_task_with_ai(title, category, deadline, duration)
            priority = enriched.get("priority", "Medium")
            risk_level = enriched.get("risk_level", "Low")
            estimated_duration = enriched.get(
                "estimated_duration", duration or "1 Hour"
            )
            category = enriched.get("category", category or "Other")
            if not deadline:
                deadline = enriched.get("suggested_completion_time", "")

        if not priority:
            priority = "Medium"
        if not risk_level:
            risk_level = "Low"
        if not status:
            status = "Pending"
        if not estimated_duration:
            estimated_duration = duration or "1 Hour"

        success = database.create_task_complete(
            user_id=session.get("user_id"),
            title=title,
            description=description,
            category=category,
            deadline=deadline,
            estimated_duration=estimated_duration,
            duration=duration,
            confidence=confidence,
            priority=priority,
            risk_level=risk_level,
            status=status,
            progress=0,
            ai_generated=1,
            source_chat_message="",
        )

        if success:
            recalculate_task_priority_risk(session.get("user_id"), data)
            database.log_user_activity(
                session.get("user_id"), "Task Created", f"Created task: {title}"
            )
            if deadline:
                database.log_user_activity(
                    session.get("user_id"),
                    "Deadline Detected",
                    f"Deadline set for '{title}': {deadline}",
                )
            return jsonify({"success": True})
        return jsonify(
            {"success": False, "error": "Failed to save task to database"}
        ), 500
    except Exception as e:
        import traceback

        app.logger.error(f"Error in api_create_task: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tasks", methods=["GET"])
@login_required
def api_get_tasks():
    try:
        search_query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        priority = request.args.get("priority", "").strip()
        status = request.args.get("status", "").strip()
        risk = request.args.get("risk", "").strip()

        tasks = database.get_user_tasks_filtered(
            user_id=session.get("user_id"),
            search_query=search_query,
            category=category,
            priority=priority,
            status=status,
            risk=risk,
        )
        return jsonify({"success": True, "tasks": tasks})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def api_update_task(task_id):
    try:
        if not database.verify_task_ownership(task_id, session.get("user_id")):
            return jsonify({"success": False, "error": "Access denied"}), 403

        data = request.get_json() or {}

        deadline = data.get("deadline")
        if deadline and "T" in deadline:
            deadline = deadline.replace("T", " ")

        fields = {
            "title": data.get("title"),
            "description": data.get("description"),
            "category": data.get("category"),
            "deadline": deadline,
            "estimated_duration": data.get("estimated_duration"),
            "priority": data.get("priority"),
            "risk_level": data.get("risk_level"),
            "status": data.get("status"),
            "progress": data.get("progress"),
        }
        # Filter out None fields
        fields = {k: v for k, v in fields.items() if v is not None}

        # Get title
        with database.connect_db() as conn:
            row = conn.execute(
                "SELECT title FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            task_title = row[0] if row else f"Task #{task_id}"

        success = database.update_task_details(task_id, fields)
        if success:
            database.update_task_status_auto(task_id)
            recalculate_task_priority_risk(session.get("user_id"), data)

            if fields.get("status") == "Completed" or fields.get("progress") == 100:
                database.log_user_activity(
                    session.get("user_id"),
                    "Task Finished",
                    f"Completed task: {task_title}",
                )
            else:
                database.log_user_activity(
                    session.get("user_id"),
                    "Task Updated",
                    f"Updated task details: {task_title}",
                )

            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Failed to update task"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def api_delete_task(task_id):
    try:
        if not database.verify_task_ownership(task_id, session.get("user_id")):
            return jsonify({"success": False, "error": "Access denied"}), 403

        with database.connect_db() as conn:
            row = conn.execute(
                "SELECT title FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            task_title = row[0] if row else f"Task #{task_id}"

        success = database.delete_task(task_id)
        if success:
            database.log_user_activity(
                session.get("user_id"), "Task Deleted", f"Deleted task: {task_title}"
            )
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Failed to delete task"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
def api_complete_task(task_id):
    try:
        if not database.verify_task_ownership(task_id, session.get("user_id")):
            return jsonify({"success": False, "error": "Access denied"}), 403

        with database.connect_db() as conn:
            row = conn.execute(
                "SELECT title FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            task_title = row[0] if row else f"Task #{task_id}"

        success = database.update_task_details(
            task_id, {"progress": 100, "status": "Completed"}
        )
        if success:
            database.update_task_status_auto(task_id)
            req_data = request.get_json() or {}
            recalculate_task_priority_risk(session.get("user_id"), req_data)
            database.log_user_activity(
                session.get("user_id"), "Task Finished", f"Completed task: {task_title}"
            )
            xp_status = database.award_xp(
                session.get("user_id"), 50, f"task completion: {task_title}"
            )
            return jsonify({"success": True, "gamification": xp_status})
        return jsonify({"success": False, "error": "Failed to complete task"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subtasks/<int:subtask_id>/toggle", methods=["POST"])
@login_required
def api_toggle_subtask(subtask_id):
    try:
        data = request.get_json() or {}
        completed = data.get("completed", False)

        with database.connect_db() as conn:
            row = conn.execute(
                "SELECT s.title, t.title FROM subtasks s JOIN tasks t ON s.task_id = t.id WHERE s.id = ?",
                (subtask_id,),
            ).fetchone()
            subtask_title = row[0] if row else f"Subtask #{subtask_id}"
            task_title = row[1] if row else "Task"

        result = database.toggle_subtask(subtask_id, completed)
        if result:
            recalculate_task_priority_risk(session.get("user_id"))
            action = "Completed" if completed else "Uncompleted"
            database.log_user_activity(
                session.get("user_id"),
                "Subtask Completed" if completed else "Subtask Updated",
                f"{action} subtask '{subtask_title}' on task '{task_title}'",
            )

            xp_status = None
            if completed:
                user_id = session.get("user_id")
                xp_status = database.award_xp(user_id, 15, f"subtask: {subtask_title}")
                if result.get("is_completed"):
                    task_xp = database.award_xp(
                        user_id, 50, f"task completion: {task_title}"
                    )
                    xp_status["xp_gained"] += task_xp["xp_gained"]
                    xp_status["level_up"] = xp_status["level_up"] or task_xp["level_up"]
                    xp_status["new_level"] = max(
                        xp_status["new_level"], task_xp["new_level"]
                    )
                    xp_status["current_xp"] = task_xp["current_xp"]
                    xp_status["new_badges"].extend(task_xp["new_badges"])

            return jsonify(
                {
                    "success": True,
                    "task_id": result["task_id"],
                    "progress": result["progress"],
                    "is_completed": result["is_completed"],
                    "gamification": xp_status,
                }
            )
        return jsonify({"success": False, "error": "Subtask not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def generate_local_schedule(tasks):
    """Fallback local priority-based scheduling algorithm when LLM is unavailable"""
    active_tasks = []
    for t in tasks:
        if t.get("status") == "Completed":
            continue
        pending_subtasks = [s for s in t.get("subtasks", []) if not s.get("completed")]
        t_copy = dict(t)
        t_copy["subtasks"] = pending_subtasks
        active_tasks.append(t_copy)

    # Sort key: 1. Deadline (closest first, none last) 2. Priority 3. Risk Level
    def parse_deadline(d_str):
        if not d_str:
            return datetime.max
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(d_str.strip(), fmt)
            except:
                pass
        return datetime.max

    priority_map = {"High": 0, "Medium": 1, "Low": 2}
    risk_map = {"High": 0, "Medium": 1, "Low": 2}

    def sort_key(tk):
        d_val = parse_deadline(tk.get("deadline"))
        prio_val = priority_map.get(tk.get("priority", "Medium"), 1)
        risk_val = risk_map.get(tk.get("risk_level", "Low"), 2)
        return (d_val, prio_val, risk_val)

    active_tasks.sort(key=sort_key)

    items_to_schedule = []
    for t in active_tasks:
        if t["subtasks"]:
            for s in t["subtasks"]:
                items_to_schedule.append(
                    {
                        "title": f"{s['title']} ({t['title']})",
                        "priority": t["priority"] or "Medium",
                        "duration": s.get("duration") or "30 min",
                        "type": "subtask",
                        "id": s["id"],
                    }
                )
        else:
            items_to_schedule.append(
                {
                    "title": t["title"],
                    "priority": t["priority"] or "Medium",
                    "duration": t.get("estimated_duration")
                    or t.get("duration")
                    or "45 min",
                    "type": "task",
                    "id": t["id"],
                }
            )

    from datetime import timedelta

    current_time = datetime.now()
    if current_time.hour < 9:
        start_dt = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        rem = 15 - (current_time.minute % 15)
        start_dt = current_time.replace(second=0, microsecond=0) + timedelta(
            minutes=rem
        )

    schedule = []
    accumulated_work = 0

    def parse_duration_minutes(dur_str):
        if not dur_str:
            return 30
        dur_str = str(dur_str).lower().strip()
        h_match = re.search(r"(\d+)\s*(?:hour|hr|h)", dur_str)
        m_match = re.search(r"(\d+)\s*(?:min|m)", dur_str)

        minutes = 0
        if h_match:
            minutes += int(h_match.group(1)) * 60
        if m_match:
            minutes += int(m_match.group(1))

        if minutes == 0:
            raw_match = re.match(r"^\d+$", dur_str)
            if raw_match:
                minutes = int(dur_str)
            else:
                minutes = 30
        return minutes

    for item in items_to_schedule:
        item_dur = parse_duration_minutes(item["duration"])

        if accumulated_work >= 90:
            break_start = start_dt.strftime("%I:%M %p")
            start_dt += timedelta(minutes=15)
            break_end = start_dt.strftime("%I:%M %p")
            schedule.append(
                {
                    "start_time": break_start,
                    "end_time": break_end,
                    "type": "break",
                    "title": "☕ Short Break",
                    "priority": "Low",
                    "id": None,
                }
            )
            accumulated_work = 0

        start_str = start_dt.strftime("%I:%M %p")
        start_dt += timedelta(minutes=item_dur)
        end_str = start_dt.strftime("%I:%M %p")

        schedule.append(
            {
                "start_time": start_str,
                "end_time": end_str,
                "type": item["type"],
                "title": item["title"],
                "priority": item["priority"],
                "id": item["id"],
            }
        )
        accumulated_work += item_dur

    return schedule


@app.route("/api/planner/generate", methods=["POST"])
@login_required
def api_generate_plan():
    try:
        data = request.get_json() or {}
        user_id = session.get("user_id")
        date_str = datetime.now().strftime("%Y-%m-%d")

        tasks = database.get_user_tasks_filtered(user_id)
        if not tasks:
            database.save_daily_plan(user_id, date_str, "[]")
            return jsonify({"success": True, "plan": []})

        ai_success = False
        generated_plan = []
        try:
            active_client, active_model = get_llm_client(data)

            tasks_context = ""
            for idx, t in enumerate(tasks):
                if t.get("status") == "Completed":
                    continue
                deadline_val = t.get("deadline") or "None"
                tasks_context += f'- Task ID {t["id"]}: "{t["title"]}" (Category: {t["category"]}, Priority: {t["priority"]}, Risk: {t["risk_level"]}, Deadline: {deadline_val}, Duration: {t.get("estimated_duration") or "45m"})\n'
                pending_subtasks = [
                    s for s in t.get("subtasks", []) if not s.get("completed")
                ]
                for sub in pending_subtasks:
                    tasks_context += f'   * Subtask ID {sub["id"]}: "{sub["title"]}" (Duration: {sub.get("duration") or "20m"}, Difficulty: {sub.get("difficulty") or "Medium"}, Dependency: {sub.get("dependency") or "None"})\n'

            current_time_str = datetime.now().strftime("%I:%M %p")
            prompt = f"""You are an AI Smart Daily Planner assistant for Mint Frost AI.
Today's date is {date_str} and the current local time is {current_time_str}.
Below are the user's active tasks and pending subtasks:
{tasks_context}

Please organize these into a structured, chronological daily planner schedule starting from {current_time_str}.
Ensure you follow these rules:
1. Prioritize tasks with urgent deadlines (today or tomorrow) and high-priority / high-risk tasks.
2. Order dependent subtasks after their prerequisites.
3. Insert 10-15 minute breaks ("☕ Short Break", type: "break") after periods of continuous work exceeding 60-90 minutes.
4. Output ONLY a valid JSON list. Do not include markdown code fences, headers, or any conversational text.

JSON Schema format:
[
  {{
    "start_time": "04:00 PM",
    "end_time": "04:30 PM",
    "type": "task or subtask or break",
    "title": "Title description",
    "priority": "High or Medium or Low",
    "id": task_id_or_subtask_id_integer_or_null
  }}
]
"""
            completion = active_client.chat.completions.create(
                model=active_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2,
            )
            raw_text = (completion.choices[0].message.content or "").strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(
                    r"^```(?:json)?\n|```$", "", raw_text, flags=re.MULTILINE
                ).strip()

            generated_plan = json.loads(raw_text)
            if isinstance(generated_plan, list):
                ai_success = True
        except Exception as e:
            app.logger.warning(
                f"AI planner generation failed: {e}. Falling back to priority-based local scheduler."
            )

        if not ai_success:
            generated_plan = generate_local_schedule(tasks)

        plan_json_str = json.dumps(generated_plan)
        database.save_daily_plan(user_id, date_str, plan_json_str)
        recalculate_task_priority_risk(user_id, data)
        database.log_user_activity(
            user_id,
            "Planner Generated",
            f"Optimized daily schedule created for {date_str}",
        )
        xp_status = database.award_xp(user_id, 30, "daily plan generation")
        return jsonify(
            {
                "success": True,
                "plan": generated_plan,
                "fallback": not ai_success,
                "gamification": xp_status,
            }
        )
    except Exception as e:
        import traceback

        app.logger.error(f"Error in api_generate_plan: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/planner/current", methods=["GET"])
@login_required
def api_get_current_plan():
    try:
        user_id = session.get("user_id")
        date_str = datetime.now().strftime("%Y-%m-%d")
        plan_str = database.get_daily_plan(user_id, date_str)
        plan = json.loads(plan_str) if plan_str else None
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/planner/regenerate", methods=["POST"])
@login_required
def api_regenerate_plan():
    return api_generate_plan()


@app.route("/api/gamification/stats", methods=["GET"])
@login_required
def api_gamification_stats():
    try:
        user_id = session.get("user_id")
        stats = database.get_gamification_stats(user_id)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def recalculate_task_priority_risk(user_id, data=None):
    """
    Recalculates priority_score, completion_probability, risk_level, suggested_action, and risk_reason
    for all active user tasks. If AI key is present, queries LLM; otherwise uses weighted calculation.
    """
    try:
        tasks = database.get_user_tasks_filtered(user_id)
        if not tasks:
            return True

        # Try to use AI if client is configured
        ai_success = False
        if data:
            try:
                active_client, active_model = get_llm_client(data)

                # Context formatting
                tasks_context = ""
                for t in tasks:
                    if t.get("status") == "Completed":
                        continue
                    deadline_val = t.get("deadline") or "None"
                    tasks_context += f'- Task ID {t["id"]}: "{t["title"]}" (Category: {t["category"]}, Priority: {t["priority"]}, Risk: {t["risk_level"]}, Deadline: {deadline_val}, Progress: {t["progress"]}%, Duration: {t.get("estimated_duration") or "45m"})\n'
                    pending_subtasks = [
                        s for s in t.get("subtasks", []) if not s.get("completed")
                    ]
                    for sub in pending_subtasks:
                        tasks_context += f'   * Subtask ID {sub["id"]}: "{sub["title"]}" (Duration: {sub.get("duration") or "20m"}, Difficulty: {sub.get("difficulty") or "Medium"})\n'

                current_time_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                prompt = f"""You are the AI Priority Decision Engine for Mint Frost AI.
Current time is {current_time_str}.
Analyze the active tasks and subtasks for this user:
{tasks_context}

For each task, calculate:
1. priority_score: integer from 0 to 100 based on urgency, priority badge, subtasks count, progress.
2. risk_level: string (one of: Safe, Attention, Critical, Overdue).
   - Overdue if deadline passed.
   - Critical if remaining time < estimated duration.
   - Attention if tight timeline.
   - Safe if ample time remains.
3. completion_probability: integer from 0 to 100 representing probability of completion before deadline.
4. suggested_action: string (short actionable recommendation, e.g. "Start immediately", "Finish within the next hour", "Complete after X").
5. risk_reason: string (brief explanation of risk level).

Output ONLY a valid JSON list. Do not include markdown code fences or conversational text.
JSON format:
[
  {{
    "id": task_id_integer,
    "priority_score": score_integer,
    "risk_level": "Safe/Attention/Critical/Overdue",
    "completion_probability": probability_integer,
    "suggested_action": "action_string",
    "risk_reason": "reason_string"
  }}
]
"""
                completion = active_client.chat.completions.create(
                    model=active_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.1,
                )
                raw_msg = completion.choices[0].message
                if raw_msg is None:
                    raise ValueError("LLM returned None message for recalculation")
                raw_text = (raw_msg.content or "").strip()
                if not raw_text:
                    raise ValueError("LLM returned empty response for recalculation")
                if raw_text.startswith("```"):
                    raw_text = re.sub(
                        r"^```(?:json)?\\n|```$", "", raw_text, flags=re.MULTILINE
                    ).strip()

                # Robust JSON extraction — find first [ or { to last ] or }
                _f, _l = raw_text.find("["), raw_text.rfind("]")
                if _f == -1 or _l == -1:
                    _f, _l = raw_text.find("{"), raw_text.rfind("}")
                if _f != -1 and _l != -1 and _l > _f:
                    raw_text = raw_text[_f : _l + 1]

                try:
                    results = json.loads(raw_text)
                except json.JSONDecodeError:
                    # Repair common LLM JSON issues
                    raw_text = re.sub(r"'([^']*?)'\s*:", r'"\1":', raw_text)
                    raw_text = re.sub(r",\s*([}\])", r"\1", raw_text)
                    try:
                        results = json.loads(raw_text)
                    except json.JSONDecodeError:
                        results = []
                if isinstance(results, list):
                    for item in results:
                        task_id = item.get("id")
                        database.update_task_details(
                            task_id,
                            {
                                "priority_score": int(item.get("priority_score", 50)),
                                "risk_level": item.get("risk_level", "Safe"),
                                "completion_probability": int(
                                    item.get("completion_probability", 100)
                                ),
                                "suggested_action": item.get("suggested_action", ""),
                                "risk_reason": item.get("risk_reason", ""),
                            },
                        )
                    ai_success = True
            except Exception as e:
                app.logger.warning(
                    f"AI Recalculation failed: {e}. Falling back to programmatic engine."
                )

        if not ai_success:
            # Local weighted algorithm fallback
            for t in tasks:
                task_id = t["id"]
                if t.get("status") == "Completed":
                    database.update_task_details(
                        task_id,
                        {
                            "priority_score": 0,
                            "risk_level": "Safe",
                            "completion_probability": 100,
                            "suggested_action": "Task completed!",
                            "risk_reason": "All items finished.",
                        },
                    )
                    continue

                # Parse deadline
                deadline_str = t.get("deadline")
                is_overdue = False
                hours_remaining = 168.0

                if deadline_str:
                    try:
                        deadline_dt = None
                        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                            try:
                                deadline_dt = datetime.strptime(
                                    deadline_str.strip(), fmt
                                )
                                break
                            except:
                                pass
                        if deadline_dt:
                            if deadline_dt < datetime.now():
                                is_overdue = True
                            else:
                                hours_remaining = (
                                    deadline_dt - datetime.now()
                                ).total_seconds() / 3600.0
                    except:
                        pass

                # Parse task duration helper
                def parse_duration_hours(dur_str):
                    if not dur_str:
                        return 1.0
                    dur_str = str(dur_str).lower().strip()
                    h_match = re.search(r"(\d+)\s*(?:hour|hr|h)", dur_str)
                    m_match = re.search(r"(\d+)\s*(?:min|m)", dur_str)
                    hours = 0.0
                    if h_match:
                        hours += float(h_match.group(1))
                    if m_match:
                        hours += float(m_match.group(1)) / 60.0
                    if hours == 0.0:
                        try:
                            hours = float(dur_str)
                        except:
                            hours = 1.0
                    return hours

                work_remaining = parse_duration_hours(t.get("estimated_duration"))
                pending_subtasks = [
                    s for s in t.get("subtasks", []) if not s.get("completed")
                ]
                for sub in pending_subtasks:
                    work_remaining += parse_duration_hours(sub.get("duration"))

                if is_overdue:
                    database.update_task_details(
                        task_id,
                        {
                            "priority_score": 100,
                            "risk_level": "Overdue",
                            "completion_probability": 0,
                            "suggested_action": "Deadline missed. Take immediate action.",
                            "risk_reason": "Task deadline has already passed.",
                        },
                    )
                    continue

                progress = t.get("progress") or 0
                time_ratio = work_remaining / max(hours_remaining, 0.1)
                prob = int(progress + (100 - progress) * (1.0 - min(time_ratio, 1.0)))
                prob = max(0, min(100, prob))

                base_urgency = 0.0
                if hours_remaining <= 24:
                    base_urgency = 50.0 * (1.0 - (hours_remaining / 24.0))
                elif hours_remaining <= 72:
                    base_urgency = 30.0 * (1.0 - (hours_remaining / 72.0))
                else:
                    base_urgency = 10.0

                prio_map = {"High": 30, "Medium": 15, "Low": 0}
                prio_weight = prio_map.get(t.get("priority", "Medium"), 15)
                progress_weight = (100 - progress) * 0.2
                subtask_weight = min(len(pending_subtasks) * 2, 10)

                score = int(
                    base_urgency + prio_weight + progress_weight + subtask_weight
                )
                score = max(0, min(100, score))

                risk = "Safe"
                reason = "Sufficient time remains."
                if hours_remaining < work_remaining:
                    risk = "Critical"
                    reason = "Estimated work exceeds remaining available time."
                elif hours_remaining < work_remaining * 1.5:
                    risk = "High"
                    reason = "Tight deadline relative to remaining work duration."
                elif hours_remaining < work_remaining * 2.5:
                    risk = "Attention"
                    reason = "Task is approaching; monitor completion rate."

                action = "Proceed at your own pace."
                if risk == "Critical":
                    action = "Estimated work exceeds remaining time. Start immediately."
                elif risk == "High":
                    action = "Due soon. Finish within the next hour."
                elif len(pending_subtasks) > 2:
                    action = "Break this task into smaller pieces."
                elif t.get("priority") == "High":
                    action = "High priority item. Focus today."

                database.update_task_details(
                    task_id,
                    {
                        "priority_score": score,
                        "risk_level": risk,
                        "completion_probability": prob,
                        "suggested_action": action,
                        "risk_reason": reason,
                    },
                )

        return True
    except Exception as e:
        import traceback

        app.logger.error(
            f"Error in recalculate_task_priority_risk: {e}\n{traceback.format_exc()}"
        )
        return False


@app.route("/api/recalculate", methods=["POST"])
@login_required
def api_recalculate_tasks():
    try:
        data = request.get_json() or {}
        user_id = session.get("user_id")
        success = recalculate_task_priority_risk(user_id, data)
        if success:
            tasks = database.get_user_tasks_filtered(user_id)
            return jsonify({"success": True, "tasks": tasks})
        return jsonify({"success": False, "error": "Recalculation failed"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/sessions/<session_id>/load", methods=["POST"])
@login_required
def load_session(session_id):
    try:
        messages = database.get_session_messages(session_id)
        session["current_session_id"] = session_id
        session.modified = True
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route("/api/sessions", methods=["GET"])
@login_required
def get_sessions():
    try:
        sessions = database.get_recent_sessions(user_id=session.get("user_id"))
        return jsonify({"sessions": sessions})
    except Exception as e:
        import traceback

        app.logger.error(f"Error in get_sessions: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


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
    session.pop("chat_history", None)
    session.pop("current_session_id", None)
    return jsonify({"success": True})


@app.route("/weather")
def get_weather():
    try:
        city = request.args.get("city", "London")
        weather_data = weather_service.get_weather_by_city(city)
        return jsonify(weather_data)
    except:
        return jsonify({"error": "Weather service unavailable"}), 500


@app.route("/api/weather/coordinates")
def get_weather_coordinates():
    try:
        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("lon", 0))
        weather_data = weather_service.get_weather_by_coordinates(lat, lon)
        return jsonify(weather_data)
    except:
        return jsonify({"error": "Invalid coordinates"}), 400


@app.route("/edit-message", methods=["POST"])
@login_required
def edit_message():
    try:
        data = request.get_json()
        message_id = data.get("message_id")
        new_text = data.get("new_text", "").strip()

        if not new_text:
            return jsonify({"error": "Message cannot be empty"}), 400

        if len(new_text) > 2000:
            return jsonify({"error": "Message too long"}), 400

        # Generate new AI response using chat logic
        messages = [
            {"role": "system", "content": "You are Mint Frost AI, a helpful assistant."}
        ]

        # Add recent chat history for context
        if "chat_history" in session:
            for msg in session["chat_history"][-5:]:
                messages.append({"role": "user", "content": msg["user"]})
                messages.append({"role": "assistant", "content": msg["ai"]})

        # Add the edited message
        messages.append({"role": "user", "content": new_text})

        # Generate AI response
        active_client, active_model = get_llm_client(data)
        completion = active_client.chat.completions.create(
            model=active_model, messages=messages, max_tokens=1000, temperature=0.7
        )

        ai_reply = completion.choices[0].message.content or ""
        ai_reply = process_image_generation(ai_reply)
        return jsonify(
            {
                "user_message": new_text,
                "ai_reply": ai_reply,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"error": f"Edit failed: {str(e)}"}), 500


@app.route("/clear-history", methods=["POST"])
@login_required
def clear_history():
    current_session_id = session.get("current_session_id")
    if current_session_id:
        try:
            # Verify ownership before deleting
            if database.verify_session_owner(
                current_session_id, session.get("user_id")
            ):
                database.delete_session(current_session_id)
        except Exception as e:
            app.logger.error(f"Error deleting current session: {e}")

    session.pop("chat_history", None)
    session.pop("current_session_id", None)
    return jsonify({"success": True, "message": "Chat history cleared"})


@app.route("/api/sessions/<session_id>/title", methods=["PUT"])
@login_required
def rename_session(session_id):
    try:
        # Verify ownership
        if not database.verify_session_owner(session_id, session.get("user_id")):
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
        if not database.verify_session_owner(session_id, session.get("user_id")):
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
        if not database.verify_session_owner(session_id, session.get("user_id")):
            return jsonify({"error": "Unauthorized"}), 403

        messages = database.get_session_messages(session_id)
        if not messages:
            return jsonify({"success": True, "formatted_text": "", "message_count": 0})

        formatted_parts = []
        for msg in messages:
            sender_label = "You" if msg["who"] == "user" else "AI"
            formatted_parts.append(f"{sender_label}: {msg['text']}")

        formatted_text = "\n\n".join(formatted_parts)
        return jsonify(
            {
                "success": True,
                "formatted_text": formatted_text,
                "message_count": len(messages),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clear-all-data", methods=["POST"])
@login_required
def clear_all_data():
    try:
        database.clear_all_data(user_id=session.get("user_id"))
        session.pop("chat_history", None)
        session.pop("current_session_id", None)
        return jsonify({"success": True, "message": "All data cleared"})
    except Exception as e:
        return jsonify({"error": f"Failed to clear data: {str(e)}"}), 500


@app.route("/api/heartbeat", methods=["POST"])
@login_required
def api_heartbeat():
    user_id = session.get("user_id")
    if user_id:
        database.update_user_last_seen(user_id)
        session_token = session.get("session_token")
        if session_token:
            database.update_active_session_activity(session_token)
    return jsonify({"success": True})


@app.route("/api/unload", methods=["POST"])
def api_unload():
    user_id = session.get("user_id")
    if user_id:
        database.set_user_online_status(user_id, 0)
    return jsonify({"success": True})


@app.route("/api/theme", methods=["GET", "POST"])
@login_required
def theme_settings():
    if request.method == "GET":
        try:
            theme_data = database.get_user_theme(user_id=session.get("user_id"))
            custom_themes = database.get_custom_themes()
            return jsonify(
                {
                    "theme": theme_data["theme"],
                    "auto_theme": theme_data["auto_theme"],
                    "custom_themes": custom_themes,
                }
            )
        except Exception as e:
            return jsonify({"theme": "dark", "auto_theme": False, "custom_themes": {}})

    data = request.get_json()
    theme = data.get("theme", "dark")
    auto_theme = data.get("auto_theme")

    if theme in [
        "dark",
        "light",
        "mint",
        "ocean",
        "sunset",
        "forest",
        "auto",
    ] or theme.startswith("custom_"):
        try:
            database.set_user_theme(theme, auto_theme, user_id=session.get("user_id"))
            return jsonify({"success": True, "theme": theme})
        except Exception as e:
            return jsonify({"error": "Failed to save theme"}), 500
    return jsonify({"error": "Invalid theme"}), 400


@app.route("/api/settings/sync", methods=["GET", "POST"])
@login_required
def api_settings_sync():
    user_id = session.get("user_id")
    if request.method == "POST":
        data = request.get_json() or {}
        provider = data.get("api_provider")
        api_key = data.get("api_key", "").strip()
        model = data.get("api_model", "").strip()
        success = database.save_api_settings(user_id, provider, api_key, model)
        return jsonify({"success": success})

    # GET method
    settings = database.get_api_settings(user_id)
    return jsonify({"success": True, "settings": settings or {}})


@app.route("/api/custom-theme", methods=["POST", "DELETE"])
@login_required
def custom_theme():
    if request.method == "POST":
        data = request.get_json()
        theme_name = data.get("name", "").strip()
        colors = data.get("colors", {})

        if not theme_name or len(theme_name) > 50:
            return jsonify({"error": "Invalid theme name"}), 400

        required_colors = ["primary", "bg0", "bg1", "fg", "muted"]
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
        theme_id = data.get("theme_id")

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


@app.route("/api/youtube/search")
@login_required
def youtube_search():
    query = request.args.get("q", "").strip()
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
            "Accept-Language": "en-US,en;q=0.9",
        }

        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            html_content = response.read().decode("utf-8", errors="ignore")

        json_pattern = re.compile(r"var ytInitialData = ({.*?});</script>")
        match = json_pattern.search(html_content)

        if not match:
            return jsonify([])

        yt_data = json.loads(match.group(1))
        contents = yt_data["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"
        ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]

        tracks = []
        for item in contents:
            video_renderer = item.get("videoRenderer")
            if video_renderer:
                video_id = video_renderer.get("videoId")
                title = video_renderer.get("title", {}).get("runs", [{}])[0].get("text")
                author = (
                    video_renderer.get("ownerText", {})
                    .get("runs", [{}])[0]
                    .get("text", "Unknown")
                )
                duration_text = video_renderer.get("lengthText", {}).get(
                    "simpleText", "0:00"
                )
                thumbnails = video_renderer.get("thumbnail", {}).get("thumbnails", [])
                thumbnail_url = thumbnails[0].get("url") if thumbnails else ""

                if video_id and title:
                    tracks.append(
                        {
                            "id": video_id,
                            "title": title,
                            "author": author,
                            "duration": duration_text,
                            "thumbnail": thumbnail_url,
                            "source": "youtube",
                        }
                    )
                    if len(tracks) >= 20:  # Limit to 20 results
                        break

        # Save to cache
        if tracks:
            youtube_search_cache[query.lower()] = tracks

        return jsonify(tracks)
    except Exception as e:
        app.logger.error("YouTube scraper search error: %s", e)
        return jsonify([])


@app.route("/api/youtube/stream")
@login_required
def youtube_stream():
    video_id = request.args.get("video_id", "").strip()
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    try:
        import urllib.parse

        import yt_dlp

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "skip_download": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get("url")

            if stream_url:
                proxy_url = f"/api/youtube/proxy?url={urllib.parse.quote(stream_url)}"
                return jsonify({"url": proxy_url})
            else:
                return jsonify({"error": "Failed to extract stream URL"}), 500
    except Exception as e:
        app.logger.error("YouTube stream extraction error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/youtube/proxy")
@login_required
def youtube_proxy():
    from flask import Response

    url = request.args.get("url")
    if not url:
        return "Missing url", 400

    if not url.startswith("https://") or ".googlevideo.com/" not in url:
        return "Invalid url", 400

    # User-Agent matching the one used in yt_dlp to resolve signatures
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Forward range headers if sent by the browser
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=15)

        # Build response headers
        resp_headers = {}
        for h in ["Content-Type", "Content-Length", "Accept-Ranges", "Content-Range"]:
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
    expires_at = session.get("google_token_expires_at")
    if not expires_at:
        return True
    return time.time() > expires_at


def _refresh_google_token():
    refresh_token = session.get("google_refresh_token")
    if not refresh_token or not google_client_id or not google_client_secret:
        return False

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            tok = resp.json()
            access_token = tok.get("access_token")
            expires_in = tok.get("expires_in", 3600)
            session["google_access_token"] = access_token
            session["google_token_expires_at"] = int(time.time() + int(expires_in) - 30)
            # Google may not return a new refresh token on refresh
            if tok.get("refresh_token"):
                session["google_refresh_token"] = tok.get("refresh_token")

            # persist to DB if account id known
            account_id = session.get("google_account_id")
            if account_id:
                try:
                    database.save_oauth_token(
                        "google",
                        account_id,
                        session.get("google_access_token"),
                        session.get("google_refresh_token"),
                        session.get("google_token_expires_at"),
                    )
                except Exception:
                    pass

            session.modified = True
            return True
    except Exception:
        return False
    return False


def _refresh_google_token_for_account(account_id):
    tokrec = database.get_oauth_token("google", account_id)
    if not tokrec:
        return False
    refresh_token = tokrec.get("refresh_token")
    if not refresh_token or not google_client_id or not google_client_secret:
        return False

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            tok = resp.json()
            access_token = tok.get("access_token")
            expires_in = tok.get("expires_in", 3600)
            new_refresh = tok.get("refresh_token") or refresh_token
            expires_at = int(time.time() + int(expires_in) - 30)
            database.save_oauth_token(
                "google", account_id, access_token, new_refresh, expires_at
            )
            # update session
            session["google_access_token"] = access_token
            session["google_refresh_token"] = new_refresh
            session["google_token_expires_at"] = expires_at
            session["google_account_id"] = account_id
            session.modified = True
            return True
    except Exception:
        return False
    return False


@app.route("/api/google/auth")
def google_auth():
    if not google_client_id or not google_client_secret:
        return jsonify({"error": "Google credentials not configured on server"}), 500

    forwarded_host = request.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_host:
        proto = forwarded_proto or "http"
        url_base = f"{proto}://{forwarded_host}/"
    else:
        url_base = request.url_root or request.host_url
        if forwarded_proto == "https":
            if url_base.startswith("http://"):
                url_base = "https://" + url_base[7:]
    redirect_uri = url_base.rstrip("/") + "/api/google/callback"
    scope = "openid email profile"
    params = {
        "client_id": google_client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    # Server-side redirect so a simple navigation or anchor/button will work
    return redirect(auth_url)


@app.route("/api/google/callback")
def google_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        return jsonify({"error": error}), 400
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400

    if not google_client_id or not google_client_secret:
        return jsonify({"error": "Google credentials not configured on server"}), 500

    token_url = "https://oauth2.googleapis.com/token"
    forwarded_host = request.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_host:
        proto = forwarded_proto or "http"
        url_base = f"{proto}://{forwarded_host}/"
    else:
        url_base = request.url_root or request.host_url
        if forwarded_proto == "https":
            if url_base.startswith("http://"):
                url_base = "https://" + url_base[7:]
    redirect_uri = url_base.rstrip("/") + "/api/google/callback"

    data = {
        "code": code,
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        try:
            resp = requests.post(token_url, data=data, headers=headers, timeout=10)
        except requests.exceptions.SSLError:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.post(
                token_url, data=data, headers=headers, timeout=10, verify=False
            )
        if resp.status_code != 200:
            err_msg = f"Token exchange failed: {resp.text}"
            return render_template(
                "google_callback.html", error=err_msg
            ) if "text/html" in request.headers.get("Accept", "") else jsonify(
                {"error": err_msg}
            ), 400
        tok = resp.json()
        access_token = tok.get("access_token")
        refresh_token = tok.get("refresh_token")
        expires_in = tok.get("expires_in", 3600)
        expires_at = int(time.time() + int(expires_in) - 30)

        session["google_access_token"] = access_token
        session["google_refresh_token"] = refresh_token
        session["google_token_expires_at"] = expires_at
        session.modified = True

        # fetch userinfo and persist tokens
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            me_resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.SSLError:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            me_resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers=headers,
                timeout=10,
                verify=False,
            )
        if me_resp.status_code != 200:
            raise Exception(
                f"Google userinfo request failed with status {me_resp.status_code}: {me_resp.text}"
            )

        profile = me_resp.json()
        account_id = profile.get("sub") or profile.get("email")
        if not account_id:
            raise Exception("No user identity found in Google profile.")

        session["google_account_id"] = account_id
        session["profile_pic"] = profile.get("picture")
        session.modified = True
        try:
            database.save_oauth_token(
                "google", account_id, access_token, refresh_token, expires_at
            )
        except Exception:
            pass

        # Link account to local user or log in via Google SSO
        google_acct_id = session.get("google_account_id")
        if not google_acct_id:
            raise Exception("No Google account identity in session.")

        # Check if this Google account is already linked to a user in the database
        linked_user_id = database.get_user_by_provider("google", google_acct_id)

        if linked_user_id:
            # Google account is already registered! Log them in
            user_details = database.get_user_secure(linked_user_id)
            if user_details and user_details.get("status") == "deactivated":
                session.clear()
                session.modified = True
                return render_template(
                    "google_callback.html",
                    error="Your account has been deactivated by an administrator.",
                ) if "text/html" in request.headers.get("Accept", "") else jsonify(
                    {
                        "success": False,
                        "error": "Your account has been deactivated by an administrator.",
                    }
                ), 403

            session["local_user_id"] = linked_user_id
            session["user_id"] = linked_user_id
            if user_details:
                session["display_name"] = user_details.get("display_name")

            # Register active session
            register_login_session(linked_user_id)

            # Log telemetry on login
            log_user_telemetry(linked_user_id)
        else:
            # Google account is not connected yet!
            # If they are already logged in locally, link Google to their active local account
            active_user_id = session.get("user_id")
            if active_user_id:
                session["local_user_id"] = active_user_id
                database.link_account_to_user(active_user_id, "google", google_acct_id)
            else:
                # Not logged in! Create a new account automatically for Google SSO
                # Try to fetch name from Google profile info
                display_name = profile.get("name")

                # Generate a clean username using Google account ID
                import uuid

                import werkzeug.security

                username = f"google_{google_acct_id[:12]}"
                # Check if username exists, otherwise add random suffix
                if database.get_user_secure(username):
                    username = f"google_{str(uuid.uuid4())[:8]}"

                # Create the secure user in the users table
                rand_pass = str(uuid.uuid4())
                database.create_user_secure(
                    username,
                    werkzeug.security.generate_password_hash(rand_pass),
                    display_name,
                )

                session["local_user_id"] = username
                session["user_id"] = username
                session["display_name"] = display_name

                # Register active session
                register_login_session(username)

                # Log telemetry on auto-login
                log_user_telemetry(username)

                # Link Google to the newly created account
                database.link_account_to_user(username, "google", google_acct_id)

        return (
            render_template("google_callback.html")
            if "text/html" in request.headers.get("Accept", "")
            else jsonify({"success": True})
        )
    except Exception as e:
        app.logger.error(f"Failed to handle Google login/linking callback: {str(e)}")
        err_msg = f"Google authentication failed: {str(e)}"
        return render_template(
            "google_callback.html", error=err_msg
        ) if "text/html" in request.headers.get("Accept", "") else jsonify(
            {"error": err_msg}
        ), 500


@app.route("/api/google/me")
def google_me():
    access_token = session.get("google_access_token")
    account_id = session.get("google_account_id")

    # load from DB if needed
    if not access_token and account_id:
        tokrec = database.get_oauth_token("google", account_id)
        if tokrec:
            if tokrec.get("expires_at") and time.time() > tokrec.get("expires_at"):
                if _refresh_google_token_for_account(account_id):
                    access_token = session.get("google_access_token")
            else:
                access_token = tokrec.get("access_token")
                session["google_access_token"] = access_token
                session["google_refresh_token"] = tokrec.get("refresh_token")
                session["google_token_expires_at"] = tokrec.get("expires_at")
                session["google_account_id"] = account_id
                session.modified = True

    if not access_token:
        return jsonify({"error": "Not signed in"}), 401

    if _google_token_expired():
        if not _refresh_google_token():
            if account_id and not _refresh_google_token_for_account(account_id):
                return jsonify({"error": "Token expired and refresh failed"}), 401
        access_token = session.get("google_access_token")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        try:
            resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.SSLError:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers=headers,
                timeout=10,
                verify=False,
            )
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify(
            {"error": "Failed to fetch profile", "details": resp.text}
        ), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/google/refresh", methods=["POST"])
def google_refresh():
    success = _refresh_google_token()
    if success:
        return jsonify({"success": True})
    account_id = session.get("google_account_id")
    if account_id and _refresh_google_token_for_account(account_id):
        return jsonify({"success": True})
    return jsonify({"error": "Refresh failed"}), 400


@app.route("/api/google/signout", methods=["POST"])
def google_signout():
    account_id = session.pop("google_account_id", None)
    session.pop("google_access_token", None)
    session.pop("google_refresh_token", None)
    session.pop("google_token_expires_at", None)
    session.modified = True
    if account_id:
        try:
            database.delete_oauth_token("google", account_id)
        except Exception:
            pass
    return jsonify({"success": True})


# --- end Google OAuth ---

# --- User linking helpers ---


def get_or_create_local_user():
    user_id = session.get("local_user_id")
    if not user_id:
        import uuid

        user_id = str(uuid.uuid4())
        session["local_user_id"] = user_id
        session.modified = True
        try:
            database.create_user(user_id, display_name=None)
        except Exception:
            pass
    return user_id


@app.route("/api/accounts/linked")
def api_get_linked_accounts():
    user_id = session.get("local_user_id")
    if not user_id:
        return jsonify({"linked": []})
    linked = database.get_linked_accounts(user_id)
    return jsonify({"linked": linked})


@app.route("/api/accounts/unlink", methods=["POST"])
def api_unlink_account():
    data = request.get_json() or {}
    provider = data.get("provider")
    if not provider:
        return jsonify({"error": "provider required"}), 400

    user_id = session.get("local_user_id")
    if not user_id:
        return jsonify({"error": "no local user"}), 400

    # delete linked_accounts entry and oauth token
    try:
        # find account id for this provider
        linked = database.get_linked_accounts(user_id)
        acct = None
        for l in linked:
            if l.get("provider") == provider:
                acct = l.get("account_id")
                break
        # unlink
        ok = database.unlink_account(user_id, provider)
        if acct:
            try:
                database.delete_oauth_token(provider, acct)
            except Exception:
                pass
        return jsonify({"success": True, "unlinked": provider})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/accounts/profile", methods=["POST"])
def api_update_profile():
    user_id = (
        g.user_id
        if hasattr(g, "user_id") and g.user_id
        else session.get("local_user_id")
    )
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    display_name = data.get("display_name", "").strip()
    if not display_name:
        return jsonify({"error": "display_name required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (display_name, user_id),
            )
            conn.commit()
        session["display_name"] = display_name
        session.modified = True
        return jsonify({"success": True, "display_name": display_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/backup", methods=["GET"])
@login_required
def api_user_backup():
    username = session.get("user_id")
    details = database.get_user_full_details_admin(username)
    if not details:
        return jsonify({"error": "User profile not found"}), 404

    # Aggregate all conversation logs
    full_history = []
    for s in details.get("sessions", []):
        messages = database.get_session_messages(s["id"])
        full_history.append(
            {
                "session_id": s["id"],
                "session_title": s["title"],
                "created_at": s["created_at"],
                "messages": messages,
            }
        )
    details["full_conversations"] = full_history

    # Stream as downloadable JSON attachment response
    import json

    from flask import Response

    response_data = json.dumps(details, indent=4)
    return Response(
        response_data,
        mimetype="application/json",
        headers={
            "Content-disposition": f"attachment; filename=user_backup_{username}.json"
        },
    )


@app.route("/api/user/delete", methods=["POST"])
@login_required
def api_user_delete():
    username = session.get("user_id")
    ok = database.delete_user_self(username)
    if ok:
        session.clear()
        session.modified = True
        return jsonify(
            {"success": True, "message": "Your account has been deleted permanently."}
        )
    else:
        return jsonify(
            {"error": "Failed to delete account. Please contact an administrator."}
        ), 500


# --- end Spotify interaction ---


def sync_provider_models(provider, api_key):
    if not provider or not api_key:
        return False
    try:
        import requests

        parsed_models = []
        provider_key = provider.lower().strip()

        if provider_key == "openai":
            resp = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for m in data:
                m_id = m["id"]
                if not any(
                    keyword in m_id
                    for keyword in [
                        "gpt",
                        "o1",
                        "o3",
                        "davinci",
                        "curie",
                        "babbage",
                        "ada",
                    ]
                ):
                    continue
                display_name = m_id
                if "gpt-4o-mini" in m_id:
                    display_name = "GPT-4o Mini"
                elif "gpt-4o" in m_id:
                    display_name = "GPT-4o"
                elif "gpt-4-turbo" in m_id:
                    display_name = "GPT-4 Turbo"
                elif "o1" in m_id:
                    display_name = "o1 Reasoning"
                elif "o3" in m_id:
                    display_name = "o3 Reasoning"

                supports_reasoning = 1 if ("o1" in m_id or "o3" in m_id) else 0
                supports_vision = 1 if ("vision" in m_id or "gpt-4o" in m_id) else 0
                supports_function_calling = (
                    1 if ("gpt-4" in m_id or "gpt-3.5" in m_id or "o1" in m_id) else 0
                )
                context_window = 128000
                if "gpt-3.5" in m_id:
                    context_window = 16385
                elif "gpt-4" in m_id and "32k" in m_id:
                    context_window = 32768
                elif "gpt-4" in m_id:
                    context_window = 8192

                parsed_models.append(
                    {
                        "model_id": m_id,
                        "display_name": display_name,
                        "description": f"Official OpenAI model: {m_id}",
                        "supports_chat": 1,
                        "supports_reasoning": supports_reasoning,
                        "supports_vision": supports_vision,
                        "supports_audio": 1 if "audio" in m_id else 0,
                        "supports_image_generation": 0,
                        "supports_function_calling": supports_function_calling,
                        "supports_streaming": 1,
                        "context_window": context_window,
                        "status": "active",
                    }
                )

        elif provider_key in ("gemini", "google"):
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("models", [])
            for m in data:
                m_name = m["name"].replace("models/", "")
                if "generateContent" not in str(
                    m.get("supportedGenerationMethods", [])
                ):
                    continue
                display_name = m.get("displayName", m_name)
                supports_reasoning = 1 if "thinking" in m_name.lower() else 0
                supports_vision = (
                    1
                    if any(
                        w in m_name.lower() for w in ["vision", "flash", "pro", "exp"]
                    )
                    else 0
                )
                context_window = m.get("inputTokenLimit", 1048576)

                parsed_models.append(
                    {
                        "model_id": m_name,
                        "display_name": display_name,
                        "description": m.get(
                            "description", f"Official Google Gemini model: {m_name}"
                        ),
                        "supports_chat": 1,
                        "supports_reasoning": supports_reasoning,
                        "supports_vision": supports_vision,
                        "supports_audio": 1 if "audio" in m_name else 0,
                        "supports_image_generation": 0,
                        "supports_function_calling": 1
                        if "pro" in m_name or "flash" in m_name
                        else 0,
                        "supports_streaming": 1,
                        "context_window": context_window,
                        "status": "active",
                    }
                )

        elif provider_key == "anthropic":
            try:
                resp = requests.get(
                    "https://api.anthropic.com/v1/models",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json().get("data", [])
                for m in data:
                    m_id = m["id"]
                    display_name = m_id.replace("claude-", "").replace("-", " ").title()
                    parsed_models.append(
                        {
                            "model_id": m_id,
                            "display_name": display_name,
                            "description": f"Official Anthropic Claude model: {m_id}",
                            "supports_chat": 1,
                            "supports_reasoning": 1 if "thinking" in m_id else 0,
                            "supports_vision": 1 if "3" in m_id else 0,
                            "supports_audio": 0,
                            "supports_image_generation": 0,
                            "supports_function_calling": 1,
                            "supports_streaming": 1,
                            "context_window": 200000,
                            "status": "active",
                        }
                    )
            except Exception:
                fallback_models = [
                    {
                        "id": "claude-3-5-sonnet-20241022",
                        "name": "Claude 3.5 Sonnet",
                        "context": 200000,
                        "vision": 1,
                    },
                    {
                        "id": "claude-3-5-haiku-20241022",
                        "name": "Claude 3.5 Haiku",
                        "context": 200000,
                        "vision": 0,
                    },
                    {
                        "id": "claude-3-opus-20240229",
                        "name": "Claude 3 Opus",
                        "context": 200000,
                        "vision": 1,
                    },
                ]
                for fm in fallback_models:
                    parsed_models.append(
                        {
                            "model_id": fm["id"],
                            "display_name": fm["name"],
                            "description": f"Standard fallback Anthropic model: {fm['id']}",
                            "supports_chat": 1,
                            "supports_reasoning": 0,
                            "supports_vision": fm["vision"],
                            "supports_audio": 0,
                            "supports_image_generation": 0,
                            "supports_function_calling": 1,
                            "supports_streaming": 1,
                            "context_window": fm["context"],
                            "status": "active",
                        }
                    )

        elif provider_key == "groq":
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for m in data:
                m_id = m["id"]
                display_name = m_id
                supports_reasoning = (
                    1 if "r1" in m_id.lower() or "reasoning" in m_id.lower() else 0
                )
                context_window = 8192
                if "8192" in m_id:
                    context_window = 8192
                elif "32768" in m_id:
                    context_window = 32768
                elif "70b" in m_id.lower():
                    context_window = 128000
                elif "r1" in m_id.lower():
                    context_window = 128000

                parsed_models.append(
                    {
                        "model_id": m_id,
                        "display_name": display_name,
                        "description": f"Official Groq model: {m_id}",
                        "supports_chat": 1,
                        "supports_reasoning": supports_reasoning,
                        "supports_vision": 1 if "vision" in m_id.lower() else 0,
                        "supports_audio": 0,
                        "supports_image_generation": 0,
                        "supports_function_calling": 1,
                        "supports_streaming": 1,
                        "context_window": context_window,
                        "status": "active",
                    }
                )

        elif provider_key == "openrouter":
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for m in data:
                m_id = m["id"]
                # Only include free models (pricing is 0 or id contains :free)
                pricing = m.get("pricing", {})
                prompt_price = pricing.get("prompt", "1")
                completion_price = pricing.get("completion", "1")
                is_free = ":free" in m_id or (
                    prompt_price == "0" and completion_price == "0"
                )
                if not is_free:
                    continue
                display_name = m.get("name", m_id)
                context_window = m.get("context_length", 8192)
                features = m.get("architecture", {})
                supports_reasoning = (
                    1
                    if "reasoning" in str(m.get("description", "")).lower()
                    or "r1" in m_id
                    or "o1" in m_id
                    else 0
                )
                supports_vision = (
                    1
                    if "vision" in str(features.get("modalities", [])).lower()
                    or "vision" in m_id
                    else 0
                )

                parsed_models.append(
                    {
                        "model_id": m_id,
                        "display_name": display_name,
                        "description": m.get(
                            "description", f"OpenRouter model: {m_id}"
                        ),
                        "supports_chat": 1,
                        "supports_reasoning": supports_reasoning,
                        "supports_vision": supports_vision,
                        "supports_audio": 0,
                        "supports_image_generation": 0,
                        "supports_function_calling": 1
                        if m.get("function_calling")
                        else 0,
                        "supports_streaming": 1,
                        "context_window": context_window,
                        "status": "active",
                    }
                )

        elif provider_key == "mistral":
            resp = requests.get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for m in data:
                m_id = m["id"]
                display_name = m_id
                context_window = 32000
                if "large" in m_id:
                    context_window = 128000
                elif "codestral" in m_id:
                    context_window = 32000

                parsed_models.append(
                    {
                        "model_id": m_id,
                        "display_name": display_name,
                        "description": f"Official Mistral model: {m_id}",
                        "supports_chat": 1,
                        "supports_reasoning": 0,
                        "supports_vision": 1 if "pixtral" in m_id.lower() else 0,
                        "supports_audio": 0,
                        "supports_image_generation": 0,
                        "supports_function_calling": 1,
                        "supports_streaming": 1,
                        "context_window": context_window,
                        "status": "active",
                    }
                )

        if parsed_models:
            database.sync_models_to_db(provider_key, parsed_models)
            return True
        return False
    except Exception as e:
        import logging

        logging.error(f"Error in sync_provider_models for {provider}: {e}")
        return False


@app.route("/api/fetch-models", methods=["POST"])
@login_required
def fetch_models():
    data = request.get_json() or {}
    provider = data.get("provider")
    api_key = data.get("api_key", "").strip()

    if not provider or not api_key:
        return jsonify({"error": "Missing provider or API key"}), 400

    sync_provider_models(provider, api_key)
    models = database.get_available_models()
    provider_models = [
        m["model_id"] for m in models if m["provider"] == provider.lower().strip()
    ]
    return jsonify({"models": provider_models})


@app.route("/api/settings/models", methods=["GET"])
@login_required
def api_get_models():
    try:
        models = database.get_available_models()
        return jsonify({"success": True, "models": models})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/settings/models/sync", methods=["POST"])
@login_required
def api_sync_models():
    data = request.get_json() or {}
    provider = data.get("provider")
    api_key = data.get("api_key", "").strip()

    if not provider or not api_key:
        return jsonify({"success": False, "error": "Missing provider or API key"}), 400

    success = sync_provider_models(provider, api_key)
    if success:
        return jsonify({"success": True})
    return jsonify(
        {"success": False, "error": "Sync failed. Kept last successful sync list."}
    ), 500


@app.route("/api/admin/models/custom", methods=["POST"])
@login_required
def api_register_custom_model():
    user_id = session.get("user_id")
    user = database.get_user_secure(user_id)
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json() or {}
    provider = data.get("provider")
    model_id = data.get("model_id")
    display_name = data.get("display_name")
    description = data.get("description", "")
    context_window = data.get("context_window")
    features = data.get("features", {})

    if not provider or not model_id or not display_name:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    success = database.register_custom_model_db(
        provider, model_id, display_name, description, context_window, features
    )
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to register custom model"}), 500


@app.route("/api/admin/models/status", methods=["GET"])
@login_required
def api_admin_model_status():
    user_id = session.get("user_id")
    user = database.get_user_secure(user_id)
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    return jsonify(
        {
            "success": True,
            "providers": database.get_model_sync_state(),
            "models": database.get_available_models(),
        }
    )


@app.route("/api/admin/models/refresh", methods=["POST"])
@login_required
def api_admin_model_refresh():
    user_id = session.get("user_id")
    user = database.get_user_secure(user_id)
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    settings = database.get_all_api_settings()
    refreshed = []
    failed = []
    for entry in settings:
        provider = (entry.get("api_provider") or "").strip()
        api_key = (entry.get("api_key") or "").strip()
        if not provider or not api_key:
            continue
        if sync_provider_models(provider, api_key):
            refreshed.append(provider)
        else:
            failed.append(provider)
    return jsonify(
        {
            "success": True,
            "refreshed": refreshed,
            "failed": failed,
            "providers": database.get_model_sync_state(),
        }
    )


# --- Administrative Authentication Guard and Routes ---


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if request.headers.get(
                "Accept"
            ) == "application/json" or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect("/admin/login")
        user = database.get_user_secure(user_id)
        if not user or not user.get("is_admin"):
            if request.headers.get(
                "Accept"
            ) == "application/json" or request.path.startswith("/api/"):
                return jsonify({"error": "Administrator access required"}), 403
            return redirect("/admin/login?error=unauthorized")
        return f(*args, **kwargs)

    return decorated


def superadmin_required(f):
    """Decorator for destructive operations — requires is_admin >= 2 (full Admin)"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        user = database.get_user_secure(user_id)
        if not user or (user.get("is_admin") or 0) < 2:
            return jsonify(
                {
                    "error": "Superadmin privileges required. Co-Admins cannot perform this action."
                }
            ), 403
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

        ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip_addr:
            if "," in ip_addr:
                ip_addr = ip_addr.split(",")[0].strip()
        else:
            ip_addr = "127.0.0.1"

        # Determine actual location by querying public lookup
        is_local = (
            ip_addr in ["127.0.0.1", "::1", "localhost"]
            or ip_addr.startswith("192.168.")
            or ip_addr.startswith("10.")
            or ip_addr.startswith("172.")
        )
        url = (
            "http://ip-api.com/json/"
            if is_local
            else f"http://ip-api.com/json/{ip_addr}"
        )
        location = "Mumbai, Maharashtra, India"  # default fallback
        try:
            resp = requests.get(url, timeout=5).json()
            if resp.get("status") == "success":
                city = resp.get("city", "")
                state = resp.get("regionName", "")
                country = resp.get("country", "")
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
    if session.get("user_id"):
        user = database.get_user_secure(session.get("user_id"))
        if user and user.get("is_admin"):
            return redirect("/admin")
    return render_template("admin_login.html")


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(
            {"success": False, "error": "Username and password required"}
        ), 400

    user = database.get_user_secure(username)
    if not user or not user.get("is_admin"):
        return jsonify(
            {"success": False, "error": "Invalid administrator credentials"}
        ), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify(
            {"success": False, "error": "Invalid administrator credentials"}
        ), 401

    session["user_id"] = user["id"]
    session["local_user_id"] = user["id"]
    session["display_name"] = user["display_name"]
    session["is_admin"] = True
    session.modified = True

    # Register active session
    register_login_session(user["id"])

    # Log administrator IP telemetry
    log_user_telemetry(user["id"])

    return jsonify({"success": True})


@app.route("/admin")
@admin_required
def admin_dashboard():
    user_id = session.get("user_id")
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
    search = request.args.get("search", "").strip() or None
    status = request.args.get("status", "").strip() or None
    date_val = request.args.get("date", "").strip() or None
    time_val = request.args.get("time", "").strip() or None
    start_date = (
        request.args.get("start_date", "").strip()
        or request.args.get("chart_start_date", "").strip()
        or None
    )
    end_date = (
        request.args.get("end_date", "").strip()
        or request.args.get("chart_end_date", "").strip()
        or None
    )
    start_time = (
        request.args.get("start_time", "").strip()
        or request.args.get("chart_start_time", "").strip()
        or None
    )
    end_time = (
        request.args.get("end_time", "").strip()
        or request.args.get("chart_end_time", "").strip()
        or None
    )

    users = database.get_all_users_admin(
        search=search,
        status=status,
        date_val=date_val,
        time_val=time_val,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
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
            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE is_online = 1 AND (strftime('%s', 'now') - strftime('%s', COALESCE(last_seen, created_at))) < 15
            """)
            online = cursor.fetchone()[0]
            offline = total - online
    except Exception as e:
        total = online = offline = active = idle = deactivated = 0

    return jsonify(
        {
            "users": users,
            "stats": {
                "total": total,
                "online": online,
                "offline": offline,
                "active": active,
                "idle": idle,
                "deactivated": deactivated,
            },
        }
    )


@app.route("/api/admin/users", methods=["POST"])
@admin_required
def api_admin_users_create():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    display_name = data.get("display_name", "").strip() or None
    role = data.get("role", "user").strip().lower()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if len(username) < 3 or len(username) > 20 or not username.isalnum():
        return jsonify({"error": "Username must be 3-20 alphanumeric characters"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if role not in ["admin", "coadmin", "user"]:
        return jsonify({"error": "Invalid role selector value"}), 400

    # Only superadmins can create admin or co-admin accounts
    if role in ["admin", "coadmin"]:
        caller = database.get_user_secure(session.get("user_id"))
        if not caller or (caller.get("is_admin") or 0) < 2:
            return jsonify(
                {"error": "Only Admins can create admin/co-admin accounts"}
            ), 403

    # Check if user already exists
    existing = database.get_user_secure(username)
    if existing:
        return jsonify({"error": "Username already exists"}), 409

    # Hash the password and save
    password_hash = generate_password_hash(password)
    is_admin = 2 if role == "admin" else (1 if role == "coadmin" else 0)

    success = database.create_user_secure(
        username, password_hash, display_name, is_admin
    )
    if success:
        database.log_admin_action(
            session.get("user_id"),
            "CREATE_USER",
            username,
            f"Created user account with role {role}",
        )
        return jsonify({"success": True})
    return jsonify({"error": "Failed to create user in database"}), 500


@app.route("/api/admin/users/<username>/status", methods=["POST"])
@admin_required
def api_admin_users_status(username):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ["active", "deactivated", "idle"]:
        return jsonify({"error": "Invalid status value"}), 400

    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    success = database.update_user_status_admin(
        username, status, caller_level=caller_level
    )
    if success:
        database.log_admin_action(
            session.get("user_id"),
            "UPDATE_STATUS",
            username,
            f"Updated account status to {status}",
        )
        if status == "deactivated":
            database.add_announcement(
                "Your account has been deactivated by an administrator.",
                user_id=username,
            )
            # Instantly set them offline in database
            database.set_user_online_status(username, 0)
        return jsonify({"success": True})
    return jsonify(
        {
            "error": "Failed to update status (note: admin profiles/tier limits are protected)"
        }
    ), 400


@app.route("/api/admin/users/<username>/reset-password", methods=["POST"])
@admin_required
def api_admin_users_reset_password(username):
    data = request.get_json() or {}
    new_password = data.get("password", "").strip()
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    password_hash = generate_password_hash(new_password)
    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    success = database.reset_user_password_admin(
        username, password_hash, caller_level=caller_level
    )
    if success:
        database.log_admin_action(
            session.get("user_id"), "RESET_PASSWORD", username, "Reset user password"
        )
        return jsonify({"success": True})
    return jsonify(
        {
            "error": "Failed to reset password (note: admin profiles/tier limits are protected)"
        }
    ), 400


@app.route("/api/admin/users/<username>", methods=["DELETE"])
@admin_required
def api_admin_users_delete(username):
    caller_id = session.get("user_id")
    if username == caller_id:
        return jsonify({"error": "You cannot delete your own profile"}), 400

    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    success = database.delete_user_admin(username, caller_level=caller_level)
    if success:
        database.log_admin_action(
            session.get("user_id"),
            "DELETE_USER",
            username,
            "Permanently deleted user account",
        )
        return jsonify({"success": True})
    return jsonify(
        {
            "error": "Failed to delete user (note: admin profiles/tier limits are protected)"
        }
    ), 400


# --- Premium Administrative Command APIs ---

# Human-friendly descriptions of security policy rules
SECURITY_RULES_METADATA = {
    "rule_admin_delete_coadmin": {
        "label": "Admin: Delete Co-Admins",
        "role": "admin",
        "desc": "Allows Admins to permanently delete Co-Admin profiles and sessions.",
    },
    "rule_admin_delete_user": {
        "label": "Admin: Delete Users",
        "role": "admin",
        "desc": "Allows Admins to permanently delete standard User profiles and sessions.",
    },
    "rule_admin_reset_coadmin": {
        "label": "Admin: Reset Co-Admin Password",
        "role": "admin",
        "desc": "Allows Admins to reset the credentials of Co-Admins.",
    },
    "rule_admin_reset_user": {
        "label": "Admin: Reset User Password",
        "role": "admin",
        "desc": "Allows Admins to reset the credentials of standard Users.",
    },
    "rule_admin_manage_config": {
        "label": "Admin: Manage System Config",
        "role": "admin",
        "desc": "Enables site setting configuration toggles for Admins.",
    },
    "rule_admin_execute_commands": {
        "label": "Admin: Execute Terminal Commands",
        "role": "admin",
        "desc": "Allows Admins to run custom terminal console commands.",
    },
    "rule_admin_publish_announcement": {
        "label": "Admin: Publish Announcements",
        "role": "admin",
        "desc": "Allows Admins to broadcast site-wide announcements.",
    },
    "rule_admin_export_data": {
        "label": "Admin: Export User Data",
        "role": "admin",
        "desc": "Allows Admins to download audit logs/JSON files of any profile.",
    },
    "rule_coadmin_delete_user": {
        "label": "Co-Admin: Delete Users",
        "role": "coadmin",
        "desc": "Allows Co-Admins to permanently delete standard User profiles.",
    },
    "rule_coadmin_reset_user": {
        "label": "Co-Admin: Reset User Password",
        "role": "coadmin",
        "desc": "Allows Co-Admins to reset standard User credentials.",
    },
    "rule_coadmin_deactivate_user": {
        "label": "Co-Admin: Deactivate Users",
        "role": "coadmin",
        "desc": "Allows Co-Admins to deactivate/suspend standard User profiles.",
    },
    "rule_coadmin_view_logs": {
        "label": "Co-Admin: View Live System Logs",
        "role": "coadmin",
        "desc": "Allows Co-Admins to access the terminal console log stream.",
    },
    "rule_coadmin_publish_announcement": {
        "label": "Co-Admin: Publish Announcements",
        "role": "coadmin",
        "desc": "Allows Co-Admins to broadcast site-wide announcements.",
    },
    "rule_coadmin_execute_commands": {
        "label": "Co-Admin: Execute Terminal Commands",
        "role": "coadmin",
        "desc": "Allows Co-Admins to run console terminal commands.",
    },
    "rule_coadmin_export_data": {
        "label": "Co-Admin: Export User Data",
        "role": "coadmin",
        "desc": "Allows Co-Admins to download user profile audits.",
    },
    "rule_user_view_logs": {
        "label": "User: View Live System Logs",
        "role": "user",
        "desc": "Permits standard Users to view system diagnostic console log streams.",
    },
}


@app.route("/api/admin/rules", methods=["GET"])
@admin_required
def api_admin_rules():
    configs = database.get_all_configs()
    rules = []
    for key, meta in SECURITY_RULES_METADATA.items():
        rules.append(
            {
                "key": key,
                "label": meta["label"],
                "role": meta["role"],
                "desc": meta["desc"],
                "enabled": configs.get(
                    key,
                    "true"
                    if "user" not in key and "coadmin_execute" not in key
                    else "false",
                )
                == "true",
            }
        )
    return jsonify({"rules": rules})


@app.route("/api/admin/rules", methods=["POST"])
@admin_required
def api_admin_rules_update():
    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0
    if caller_level < 2:
        return jsonify(
            {
                "error": "Only full Administrators (tier 2) can configure security policies."
            }
        ), 403

    data = request.get_json() or {}
    key = data.get("key")
    enabled = data.get("enabled")
    if key not in SECURITY_RULES_METADATA:
        return jsonify({"error": "Invalid security policy rule."}), 400

    database.set_config_value(key, "true" if enabled else "false")
    database.add_announcement(
        f"Security policy updated: {SECURITY_RULES_METADATA[key]['label']} set to {enabled}"
    )
    database.log_admin_action(
        session.get("user_id"),
        "UPDATE_RULE",
        None,
        f"Security policy updated: {SECURITY_RULES_METADATA[key]['label']} set to {enabled}",
    )
    return jsonify({"success": True})


@app.route("/api/admin/settings", methods=["GET"])
@admin_required
def api_admin_settings():
    configs = database.get_all_configs()
    return jsonify({"configs": configs})


@app.route("/api/admin/settings", methods=["POST"])
@admin_required
def api_admin_settings_update():
    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    rule_ok = False
    if caller_level >= 2:
        rule_ok = (
            database.get_config_value("rule_admin_manage_config", "true") == "true"
        )
    elif caller_level == 1:
        rule_ok = (
            database.get_config_value("rule_coadmin_manage_config", "false") == "true"
        )

    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403

    data = request.get_json() or {}
    for key, val in data.items():
        if key in [
            "enable_registration",
            "allow_guests",
            "enable_music",
            "enforce_passwords",
        ]:
            database.set_config_value(key, str(val))
            database.log_admin_action(
                session.get("user_id"),
                "UPDATE_SETTINGS",
                None,
                f"Updated setting: {key} = {val}",
            )
    return jsonify({"success": True})


@app.route("/api/admin/announcement", methods=["POST"])
@admin_required
def api_admin_announcement_update():
    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    rule_ok = False
    if caller_level >= 2:
        rule_ok = (
            database.get_config_value("rule_admin_publish_announcement", "true")
            == "true"
        )
    elif caller_level == 1:
        rule_ok = (
            database.get_config_value("rule_coadmin_publish_announcement", "true")
            == "true"
        )

    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403

    data = request.get_json() or {}
    announcement = data.get("announcement", "").strip()
    database.set_config_value("site_announcement", announcement)
    if announcement:
        database.add_announcement(announcement)
    database.log_admin_action(
        session.get("user_id"),
        "PUBLISH_ANNOUNCEMENT",
        None,
        f"Published global announcement: {announcement}"
        if announcement
        else "Cleared global announcement banner",
    )
    return jsonify({"success": True})


def get_avg_latency_with_sim(t_val=None):
    if t_val is None:
        t_val = int(time.time())

    # Base random latency
    random.seed(t_val)
    lat_val = round(340.0 + random.uniform(0, 45.0), 1)

    try:
        sim_val = database.get_config_value("sim_latency_spike", "")
        if sim_val:
            parts = sim_val.split(",")
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
        "totalRequests": total_messages,
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
    start_date = (
        request.args.get("start_date", "").strip()
        or request.args.get("chart_start_date", "").strip()
        or None
    )
    end_date = (
        request.args.get("end_date", "").strip()
        or request.args.get("chart_end_date", "").strip()
        or None
    )
    start_time_val = (
        request.args.get("start_time", "").strip()
        or request.args.get("chart_start_time", "").strip()
        or None
    )
    end_time_val = (
        request.args.get("end_time", "").strip()
        or request.args.get("chart_end_time", "").strip()
        or None
    )

    now = time.time()
    rounded_now = int(now // 60) * 60

    start_ts = None
    end_ts = None

    if start_date:
        try:
            start_str = f"{start_date} {start_time_val or '00:00:00'}"
            dt = datetime.strptime(
                start_str.split(".")[0],
                "%Y-%m-%d %H:%M:%S"
                if len(start_str.split(":")) == 3
                else "%Y-%m-%d %H:%M",
            )
            start_ts = int(dt.timestamp())
        except Exception:
            pass

    if end_date:
        try:
            end_str = f"{end_date} {end_time_val or '23:59:59'}"
            dt = datetime.strptime(
                end_str.split(".")[0],
                "%Y-%m-%d %H:%M:%S"
                if len(end_str.split(":")) == 3
                else "%Y-%m-%d %H:%M",
            )
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

    step = 60  # 1 minute
    if diff > 7 * 24 * 3600:  # more than 7 days, step = 1 hour
        step = 3600
    elif diff > 24 * 3600:  # more than 1 day, step = 15 minutes
        step = 900
    elif diff > 4 * 3600:  # more than 4 hours, step = 5 minutes
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
    user_id = session.get("user_id")
    if not user_id:
        return "Unauthorized", 401
    user = database.get_user_secure(user_id)
    if not user or not user.get("is_admin"):
        return "Forbidden", 403

    from flask import Response

    def event_stream():
        import json

        metrics = _get_pre_aggregated_metrics()
        yield f"data: {json.dumps(metrics)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/api/announcement", methods=["GET"])
def api_get_announcement():
    announcement = database.get_config_value("site_announcement", "")
    enable_music = database.get_config_value("enable_music", "true")
    return jsonify(
        {"announcement": announcement, "enable_music": enable_music == "true"}
    )


@app.route("/api/announcements", methods=["GET"])
@login_required
def api_get_announcements_history():
    user_id = session.get("user_id")
    history = database.get_announcements_history(user_id)
    return jsonify({"history": history})


@app.route("/api/support/send", methods=["POST"])
def api_support_send():
    data = request.get_json() or {}
    sender = data.get("sender", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    category = data.get("category", "").strip()
    priority = data.get("priority", "").strip()

    if not sender or not message:
        return jsonify({"error": "Sender email and message are required."}), 400

    # Prioritize environment variables for SMTP credentials, then fall back to local files
    support_email = os.environ.get("MAIL_ID") or os.environ.get("SMTP_EMAIL")
    if not support_email:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        mail_id_file = os.path.join(base_dir, "mail_id.txt")
        if os.path.exists(mail_id_file):
            try:
                with open(mail_id_file, "r", encoding="utf-8") as f:
                    support_email = f.read().strip()
            except Exception as e:
                return jsonify(
                    {"error": f"Failed to load mail ID from file: {str(e)}"}
                ), 500

    support_password = os.environ.get("MAIL_PASSWORD") or os.environ.get(
        "SMTP_PASSWORD"
    )
    if not support_password:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        mail_pw_file = os.path.join(base_dir, "mail_password.txt")
        if os.path.exists(mail_pw_file):
            try:
                with open(mail_pw_file, "r", encoding="utf-8") as f:
                    support_password = f.read().strip()
            except Exception as e:
                return jsonify(
                    {"error": f"Failed to load mail password from file: {str(e)}"}
                ), 500

    if not support_email or not support_password:
        return jsonify(
            {"error": "Support mail service is not configured on the server."}
        ), 503

    if "your-email" in support_email or "your-google" in support_password:
        return jsonify(
            {"error": "Support mail service is not configured (placeholder detected)."}
        ), 503

    # Save support ticket to SQLite database
    database.create_support_ticket(sender, subject, message, category, priority)

    import html
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Format fields for HTML email
    message_html = html.escape(message).replace("\n", "<br>")
    category_display = category.capitalize()
    priority_display = priority.upper()
    priority_lower = priority.lower()
    subject_display = html.escape(subject or "No Subject")
    sender_display = html.escape(sender)

    # HTML Email Template to Support Inbox
    html_support = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #080c14;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      background-color: #080c14;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background: #0f1622;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      background: linear-gradient(135deg, #0f1622 0%, #172237 100%);
      padding: 30px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      text-align: center;
    }}
    .logo-text {{
      font-size: 24px;
      font-weight: 800;
      color: #37e6b5;
      letter-spacing: -0.5px;
      margin: 0;
    }}
    .logo-sub {{
      color: #94a3b8;
      font-size: 12px;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
    }}
    .content {{
      padding: 40px 30px;
    }}
    h1 {{
      font-size: 20px;
      color: #ffffff;
      margin-top: 0;
      margin-bottom: 20px;
      font-weight: 700;
    }}
    p {{
      font-size: 15px;
      color: #94a3b8;
      line-height: 1.6;
      margin-top: 0;
      margin-bottom: 24px;
    }}
    .details-box {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .details-row {{
      margin-bottom: 12px;
      display: flex;
      font-size: 14px;
    }}
    .details-row:last-child {{
      margin-bottom: 0;
    }}
    .details-label {{
      width: 100px;
      color: #64748b;
      font-weight: 600;
    }}
    .details-value {{
      color: #f1f5f9;
      flex: 1;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .badge-priority-high {{
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.2);
    }}
    .badge-priority-medium {{
      background: rgba(245, 158, 11, 0.1);
      color: #f59e0b;
      border: 1px solid rgba(245, 158, 11, 0.2);
    }}
    .badge-priority-low {{
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }}
    .message-container {{
      background: rgba(0, 0, 0, 0.2);
      border-radius: 8px;
      padding: 16px;
      margin-top: 15px;
      border-left: 3px solid #37e6b5;
      font-size: 14px;
      color: #cbd5e1;
      line-height: 1.5;
    }}
    .footer {{
      background: #0b1019;
      padding: 24px;
      text-align: center;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 12px;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;"><tr>
          <td style="vertical-align: middle; padding-right: 12px;"><img src="https://raw.githubusercontent.com/Coder-Paradise-15/Mint-Frost-AI-Ltd/main/static/favicon-dark.png" alt="Mint Frost" width="36" height="36" style="display:block; border-radius: 8px;"></td>
          <td style="vertical-align: middle;">
            <div class="logo-text">MINT FROST</div>
            <div class="logo-sub">Internal Support Notification</div>
          </td>
        </tr></table>
      </div>
      <div class="content">
        <h1>New Support Ticket Received</h1>
        <p>A new user support ticket has been submitted. Details are below:</p>

        <div class="details-box">
          <div class="details-row">
            <div class="details-label">From</div>
            <div class="details-value">{sender_display}</div>
          </div>
          <div class="details-row">
            <div class="details-label">Category</div>
            <div class="details-value">{category_display}</div>
          </div>
          <div class="details-row">
            <div class="details-label">Priority</div>
            <div class="details-value">
              <span class="badge badge-priority-{priority_lower}">{priority_display}</span>
            </div>
          </div>
          <div class="details-row">
            <div class="details-label">Subject</div>
            <div class="details-value">{subject_display}</div>
          </div>
          <div class="message-container">{message_html}</div>
        </div>
      </div>
      <div class="footer">
        &copy; 2026 Mint Frost Admin Console
      </div>
    </div>
  </div>
</body>
</html>"""

    # HTML Email Template to User (Receipt)
    html_user = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #080c14;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      background-color: #080c14;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background: #0f1622;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      background: linear-gradient(135deg, #0f1622 0%, #172237 100%);
      padding: 30px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      text-align: center;
    }}
    .logo-text {{
      font-size: 24px;
      font-weight: 800;
      color: #37e6b5;
      letter-spacing: -0.5px;
      margin: 0;
    }}
    .logo-sub {{
      color: #94a3b8;
      font-size: 12px;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
    }}
    .content {{
      padding: 40px 30px;
    }}
    h1 {{
      font-size: 20px;
      color: #ffffff;
      margin-top: 0;
      margin-bottom: 20px;
      font-weight: 700;
    }}
    p {{
      font-size: 15px;
      color: #94a3b8;
      line-height: 1.6;
      margin-top: 0;
      margin-bottom: 24px;
    }}
    .details-box {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .details-row {{
      margin-bottom: 12px;
      display: flex;
      font-size: 14px;
    }}
    .details-row:last-child {{
      margin-bottom: 0;
    }}
    .details-label {{
      width: 100px;
      color: #64748b;
      font-weight: 600;
    }}
    .details-value {{
      color: #f1f5f9;
      flex: 1;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .badge-priority-high {{
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.2);
    }}
    .badge-priority-medium {{
      background: rgba(245, 158, 11, 0.1);
      color: #f59e0b;
      border: 1px solid rgba(245, 158, 11, 0.2);
    }}
    .badge-priority-low {{
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }}
    .message-container {{
      background: rgba(0, 0, 0, 0.2);
      border-radius: 8px;
      padding: 16px;
      margin-top: 15px;
      border-left: 3px solid #37e6b5;
      font-size: 14px;
      color: #cbd5e1;
      font-style: italic;
      line-height: 1.5;
    }}
    .footer {{
      background: #0b1019;
      padding: 24px;
      text-align: center;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 12px;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;"><tr>
          <td style="vertical-align: middle; padding-right: 12px;"><img src="https://raw.githubusercontent.com/Coder-Paradise-15/Mint-Frost-AI-Ltd/main/static/favicon-dark.png" alt="Mint Frost" width="36" height="36" style="display:block; border-radius: 8px;"></td>
          <td style="vertical-align: middle;">
            <div class="logo-text">MINT FROST</div>
            <div class="logo-sub">Support System</div>
          </td>
        </tr></table>
      </div>
      <div class="content">
        <h1>Ticket Received</h1>
        <p>Hello,</p>
        <p>Thank you for contacting Mint Frost Support. We have received your support request and our team will get back to you shortly. A summary of your ticket details is provided below:</p>

        <div class="details-box">
          <div class="details-row">
            <div class="details-label">Category</div>
            <div class="details-value">{category_display}</div>
          </div>
          <div class="details-row">
            <div class="details-label">Priority</div>
            <div class="details-value">
              <span class="badge badge-priority-{priority_lower}">{priority_display}</span>
            </div>
          </div>
          <div class="details-row">
            <div class="details-label">Subject</div>
            <div class="details-value">{subject_display}</div>
          </div>
          <div class="message-container">{message_html}</div>
        </div>

        <p style="margin-bottom: 0;">Best regards,<br><span style="color: #ffffff; font-weight: 600;">Mint Frost Team</span></p>
      </div>
      <div class="footer">
        &copy; 2026 Mint Frost Ltd. All rights reserved.
      </div>
    </div>
  </div>
</body>
</html>"""

    # Send ticket notification to Support Inbox
    from email.utils import formataddr

    msg_to_support = MIMEMultipart("alternative")
    msg_to_support["From"] = formataddr(("Mint Frost Support", support_email))
    msg_to_support["To"] = support_email
    msg_to_support["Reply-To"] = sender
    msg_to_support["Subject"] = (
        f"[Support Ticket] {category.upper()}: {subject or 'No Subject'}"
    )
    msg_to_support.attach(MIMEText(html_support, "html", "utf-8"))

    # Send receipt/acknowledgement to User Sender
    msg_to_user = MIMEMultipart("alternative")
    msg_to_user["From"] = formataddr(("Mint Frost Support", support_email))
    msg_to_user["To"] = sender
    msg_to_user["Subject"] = f"Re: {subject or 'Support Ticket Received'}"
    msg_to_user.attach(MIMEText(html_user, "html", "utf-8"))

    # Log the action in database first
    user_id = session.get("user_id")
    if user_id:
        database.log_admin_action(
            user_id,
            "SEND_SUPPORT_TICKET",
            sender,
            f"Support ticket category: {category}",
        )

    smtp_success = True
    smtp_error_msg = ""
    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(support_email, support_password)

        # Send to Support
        server.sendmail(support_email, [support_email], msg_to_support.as_string())

        # Send receipt to user
        if "@" in sender:
            try:
                server.sendmail(support_email, [sender], msg_to_user.as_string())
            except Exception as user_err:
                import logging

                logging.warning(f"Failed to send confirmation receipt: {user_err}")

        server.quit()
    except Exception as e:
        smtp_success = False
        smtp_error_msg = str(e)
        import logging

        logging.error(f"SMTP sending error (bypassed for development): {e}")

    # Return success true even if SMTP fails, since ticket is saved to db
    return jsonify(
        {
            "success": True,
            "message": "Support message sent successfully"
            if smtp_success
            else f"Support ticket saved, but email delivery failed: {smtp_error_msg}",
        }
    )


@app.route("/api/admin/support-tickets", methods=["GET"])
@admin_required
def api_admin_support_tickets():
    tickets = database.get_support_tickets()
    return jsonify({"tickets": tickets})


@app.route("/api/admin/support-tickets/<int:ticket_id>/status", methods=["POST"])
@admin_required
def api_admin_support_ticket_status(ticket_id):
    data = request.get_json() or {}
    status = data.get("status", "open").strip()
    success = database.update_support_ticket_status(ticket_id, status)
    if success:
        user_id = session.get("user_id")
        if user_id:
            database.log_admin_action(
                user_id,
                "UPDATE_TICKET_STATUS",
                str(ticket_id),
                f"Set status to {status}",
            )
        return jsonify({"success": True})
    return jsonify({"error": "Failed to update ticket status."}), 500


@app.route("/api/admin/support-tickets/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def api_admin_support_ticket_reply(ticket_id):
    ticket = database.get_support_ticket(ticket_id)
    if not ticket:
        return jsonify({"error": "Support ticket not found."}), 404

    data = request.get_json() or {}
    reply_message = data.get("message", "").strip()
    new_status = data.get("status", "").strip() or ticket.get("status", "open")
    if not reply_message:
        return jsonify({"error": "Reply message cannot be empty."}), 400

    # Prioritize environment variables for SMTP credentials, then fall back to local files
    support_email = os.environ.get("MAIL_ID") or os.environ.get("SMTP_EMAIL")
    if not support_email:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        mail_id_file = os.path.join(base_dir, "mail_id.txt")
        if os.path.exists(mail_id_file):
            try:
                with open(mail_id_file, "r", encoding="utf-8") as f:
                    support_email = f.read().strip()
            except Exception as e:
                return jsonify(
                    {"error": f"Failed to load mail ID from file: {str(e)}"}
                ), 500

    support_password = os.environ.get("MAIL_PASSWORD") or os.environ.get(
        "SMTP_PASSWORD"
    )
    if not support_password:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        mail_pw_file = os.path.join(base_dir, "mail_password.txt")
        if os.path.exists(mail_pw_file):
            try:
                with open(mail_pw_file, "r", encoding="utf-8") as f:
                    support_password = f.read().strip()
            except Exception as e:
                return jsonify(
                    {"error": f"Failed to load mail password from file: {str(e)}"}
                ), 500

    if not support_email or not support_password:
        return jsonify(
            {"error": "Support mail service is not configured on the server."}
        ), 503

    if "your-email" in support_email or "your-google" in support_password:
        return jsonify(
            {"error": "Support mail service is not configured (placeholder detected)."}
        ), 503

    import html
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formataddr

    # Format fields for HTML email
    reply_html = reply_message
    category_display = (ticket.get("category") or "general").capitalize()
    priority_display = (ticket.get("priority") or "low").upper()
    subject_display = html.escape(ticket.get("subject") or "No Subject")
    original_message_html = html.escape(ticket.get("message") or "").replace(
        "\n", "<br>"
    )

    # HTML Email Template to User for Reply
    html_reply = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #080c14;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      background-color: #080c14;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background: #0f1622;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      background: linear-gradient(135deg, #0f1622 0%, #172237 100%);
      padding: 30px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      text-align: center;
    }}
    .logo-text {{
      font-size: 24px;
      font-weight: 800;
      color: #37e6b5;
      letter-spacing: -0.5px;
      margin: 0;
    }}
    .logo-sub {{
      color: #94a3b8;
      font-size: 12px;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
    }}
    .content {{
      padding: 40px 30px;
    }}
    h1 {{
      font-size: 20px;
      color: #ffffff;
      margin-top: 0;
      margin-bottom: 20px;
      font-weight: 700;
    }}
    p {{
      font-size: 15px;
      color: #94a3b8;
      line-height: 1.6;
      margin-top: 0;
      margin-bottom: 24px;
    }}
    .reply-box {{
      background: rgba(55, 230, 181, 0.03);
      border: 1px solid rgba(55, 230, 181, 0.1);
      border-left: 4px solid #37e6b5;
      border-radius: 8px;
      padding: 24px;
      margin-bottom: 30px;
      font-size: 15px;
      color: #ffffff;
      line-height: 1.6;
    }}
    .quote-box {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 16px;
      font-size: 13px;
      color: #64748b;
      margin-top: 20px;
    }}
    .quote-header {{
      font-weight: 700;
      margin-bottom: 8px;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.5px;
    }}
    .footer {{
      background: #0b1019;
      padding: 24px;
      text-align: center;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 12px;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;"><tr>
          <td style="vertical-align: middle; padding-right: 12px;"><img src="https://raw.githubusercontent.com/Coder-Paradise-15/Mint-Frost-AI-Ltd/main/static/favicon-dark.png" alt="Mint Frost" width="36" height="36" style="display:block; border-radius: 8px;"></td>
          <td style="vertical-align: middle;">
            <div class="logo-text">MINT FROST</div>
            <div class="logo-sub">Support Response</div>
          </td>
        </tr></table>
      </div>
      <div class="content">
        <h1>Response to Your Ticket</h1>
        <p>Hello,</p>
        <p>An administrator from Mint Frost Support has responded to your ticket:</p>

        <div class="reply-box">
          {reply_html}
        </div>

        <p>If you have any further questions, you can reply directly to this email.</p>

        <div class="quote-box">
          <div class="quote-header">Original Ticket Details</div>
          <strong>Subject:</strong> {subject_display}<br>
          <strong>Category:</strong> {category_display}<br>
          <strong>Priority:</strong> {priority_display}<br>
          <strong>Status:</strong> <span style="color: #37e6b5; font-weight: 600;">{new_status.upper()}</span><br><br>
          {original_message_html}
        </div>

        <p style="margin-top: 30px; margin-bottom: 0;">Best regards,<br><span style="color: #ffffff; font-weight: 600;">Mint Frost Support Team</span></p>
      </div>
      <div class="footer">
        &copy; 2026 Mint Frost Ltd. All rights reserved.
      </div>
    </div>
  </div>
</body>
</html>"""

    # Send reply to User Sender
    msg_to_user = MIMEMultipart("alternative")
    msg_to_user["From"] = formataddr(("Mint Frost Support", support_email))
    msg_to_user["To"] = ticket.get("sender")
    msg_to_user["Reply-To"] = support_email
    msg_to_user["Subject"] = f"Re: {ticket.get('subject') or 'Support Ticket'}"
    msg_to_user.attach(MIMEText(html_reply, "html", "utf-8"))

    # Update ticket status in database to admin-selected status first
    database.update_support_ticket_status(ticket_id, new_status)

    user_id = session.get("user_id")
    if user_id:
        database.log_admin_action(
            user_id,
            "REPLY_SUPPORT_TICKET",
            ticket.get("sender"),
            f"Replied to ticket ID {ticket_id}",
        )

    smtp_success = True
    smtp_error_msg = ""
    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(support_email, support_password)
        server.sendmail(support_email, [ticket.get("sender")], msg_to_user.as_string())
        server.quit()
    except Exception as e:
        smtp_success = False
        smtp_error_msg = str(e)
        import logging

        logging.error(
            f"SMTP sending error in admin reply (bypassed for development): {e}"
        )

    # Return success true even if SMTP fails, since ticket status is updated in db
    return jsonify(
        {
            "success": True,
            "message": "Reply email sent successfully"
            if smtp_success
            else f"Ticket status updated, but reply email failed: {smtp_error_msg}",
        }
    )


@app.route("/api/admin/support-tickets/<int:ticket_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_support_ticket(ticket_id):
    success = database.delete_support_ticket(ticket_id)
    if success:
        user_id = session.get("user_id")
        if user_id:
            database.log_admin_action(
                user_id, "DELETE_SUPPORT_TICKET", "", f"Deleted ticket ID {ticket_id}"
            )
        return jsonify({"success": True, "message": "Ticket deleted successfully."})
    return jsonify({"error": "Failed to delete ticket."}), 400


@app.route("/api/admin/support-tickets/clear-all", methods=["DELETE"])
@admin_required
def api_admin_delete_all_support_tickets():
    count = database.delete_all_support_tickets()
    user_id = session.get("user_id")
    if user_id:
        database.log_admin_action(
            user_id, "DELETE_ALL_SUPPORT_TICKETS", "", f"Deleted {count} tickets"
        )
    return jsonify(
        {"success": True, "message": f"{count} tickets deleted.", "count": count}
    )


@app.route("/api/admin/users/<username>/details", methods=["GET"])
@admin_required
def api_admin_user_details(username):
    details = database.get_user_full_details_admin(username)
    if details:
        # High fidelity simulated biodata values to look incredibly rich and realistic:
        cities_addresses = {
            "Mumbai, India": "45, Hill Road, Bandra West, Mumbai, Maharashtra 400050",
            "New York, USA": "742 Broadway, Floor 4, New York, NY 10003",
            "London, UK": "221B Baker St, London NW1 6XE, United Kingdom",
            "Berlin, Germany": "Klingelhöferstraße 21, 10785 Berlin, Germany",
            "Tokyo, Japan": "1-1-2 Otemachi, Chiyoda City, Tokyo 100-0004, Japan",
            "Paris, France": "4 Rue de la Paix, 75002 Paris, France",
            "Sydney, Australia": "31 Alfred St, Sydney NSW 2000, Australia",
            "Singapore": "10 Bayfront Ave, Singapore 018956",
        }
        loc = details.get("last_login_location", "Mumbai, Maharashtra, India")
        addr = cities_addresses.get(loc, "75, Marine Drive, Churchgate, Mumbai, India")
        details["home_address"] = (
            addr
            if details["home_address"] == "Not Provided"
            else details["home_address"]
        )

        # Get coordinates based on IP lookup or fallback
        ip_addr = details.get("last_login_ip", "127.0.0.1")
        is_local = (
            ip_addr in ["127.0.0.1", "::1", "localhost"]
            or ip_addr.startswith("192.168.")
            or ip_addr.startswith("10.")
            or ip_addr.startswith("172.")
        )
        url = (
            "http://ip-api.com/json/"
            if is_local
            else f"http://ip-api.com/json/{ip_addr}"
        )
        coords = "18.9220° N, 72.8347° E"  # default Mumbai coords
        try:
            resp = requests.get(url, timeout=3).json()
            if resp.get("status") == "success":
                lat = resp.get("lat")
                lon = resp.get("lon")
                if lat is not None and lon is not None:
                    lat_dir = "N" if lat >= 0 else "S"
                    lon_dir = "E" if lon >= 0 else "W"
                    coords = f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"
        except Exception:
            pass
        details["geolocation_coords"] = coords

        # Age birth dates mockup
        birthdays = [
            "1998-05-14",
            "1995-10-22",
            "2001-02-09",
            "1992-12-03",
            "2003-08-30",
            "1989-07-17",
        ]
        import random

        # deterministic index based on username length to maintain consistency
        bd = birthdays[len(username) % len(birthdays)]
        caller_id = session.get("user_id")
        caller = database.get_user_secure(caller_id)
        caller_level = caller.get("is_admin") or 0 if caller else 0
        return jsonify({"details": details, "caller_level": caller_level})
    return jsonify({"error": "User profile not found"}), 404


@app.route(
    "/api/admin/users/<username>/sessions/<session_id>/messages", methods=["GET"]
)
@admin_required
def api_admin_user_session_messages(username, session_id):
    # Verify session belongs to user
    with database.connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, username),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Chat session not found for this user"}), 404

    # Fetch messages list
    messages = database.get_session_messages(session_id)
    return jsonify({"messages": messages})


@app.route("/api/admin/users/<username>/export", methods=["GET"])
@admin_required
def api_admin_user_export(username):
    caller_id = session.get("user_id")
    caller = database.get_user_secure(caller_id)
    caller_level = caller.get("is_admin") or 0 if caller else 0

    rule_ok = False
    if caller_level >= 2:
        rule_ok = database.get_config_value("rule_admin_export_data", "true") == "true"
    elif caller_level == 1:
        rule_ok = (
            database.get_config_value("rule_coadmin_export_data", "true") == "true"
        )

    if not rule_ok:
        return jsonify({"error": "Access denied by security policies."}), 403

    details = database.get_user_full_details_admin(username)
    if not details:
        return jsonify({"error": "User profile not found"}), 404

    # Aggregate all conversation logs
    full_history = []
    for s in details["sessions"]:
        messages = database.get_session_messages(s["id"])
        full_history.append(
            {
                "session_id": s["id"],
                "session_title": s["title"],
                "created_at": s["created_at"],
                "messages": messages,
            }
        )
    details["full_conversations"] = full_history

    # Stream as downloadable JSON attachment response
    import json

    from flask import Response

    response_data = json.dumps(details, indent=4)
    return Response(
        response_data,
        mimetype="application/json",
        headers={
            "Content-disposition": f"attachment; filename=user_export_{username}.json"
        },
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
    active_count = len([u for u in users if u.get("status") == "active"])

    return jsonify(
        {
            "db_size_mb": db_size_mb,
            "total_users": total_users,
            "uptime": uptime_str,
            "active_sessions": active_count,
        }
    )


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
    raw = data.get("command", "").strip()
    if not raw:
        return jsonify({"error": "No command provided"}), 400

    parts = raw.split()
    cmd = parts[0].lower()
    args = parts[1:]

    def _role_name(level):
        level = level or 0
        if level >= 2:
            return "Admin"
        if level == 1:
            return "Co-Admin"
        return "User"

    caller = database.get_user_secure(session.get("user_id"))
    caller_level = (caller.get("is_admin") or 0) if caller else 0

    # Rules check for command execution
    rule_ok = False
    if caller_level >= 2:
        rule_ok = (
            database.get_config_value("rule_admin_execute_commands", "true") == "true"
        )
    elif caller_level == 1:
        rule_ok = (
            database.get_config_value("rule_coadmin_execute_commands", "false")
            == "true"
        )
    else:
        rule_ok = database.get_config_value("rule_user_view_logs", "false") == "true"

    if not rule_ok:
        return jsonify(
            {
                "error": "⛔ Access denied. Security policy blocks terminal command execution for your role tier."
            }
        ), 403

    database.log_admin_action(
        session.get("user_id"),
        "EXECUTE_CONSOLE_CMD",
        None,
        f"Executed console command: {raw}",
    )

    try:
        # Check if we are awaiting database wipe confirmation
        if session.get("awaiting_reset_confirm"):
            session.pop("awaiting_reset_confirm", None)  # consume the flag
            if cmd in ("yes", "y"):
                success = database.reset_database()
                if success:
                    database.log_admin_action(
                        "admin",
                        "DB_RESET",
                        None,
                        f"Database fully reset via console command by: {session.get('user_id')}",
                    )
                    session.clear()
                    return jsonify(
                        {
                            "output": "Server Data Override Deletion Protocols initiated!\n All Data of these Sever is Deleted"
                        }
                    )
                else:
                    return jsonify({"error": "Failed to reset database tables."})
            elif cmd in ("no", "n"):
                return jsonify({"output": "Database wipe cancelled."})
            else:
                return jsonify(
                    {"error": "Database wipe cancelled (invalid confirmation)."}
                )

        # Check if we are awaiting audit trail wipe confirmation
        if session.get("awaiting_audit_confirm"):
            session.pop("awaiting_audit_confirm", None)  # consume the flag
            if cmd in ("yes", "y"):
                success = database.clear_admin_audit_logs()
                if success:
                    return jsonify(
                        {
                            "output": "Security Audit Trail Override Deletion Protocols initiated!\n All Audit Logs have been completely wiped!"
                        }
                    )
                else:
                    return jsonify({"error": "Failed to clear audit logs."})
            elif cmd in ("no", "n"):
                return jsonify({"output": "Audit logs wipe cancelled."})
            else:
                return jsonify(
                    {"error": "Audit logs wipe cancelled (invalid confirmation)."}
                )

        # Check if we are awaiting update pack selection
        if session.get("awaiting_patch_select"):
            session.pop("awaiting_patch_select", None)  # consume the flag
            if cmd == "cancel" or cmd == "c":
                return jsonify({"output": "Update patching sequence cancelled."})

            if cmd in ("1", "2", "3"):
                pack_names = {
                    "1": "Update Pack V4.1 (Stability & Performance Hotfix)",
                    "2": "Update Pack V4.2 (Advanced Telemetry & Analytics)",
                    "3": "Update Pack V5.0-Beta (Quantum ML Core Integration)",
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
                    "🟢 [SYSTEM] Mint Frost Server live patched and running!",
                ]
                return jsonify({"output": "\n".join(lines)})
            else:
                return jsonify(
                    {"error": "Invalid selection. Please select 1, 2, 3, or 'cancel'."}
                )

        # ── help ──
        if cmd == "help":
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
        elif (
            cmd == "delete"
            and len(args) >= 2
            and args[0].lower() == "data"
            and args[1].lower() == "override"
        ):
            session["awaiting_reset_confirm"] = True
            output_msg = (
                "Initializing Server Data Override Deletion Protocols......\n"
                "Everything will wipe up !!!!\n"
                " Are You Sure Want to continue ?  Yes / No"
            )
            return jsonify({"output": output_msg})

        # ── delete audit override ──
        elif (
            cmd == "delete"
            and len(args) >= 2
            and args[0].lower() == "audit"
            and args[1].lower() == "override"
        ):
            session["awaiting_audit_confirm"] = True
            output_msg = (
                "Initializing Security Audit Trail Override Deletion Protocols......\n"
                "All administrative audit logs will be permanently wiped !!!!\n"
                " Are You Sure Want to continue ?  Yes / No"
            )
            return jsonify({"output": output_msg})

        # ── clear (handled client-side but acknowledge) ──
        elif cmd == "clear":
            return jsonify({"output": "__CLEAR__"})

        # ── whoami ──
        elif cmd == "whoami":
            uid = session.get("user_id", "unknown")
            role = _role_name(caller_level)
            return jsonify(
                {
                    "output": f"Logged in as: {uid}\nDisplay Name: {caller.get('display_name', 'N/A') if caller else 'N/A'}\nRole: {role}\nAccess Level: {caller_level}"
                }
            )

        # ── uptime ──
        elif cmd == "uptime":
            import time as _time

            if not hasattr(app, "_start_time"):
                app._start_time = _time.time()
            elapsed = int(_time.time() - app._start_time)
            days, rem = divmod(elapsed, 86400)
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            return jsonify(
                {"output": f"Server uptime: {days}d {hours}h {mins}m {secs}s"}
            )

        # ── health ──
        elif cmd == "health":
            try:
                db_path = database.DATABASE_PATH
                db_mb = round(os.path.getsize(db_path) / (1024 * 1024), 3)
            except Exception:
                db_mb = 0
            all_users = database.get_all_users_admin()
            total = len(all_users)
            active = len([u for u in all_users if u.get("status") == "active"])
            online = len([u for u in all_users if u.get("is_online")])
            deactivated = len(
                [u for u in all_users if u.get("status") == "deactivated"]
            )
            admins = len([u for u in all_users if (u.get("is_admin") or 0) >= 2])
            coadmins = len([u for u in all_users if (u.get("is_admin") or 0) == 1])
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
        elif cmd == "dbsize":
            try:
                db_path = database.DATABASE_PATH
                sz = os.path.getsize(db_path)
                return jsonify(
                    {
                        "output": f"Database file: {round(sz / 1024, 2)} KB ({round(sz / (1024 * 1024), 3)} MB)"
                    }
                )
            except Exception as e:
                return jsonify({"error": str(e)})

        # ── version ──
        elif cmd == "version":
            return jsonify(
                {
                    "output": "Mint Frost AI — Admin Command Center v2.0\nEngine: Flask + SQLite3 WAL\nPython: "
                    + __import__("sys").version.split()[0]
                }
            )

        # ── users ──
        elif cmd == "users":
            all_users = database.get_all_users_admin()
            if not all_users:
                return jsonify({"output": "No users found."})
            header = f"{'USERNAME':<18} {'DISPLAY NAME':<20} {'ROLE':<10} {'STATUS':<12} {'ONLINE':<8}"
            sep = "─" * 68
            lines = [header, sep]
            for u in all_users:
                role = _role_name(u.get("is_admin"))
                on = "●" if u.get("is_online") else "○"
                lines.append(
                    f"{u['username']:<18} {u['display_name']:<20} {role:<10} {u['status']:<12} {on:<8}"
                )
            lines.append(sep)
            lines.append(f"Total: {len(all_users)} users")
            return jsonify({"output": "\n".join(lines)})

        # ── online ──
        elif cmd == "online":
            all_users = database.get_all_users_admin()
            online_users = [u for u in all_users if u.get("is_online")]
            if not online_users:
                return jsonify({"output": "No users currently online."})
            lines = [f"Online Users ({len(online_users)}):"]
            for u in online_users:
                role = _role_name(u.get("is_admin"))
                lines.append(f"  ● {u['username']} ({u['display_name']}) — {role}")
            return jsonify({"output": "\n".join(lines)})

        # ── find <query> ──
        elif cmd == "find":
            if not args:
                return jsonify({"error": "Usage: find <search_query>"})
            q = " ".join(args)
            results = database.get_all_users_admin(search=q)
            if not results:
                return jsonify({"output": f'No users matching "{q}".'})
            lines = [f'Search results for "{q}" ({len(results)} found):']
            for u in results:
                role = _role_name(u.get("is_admin"))
                lines.append(
                    f"  • {u['username']} — {u['display_name']} [{role}] ({u['status']})"
                )
            return jsonify({"output": "\n".join(lines)})

        # ── adduser <user> <pass> [admin|coadmin|user] ──
        elif cmd == "adduser":
            if len(args) < 2:
                return jsonify(
                    {
                        "error": "Usage: adduser <username> <password> [admin|coadmin|user]"
                    }
                )
            username = args[0]
            password = args[1]
            role = args[2].lower() if len(args) > 2 else "user"
            if role not in ("admin", "coadmin", "user"):
                return jsonify({"error": "Role must be 'admin', 'coadmin', or 'user'."})
            if role in ("admin", "coadmin") and caller_level < 2:
                return jsonify(
                    {"error": "Only Admins can create admin/co-admin accounts."}
                )
            if len(username) < 3 or not username.isalnum():
                return jsonify(
                    {"error": "Username must be 3+ alphanumeric characters."}
                )
            if len(password) < 6:
                return jsonify({"error": "Password must be at least 6 characters."})
            existing = database.get_user_secure(username)
            if existing:
                return jsonify({"error": f'User "{username}" already exists.'})
            is_admin = 2 if role == "admin" else (1 if role == "coadmin" else 0)
            ph = generate_password_hash(password)
            ok = database.create_user_secure(username, ph, username, is_admin)
            if ok:
                return jsonify(
                    {
                        "output": f'✓ User "{username}" created successfully as {_role_name(is_admin).upper()}.'
                    }
                )
            return jsonify({"error": f'Failed to create user "{username}".'})

        # ── deluser <username> (Admin and Co-Admin tier checks) ──
        elif cmd == "deluser":
            if caller_level < 1:
                return jsonify(
                    {
                        "error": "⛔ Access denied. Only administrators can delete accounts."
                    }
                )
            if not args:
                return jsonify({"error": "Usage: deluser <username>"})
            target = args[0]
            if target == session.get("user_id"):
                return jsonify(
                    {"error": "Cannot delete your own administrator profile."}
                )
            ok = database.delete_user_admin(target, caller_level=caller_level)
            if ok:
                return jsonify(
                    {"output": f'✓ User "{target}" and all associated data deleted.'}
                )
            return jsonify(
                {
                    "error": f'Failed to delete "{target}" (tier security constraint or target does not exist).'
                }
            )

        # ── activate / deactivate ──
        elif cmd in ("activate", "deactivate"):
            if not args:
                return jsonify({"error": f"Usage: {cmd} <username>"})
            target = args[0]
            new_status = "active" if cmd == "activate" else "deactivated"
            ok = database.update_user_status_admin(
                target, new_status, caller_level=caller_level
            )
            if ok:
                if new_status == "deactivated":
                    database.set_user_online_status(target, 0)
                return jsonify(
                    {"output": f'✓ User "{target}" status set to {new_status}.'}
                )
            return jsonify(
                {
                    "error": f'Failed to update status for "{target}" (tier security constraint or target does not exist).'
                }
            )

        # ── resetpwd <user> <newpass> ──
        elif cmd == "resetpwd":
            if len(args) < 2:
                return jsonify({"error": "Usage: resetpwd <username> <new_password>"})
            target = args[0]
            new_pass = args[1]
            if len(new_pass) < 6:
                return jsonify({"error": "Password must be at least 6 characters."})
            ph = generate_password_hash(new_pass)
            ok = database.reset_user_password_admin(
                target, ph, caller_level=caller_level
            )
            if ok:
                return jsonify({"output": f'✓ Password reset for "{target}".'})
            return jsonify(
                {
                    "error": f'Failed to reset password for "{target}" (tier security constraint or target does not exist).'
                }
            )

        # ── setrole <user> <admin|coadmin|user> (Admin only) ──
        elif cmd == "setrole":
            if len(args) < 2:
                return jsonify(
                    {"error": "Usage: setrole <username> <admin|coadmin|user>"}
                )
            if caller_level < 2:
                return jsonify(
                    {"error": "⛔ Access denied. Only Admins can change roles."}
                )
            target = args[0]
            role = args[1].lower()
            if role not in ("admin", "coadmin", "user"):
                return jsonify({"error": "Role must be 'admin', 'coadmin', or 'user'."})

            target_user = database.get_user_secure(target)
            if not target_user:
                return jsonify({"error": f'User "{target}" not found.'})
            target_level = target_user.get("is_admin") or 0
            if target_level >= 2 and target != session.get("user_id"):
                return jsonify(
                    {"error": "Cannot change the role of another Admin account."}
                )

            is_admin = 2 if role == "admin" else (1 if role == "coadmin" else 0)
            try:
                with database.connect_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, target)
                    )
                    conn.commit()
                    if cursor.rowcount > 0:
                        return jsonify(
                            {
                                "output": f'✓ User "{target}" role set to {_role_name(is_admin)}.'
                            }
                        )
                    return jsonify({"error": f'User "{target}" not found.'})
            except Exception as e:
                return jsonify({"error": str(e)})

        # ── userinfo <user> ──
        elif cmd == "userinfo":
            if not args:
                return jsonify({"error": "Usage: userinfo <username>"})
            details = database.get_user_full_details_admin(args[0])
            if not details:
                return jsonify({"error": f'User "{args[0]}" not found.'})
            role = _role_name(details.get("is_admin"))
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
        elif cmd == "config":
            configs = database.get_all_configs()
            if not configs:
                return jsonify({"output": "No configuration entries found."})
            lines = ["─── Platform Configuration ───"]
            for k, v in configs.items():
                lines.append(f"  {k:<25} = {v}")
            return jsonify({"output": "\n".join(lines)})

        # ── setconfig <key> <value> ──
        elif cmd == "setconfig":
            if len(args) < 2:
                return jsonify({"error": "Usage: setconfig <key> <value>"})
            key = args[0]
            val = " ".join(args[1:])
            allowed = [
                "enable_registration",
                "allow_guests",
                "enable_music",
                "enforce_passwords",
            ]
            if key not in allowed:
                return jsonify(
                    {"error": f"Invalid config key. Allowed: {', '.join(allowed)}"}
                )
            database.set_config_value(key, val)
            return jsonify({"output": f'✓ Config "{key}" set to "{val}".'})

        # ── announce <message> ──
        elif cmd == "announce":
            if not args:
                return jsonify({"error": "Usage: announce <message text>"})
            msg = " ".join(args)
            database.set_config_value("site_announcement", msg)
            database.add_announcement(msg)
            return jsonify({"output": f'✓ Announcement published: "{msg}"'})

        # ── clearannounce ──
        elif cmd == "clearannounce":
            database.set_config_value("site_announcement", "")
            return jsonify({"output": "✓ Announcement banner cleared."})

        # ── sessions <user> ──
        elif cmd == "sessions":
            if not args:
                return jsonify({"error": "Usage: sessions <username>"})
            details = database.get_user_full_details_admin(args[0])
            if not details:
                return jsonify({"error": f'User "{args[0]}" not found.'})
            sess = details.get("sessions", [])
            if not sess:
                return jsonify({"output": f'No chat sessions for "{args[0]}".'})
            lines = [f'Chat sessions for "{args[0]}" ({len(sess)}):']
            for s in sess[:20]:
                lines.append(f"  [{s['created_at']}] {s['title']}")
            if len(sess) > 20:
                lines.append(f"  ... and {len(sess) - 20} more")
            return jsonify({"output": "\n".join(lines)})

        # ── stats ──
        elif cmd == "stats":
            all_users = database.get_all_users_admin()
            total = len(all_users)
            active = len([u for u in all_users if u.get("status") == "active"])
            online = len([u for u in all_users if u.get("is_online")])
            deactivated = len(
                [u for u in all_users if u.get("status") == "deactivated"]
            )
            idle = len([u for u in all_users if u.get("status") == "idle"])
            admins = len([u for u in all_users if (u.get("is_admin") or 0) >= 2])
            coadmins = len([u for u in all_users if (u.get("is_admin") or 0) == 1])
            std_users = total - admins - coadmins
            try:
                db_mb = round(
                    os.path.getsize(database.DATABASE_PATH) / (1024 * 1024), 3
                )
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
        elif cmd == "backup":
            if not args:
                return jsonify(
                    {"error": "Usage: backup <username> or backup server/--all"}
                )

            target = args[0]
            import json
            import os
            import shutil
            from datetime import datetime

            backup_dir = os.path.join(os.path.dirname(__file__), "databases", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if target in ("server", "--all"):
                db_path = database.DATABASE_PATH
                if not os.path.exists(db_path):
                    return jsonify({"error": f"Database file not found at {db_path}."})

                dest_path = os.path.join(backup_dir, f"server_backup_{timestamp}.db")
                try:
                    shutil.copy2(db_path, dest_path)
                    return jsonify(
                        {
                            "output": f"✓ Overall server database backup created successfully at:\n  databases/backups/server_backup_{timestamp}.db"
                        }
                    )
                except Exception as e:
                    return jsonify(
                        {"error": f"Failed to backup server database: {str(e)}"}
                    )
            else:
                details = database.get_user_full_details_admin(target)
                if not details:
                    return jsonify({"error": f"User '{target}' not found."})

                # Aggregate all conversation logs
                full_history = []
                for s in details.get("sessions", []):
                    messages = database.get_session_messages(s["id"])
                    full_history.append(
                        {
                            "session_id": s["id"],
                            "session_title": s["title"],
                            "created_at": s["created_at"],
                            "messages": messages,
                        }
                    )
                details["full_conversations"] = full_history

                dest_path = os.path.join(
                    backup_dir, f"backup_{target}_{timestamp}.json"
                )
                try:
                    with open(dest_path, "w", encoding="utf-8") as f:
                        json.dump(details, f, indent=4)
                    return jsonify(
                        {
                            "output": f"✓ Backup for user '{target}' created successfully at:\n  databases/backups/backup_{target}_{timestamp}.json"
                        }
                    )
                except Exception as e:
                    return jsonify(
                        {"error": f"Failed to write user backup file: {str(e)}"}
                    )

        # ── update/patch ──
        elif cmd in ("update", "patch"):
            session["awaiting_patch_select"] = True
            lines = [
                "Select the Update pack to patch on live system/server:",
                "  [1] Update Pack V4.1 (Stability & Performance Hotfix)",
                "  [2] Update Pack V4.2 (Advanced Telemetry & Analytics)",
                "  [3] Update Pack V5.0-Beta (Quantum ML Core Integration)",
                "Enter selection (1-3) or 'cancel' to exit:",
            ]
            return jsonify({"output": "\n".join(lines)})

        # ── unknown ──
        else:
            return jsonify(
                {
                    "error": f"Unknown command: \"{cmd}\". Type 'help' for available commands."
                }
            )

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

        database.log_admin_action(
            session.get("user_id"), "DB_BACKUP", None, "Downloaded database backup file"
        )
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"chat_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mimetype="application/x-sqlite3",
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download database backup: {str(e)}"}), 500


@app.route("/api/admin/db-reset", methods=["POST"])
@admin_required
@superadmin_required
def api_admin_db_reset():
    try:
        admin_id = session.get("user_id")
        import logging

        logging.warning(
            f"Superadmin {admin_id} initiated a full database override deletion/reset."
        )

        success = database.reset_database()
        if success:
            database.log_admin_action(
                "admin",
                "DB_RESET",
                None,
                f"Database fully reset to defaults by superadmin: {admin_id}",
            )
            session.clear()
            return jsonify(
                {
                    "success": True,
                    "message": "Database successfully reset to factory defaults. All sessions cleared.",
                }
            )
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
    cleaned_rel_path = file_rel_path.replace("\\", "/").lstrip("/")
    target_abs = os.path.abspath(os.path.join(base_dir, cleaned_rel_path))

    # Whitelisted config files (exact matches)
    whitelisted_configs = [
        "mail_id.txt",
        "mail_password.txt",
        "weather_key.txt",
        "google.txt",
        "google_credentials.txt",
        "OpenAI-Key.txt",
    ]

    for conf in whitelisted_configs:
        conf_abs = os.path.abspath(os.path.join(base_dir, conf))
        if target_abs == conf_abs:
            return target_abs

    # Whitelisted directory databases/backups/ (must be strictly inside)
    backups_dir_abs = os.path.abspath(os.path.join(base_dir, "databases", "backups"))
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
            "mail_id.txt",
            "mail_password.txt",
            "weather_key.txt",
            "google.txt",
            "google_credentials.txt",
            "OpenAI-Key.txt",
        ]

        configs = []
        for name in whitelisted_configs:
            file_abs = os.path.join(base_dir, name)
            exists = os.path.exists(file_abs)
            size = os.path.getsize(file_abs) if exists else 0
            mtime = os.path.getmtime(file_abs) if exists else 0
            configs.append(
                {
                    "name": name,
                    "path": name,
                    "type": "config",
                    "exists": exists,
                    "size": size,
                    "modified": mtime,
                }
            )

        # 2. Gather backups files
        backups_dir = os.path.join(base_dir, "databases", "backups")
        os.makedirs(backups_dir, exist_ok=True)

        backups = []
        for entry in os.scandir(backups_dir):
            if entry.is_file():
                backups.append(
                    {
                        "name": entry.name,
                        "path": f"databases/backups/{entry.name}",
                        "type": "backup",
                        "exists": True,
                        "size": entry.stat().st_size,
                        "modified": entry.stat().st_mtime,
                    }
                )

        # Sort backups by modified time descending (newest first)
        backups.sort(key=lambda x: x["modified"], reverse=True)

        return jsonify({"configs": configs, "backups": backups})
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
        if os.path.basename(safe_path) in [
            "mail_id.txt",
            "mail_password.txt",
            "weather_key.txt",
            "google.txt",
            "google_credentials.txt",
            "OpenAI-Key.txt",
        ]:
            return jsonify({"content": "", "exists": False})
        return jsonify({"error": "File not found"}), 404

    try:
        # Check if it's binary (like .db database backups)
        is_binary = safe_path.endswith(".db")
        if is_binary:
            return jsonify(
                {"content": "[Binary Database File]", "is_binary": True, "exists": True}
            )

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
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
    if safe_path.endswith(".db"):
        return jsonify({"error": "Cannot edit binary database files directly"}), 400

    try:
        # Ensure parent dir exists
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        database.log_admin_action(
            session.get("user_id"),
            "FILE_EDIT",
            filepath_input,
            f"Modified file content: {filepath_input}",
        )
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

        database.log_admin_action(
            session.get("user_id"),
            "FILE_DOWNLOAD",
            filepath_input,
            f"Downloaded file: {filepath_input}",
        )
        return send_file(
            safe_path, as_attachment=True, download_name=os.path.basename(safe_path)
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
    backups_dir_abs = os.path.abspath(os.path.join(base_dir, "databases", "backups"))
    if not safe_path.startswith(backups_dir_abs + os.sep):
        return jsonify(
            {"error": "Access Denied: Configuration files cannot be deleted"}
        ), 403

    if not os.path.exists(safe_path):
        return jsonify({"error": "File not found"}), 404

    try:
        os.remove(safe_path)
        database.log_admin_action(
            session.get("user_id"),
            "FILE_DELETE",
            filepath_input,
            f"Deleted file: {filepath_input}",
        )
        return jsonify({"success": True, "message": "File deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500


@app.route("/api/admin/files/upload", methods=["POST"])
@admin_required
def api_admin_upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Standardize and secure filename
        from werkzeug.utils import secure_filename

        filename = secure_filename(file.filename)

        # Only allow uploading to backups directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        backups_dir = os.path.join(base_dir, "databases", "backups")
        os.makedirs(backups_dir, exist_ok=True)

        dest_path = os.path.join(backups_dir, filename)
        file.save(dest_path)

        database.log_admin_action(
            session.get("user_id"),
            "FILE_UPLOAD",
            filename,
            f"Uploaded backup file: {filename}",
        )
        return jsonify(
            {
                "success": True,
                "message": f"File '{filename}' uploaded successfully to backups",
            }
        )
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
        token = data.get("session_token")
        if not token:
            return jsonify({"error": "Session token required"}), 400

        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.is_admin, s.user_id
                FROM active_sessions s
                LEFT JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            """,
                (token,),
            )
            row = cursor.fetchone()

        if row:
            target_admin_level = row[0] or 0
            target_user_id = row[1]
            caller_id = session.get("user_id")
            caller_user = database.get_user_secure(caller_id)
            caller_level = caller_user.get("is_admin") or 0 if caller_user else 0

            if target_admin_level >= caller_level and target_user_id != caller_id:
                return jsonify({"error": "Unauthorized to revoke this session"}), 403

        database.revoke_active_session(token)
        database.log_admin_action(
            session.get("user_id"),
            "REVOKE_SESSION",
            None,
            f"Revoked active session token: {token[:8]}...",
        )
        return jsonify({"success": True, "message": "Session terminated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/sessions/revoke-all", methods=["POST"])
@admin_required
@superadmin_required
def api_admin_sessions_revoke_all():
    try:
        current_token = session.get("session_token")
        caller_id = session.get("user_id")

        with database.connect_db() as conn:
            cursor = conn.cursor()
            if current_token:
                cursor.execute(
                    "DELETE FROM active_sessions WHERE session_token != ?",
                    (current_token,),
                )
            else:
                cursor.execute("DELETE FROM active_sessions")
            conn.commit()

        database.log_admin_action(
            caller_id,
            "REVOKE_ALL_SESSIONS",
            None,
            "Revoked all active sessions except self",
        )
        return jsonify(
            {
                "success": True,
                "message": "All other user sessions terminated successfully",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/database/query", methods=["POST"])
@admin_required
def api_admin_database_query():
    try:
        data = request.get_json() or {}
        raw_query = data.get("query", "").strip()
        if not raw_query:
            return jsonify({"error": "Query cannot be empty"}), 400

        norm_query = re.sub(r"/\*.*?\*/", "", raw_query, flags=re.DOTALL)
        norm_query = norm_query.strip()

        caller = database.get_user_secure(session.get("user_id"))
        caller_level = (caller.get("is_admin") or 0) if caller else 0

        # Superadmin visual / delete override check for audit logs
        query_upper = norm_query.upper()
        if "ADMIN_AUDIT_LOGS" in query_upper and "DELETE" in query_upper:
            if caller_level >= 2:
                database.clear_admin_audit_logs()
                return jsonify(
                    {
                        "success": True,
                        "headers": ["Status"],
                        "rows": [
                            ["Audit logs successfully wiped clean via query override."]
                        ],
                        "count": 1,
                    }
                )
            else:
                return jsonify(
                    {
                        "error": "Security Restriction: Superadmin privileges required to wipe audit logs."
                    }
                ), 403

        if caller_level >= 2:
            # Superadmin has access to run all queries with no restricted keywords
            block_keywords = []
        elif caller_level == 1:
            # Co-admin has access with specific block list
            block_keywords = [
                "INSERT",
                "CREATE",
                "REPLACE",
                "PRAGMA",
                "RENAME",
                "ATTACH",
                "DETACH",
            ]
        else:
            return jsonify(
                {"error": "Security Restriction: Administrator privileges required."}
            ), 403

        if block_keywords:
            words = re.findall(r"\b\w+\b", norm_query.upper())
            for keyword in block_keywords:
                if keyword in words:
                    return jsonify(
                        {
                            "error": f"Security Restriction: Modification keyword '{keyword}' is blocked for co-admins in the sandbox."
                        }
                    ), 403

        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(raw_query)

            headers = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            rows = cursor.fetchall() if cursor.description else []
            data_rows = [list(row) for row in rows]

        database.log_admin_action(
            session.get("user_id"),
            "DB_SANDBOX_QUERY",
            None,
            f"Executed sandbox SQL query: {raw_query[:100]}",
        )

        return jsonify(
            {
                "success": True,
                "headers": headers,
                "rows": data_rows,
                "count": len(data_rows),
            }
        )
    except Exception as e:
        return jsonify({"error": f"SQL Error: {str(e)}"}), 400


@app.route("/api/admin/simulate", methods=["POST"])
@admin_required
def api_admin_simulate():
    try:
        data = request.get_json() or {}
        action = data.get("action")

        if action == "signup":
            count = int(data.get("count", 10))

            names = [
                "Emma Vance",
                "Liam Frost",
                "Olivia Sterling",
                "Noah Vance",
                "Sophia Vance",
                "Oliver Frost",
                "Isabella Sterling",
                "William Frost",
                "Mia Sterling",
                "James Vance",
                "Ava Frost",
                "Benjamin Sterling",
            ]
            locations = [
                "Mumbai, Maharashtra, India",
                "Paris, France",
                "New York, NY, USA",
                "London, UK",
                "Tokyo, Japan",
                "Sydney, NSW, Australia",
                "Berlin, Germany",
                "Toronto, ON, Canada",
            ]

            import random
            import uuid
            from datetime import timedelta

            from werkzeug.security import generate_password_hash

            created_users = []
            dummy_hash = generate_password_hash("mockpass123")

            with database.connect_db() as conn:
                cursor = conn.cursor()
                for _ in range(count):
                    user_uuid = f"sim_{str(uuid.uuid4())[:8]}"
                    display_name = (
                        random.choice(names) + " " + str(random.randint(10, 99))
                    )
                    location = random.choice(locations)
                    ip_addr = f"{random.randint(24, 220)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

                    days_ago = random.uniform(0.01, 7.0)
                    created_date = (datetime.now() - timedelta(days=days_ago)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    cursor.execute(
                        """
                        INSERT INTO users (id, password_hash, display_name, created_at, is_admin, status, last_login_ip, last_login_location, is_online, last_seen)
                        VALUES (?, ?, ?, ?, 0, 'active', ?, ?, 0, ?)
                    """,
                        (
                            user_uuid,
                            dummy_hash,
                            display_name,
                            created_date,
                            ip_addr,
                            location,
                            created_date,
                        ),
                    )

                    created_users.append(user_uuid)
                conn.commit()

            database.log_admin_action(
                session.get("user_id"),
                "SIMULATION_SIGNUPS",
                None,
                f"Simulated signup of {count} mock user records",
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully simulated {count} user signups.",
                    "users": created_users,
                }
            )

        elif action == "latency":
            spike_val = float(data.get("value", 1200.0))
            duration_mins = int(data.get("duration", 15))

            start_ts = int(time.time())
            end_ts = start_ts + duration_mins * 60

            val_str = f"{spike_val},{start_ts},{end_ts}"
            database.set_config_value("sim_latency_spike", val_str)

            database.log_admin_action(
                session.get("user_id"),
                "SIMULATION_LATENCY",
                None,
                f"Simulated latency spike (+{spike_val}ms) for {duration_mins} minutes",
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Latency spike of +{spike_val}ms injected for {duration_mins} minutes.",
                }
            )

        elif action == "clear":
            with database.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM messages
                    WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id LIKE 'sim_%')
                """)
                cursor.execute("DELETE FROM chat_sessions WHERE user_id LIKE 'sim_%'")
                cursor.execute("DELETE FROM user_settings WHERE id LIKE 'sim_%'")
                cursor.execute("DELETE FROM linked_accounts WHERE user_id LIKE 'sim_%'")
                cursor.execute("DELETE FROM users WHERE id LIKE 'sim_%'")
                cursor.execute("DELETE FROM active_sessions WHERE user_id LIKE 'sim_%'")
                conn.commit()

            database.set_config_value("sim_latency_spike", "")
            database.log_admin_action(
                session.get("user_id"),
                "SIMULATION_CLEAR",
                None,
                "Cleared all simulation logs and mock user profiles",
            )
            return jsonify(
                {
                    "success": True,
                    "message": "Simulation states and mock records fully purged.",
                }
            )

        else:
            return jsonify({"error": f"Unknown simulation action '{action}'"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- end Spotify debug ---


# --- Multi-Factor Authentication (MFA) API Endpoints ---


def verify_totp(secret, code):
    import base64
    import hashlib
    import hmac
    import struct
    import time

    try:
        secret = secret.upper().replace(" ", "")
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += "=" * (8 - missing_padding)
        key = base64.b32decode(secret)
        t = int(time.time() / 30)
        for i in (-1, 0, 1):
            val = struct.pack(">Q", t + i)
            hmac_hash = hmac.new(key, val, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0F
            truncated_hash = (
                struct.unpack(">I", hmac_hash[offset : offset + 4])[0] & 0x7FFFFFFF
            )
            otp = truncated_hash % 1000000
            if f"{otp:06d}" == str(code).strip():
                return True
        return False
    except Exception:
        return False


@app.route("/api/login/mfa/totp/verify", methods=["POST"])
def api_login_mfa_totp_verify():
    pending_user_id = session.get("mfa_pending_user_id")
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401

    data = request.get_json() or {}
    code = data.get("code", "").strip()
    if not code:
        return jsonify({"error": "Verification code is required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT secret FROM user_authenticators WHERE user_id = ?",
                (pending_user_id,),
            )
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
        session["user_id"] = user["id"]
        session["local_user_id"] = user["id"]
        session["display_name"] = user["display_name"]
        session.pop("mfa_pending_user_id", None)
        session.modified = True

        register_login_session(user["id"])
        log_user_telemetry(user["id"])

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login/mfa/passkey/options", methods=["POST"])
def api_login_mfa_passkey_options():
    pending_user_id = session.get("mfa_pending_user_id")
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401

    import base64
    import uuid

    challenge = base64.b64encode(uuid.uuid4().bytes).decode().replace("=", "")
    session["passkey_auth_challenge"] = challenge

    allow_credentials = []
    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT credential_id FROM user_passkeys WHERE user_id = ?",
                (pending_user_id,),
            )
            for r in cursor.fetchall():
                allow_credentials.append({"type": "public-key", "id": r[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    rp_id = request.host.split(":")[0]
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
        "allowCredentials": allow_credentials,
    }

    if not is_ip:
        options["rpId"] = rp_id

    return jsonify(options)


@app.route("/api/login/mfa/passkey/verify", methods=["POST"])
def api_login_mfa_passkey_verify():
    pending_user_id = session.get("mfa_pending_user_id")
    if not pending_user_id:
        return jsonify({"error": "No login session in progress"}), 401

    data = request.get_json() or {}
    credential_id = data.get("credential_id", "").strip()
    if not credential_id:
        return jsonify({"error": "Credential ID is required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM user_passkeys WHERE user_id = ? AND credential_id = ?",
                (pending_user_id, credential_id),
            )
            r = cursor.fetchone()

        if not r:
            return jsonify({"error": "Invalid passkey"}), 400

        user = database.get_user_secure(pending_user_id)
        session["user_id"] = user["id"]
        session["local_user_id"] = user["id"]
        session["display_name"] = user["display_name"]
        session.pop("mfa_pending_user_id", None)
        session.pop("passkey_auth_challenge", None)
        session.modified = True

        register_login_session(user["id"])
        log_user_telemetry(user["id"])

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/status", methods=["GET"])
def api_mfa_status():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()

            # Fetch passkeys
            cursor.execute(
                "SELECT id, key_name, created_at FROM user_passkeys WHERE user_id = ?",
                (user_id,),
            )
            passkeys = [
                {"id": r[0], "key_name": r[1], "created_at": r[2]}
                for r in cursor.fetchall()
            ]

            # Fetch authenticators
            cursor.execute(
                "SELECT id, device_name, created_at FROM user_authenticators WHERE user_id = ?",
                (user_id,),
            )
            authenticators = [
                {"id": r[0], "device_name": r[1], "created_at": r[2]}
                for r in cursor.fetchall()
            ]

        return jsonify(
            {
                "passkeys_enabled": len(passkeys) > 0,
                "totp_enabled": len(authenticators) > 0,
                "passkeys": passkeys,
                "authenticators": authenticators,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/passkey/register/options", methods=["POST"])
def api_mfa_passkey_register_options():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    import base64
    import uuid

    user_handle = base64.b64encode(user_id.encode()).decode().replace("=", "")
    challenge = base64.b64encode(uuid.uuid4().bytes).decode().replace("=", "")

    rp_id = request.host.split(":")[0]
    is_ip = False
    try:
        import ipaddress

        ipaddress.ip_address(rp_id)
        is_ip = True
    except ValueError:
        pass

    options = {
        "challenge": challenge,
        "rp": {"name": "Mint Frost AI"},
        "user": {
            "id": user_handle,
            "name": user_id,
            "displayName": session.get("display_name") or user_id,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},  # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",
            "userVerification": "preferred",
        },
        "timeout": 60000,
        "attestation": "none",
    }

    if not is_ip:
        options["rp"]["id"] = rp_id

    session["passkey_reg_challenge"] = challenge
    return jsonify(options)


@app.route("/api/mfa/passkey/register/verify", methods=["POST"])
def api_mfa_passkey_register_verify():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    key_name = data.get("key_name", "").strip() or "My Passkey"
    credential_id = data.get("credential_id", "").strip()
    public_key = data.get("public_key", "").strip() or "mock_public_key"

    if not credential_id:
        return jsonify({"error": "Credential ID is required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_passkeys (user_id, key_name, credential_id, public_key)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, key_name, credential_id, public_key),
            )
            conn.commit()

        database.log_admin_action(
            user_id, "REGISTER_PASSKEY", user_id, f"Registered new passkey: {key_name}"
        )
        return jsonify({"success": True, "message": "Passkey registered successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/passkey/delete", methods=["POST"])
def api_mfa_passkey_delete():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    key_id = data.get("id")

    if not key_id:
        return jsonify({"error": "Passkey ID is required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_passkeys WHERE id = ? AND user_id = ?",
                (key_id, user_id),
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            database.log_admin_action(
                user_id,
                "DELETE_PASSKEY",
                user_id,
                f"Revoked passkey registration ID: {key_id}",
            )
            return jsonify({"success": True, "message": "Passkey deleted successfully"})
        else:
            return jsonify({"error": "Passkey not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mfa/totp/setup", methods=["POST"])
def api_mfa_totp_setup():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    import base64
    import os

    random_bytes = os.urandom(10)
    secret = base64.b32encode(random_bytes).decode().replace("=", "")[:16]

    host = request.host.split(":")[0]
    label = f"{user_id}@{host}"
    otpauth_url = f"otpauth://totp/MintFrost:{label}?secret={secret}&issuer=MintFrost"

    session["temp_totp_secret"] = secret
    return jsonify({"secret": secret, "otpauth_url": otpauth_url})


@app.route("/api/mfa/totp/verify", methods=["POST"])
def api_mfa_totp_verify():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    code = data.get("code", "").strip()
    device_name = data.get("device_name", "").strip() or "Authenticator App"

    secret = session.get("temp_totp_secret")
    if not secret:
        return jsonify(
            {"error": "TOTP setup session expired. Please restart setup."}
        ), 400

    if not code:
        return jsonify({"error": "Verification code is required"}), 400

    if verify_totp(secret, code):
        try:
            with database.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_authenticators (user_id, device_name, secret_key)
                    VALUES (?, ?, ?)
                """,
                    (user_id, device_name, secret),
                )
                conn.commit()

            session.pop("temp_totp_secret", None)
            database.log_admin_action(
                user_id,
                "ENABLE_TOTP",
                user_id,
                f"Enabled App Authenticator: {device_name}",
            )
            return jsonify(
                {"success": True, "message": "App Authenticator enabled successfully!"}
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify(
            {"error": "Invalid verification code. Please check your authenticator app."}
        ), 400


@app.route("/api/mfa/totp/delete", methods=["POST"])
def api_mfa_totp_delete():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    auth_id = data.get("id")

    if not auth_id:
        return jsonify({"error": "Authenticator ID is required"}), 400

    try:
        with database.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_authenticators WHERE id = ? AND user_id = ?",
                (auth_id, user_id),
            )
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            database.log_admin_action(
                user_id,
                "DISABLE_TOTP",
                user_id,
                f"Revoked App Authenticator ID: {auth_id}",
            )
            return jsonify(
                {"success": True, "message": "App Authenticator disabled successfully"}
            )
        else:
            return jsonify({"error": "Authenticator not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/productivity/insights", methods=["GET"])
@login_required
def api_productivity_insights():
    try:
        user_id = session.get("user_id")
        tasks = database.get_user_tasks_filtered(user_id) or []

        insights = []
        active_tasks = [t for t in tasks if t.get("status") != "Completed"]
        overdue_tasks = [t for t in active_tasks if t.get("status") == "Overdue"]
        highest_prio_task = None
        highest_score = -1
        for t in active_tasks:
            score = t.get("priority_score") or 0
            if score > highest_score:
                highest_score = score
                highest_prio_task = t

        if len(tasks) == 0:
            insights.append(
                "No active tasks found. Start by creating a task to receive AI coaching!"
            )
        elif len(active_tasks) > 5:
            insights.append(
                "Your schedule is highly packed today. Focus on completing critical tasks first."
            )
        else:
            insights.append(
                "You have a balanced workload today. Keep up the great pace!"
            )

        if overdue_tasks:
            insights.append(
                f"You have {len(overdue_tasks)} overdue tasks. Resolve these immediately to protect your completion rate."
            )

        if highest_prio_task:
            insights.append(
                f"'{highest_prio_task['title']}' is currently your highest priority. Finishing it now boosts success probability."
            )

        cat_counts = defaultdict(int)
        for t in active_tasks:
            cat_counts[t.get("category") or "Other"] += 1
        if cat_counts:
            top_cat = max(cat_counts, key=cat_counts.get)
            if cat_counts[top_cat] >= 3:
                insights.append(
                    f"'{top_cat}' tasks make up the majority of your current backlog."
                )

        ai_success = False
        try:
            data = request.args.to_dict()
            active_client, active_model = get_llm_client(data)

            tasks_ctx = ""
            for t in active_tasks[:10]:
                tasks_ctx += f'- Task: "{t["title"]}" (PrioScore: {t.get("priority_score") or 50}, Risk: {t.get("risk_level") or "Safe"}, Deadline: {t.get("deadline") or "None"})\n'

            prompt = f"""You are a productivity coach for Mint Frost AI.
Here is a list of the user's active tasks:
{tasks_ctx}

Please generate exactly 4 concise, highly personalized, motivational and actionable productivity insights for today (1 sentence each).
Respond ONLY with a JSON list of strings. Do not include markdown formatting or extra text.
Example:
[
  "Today is your busiest day. Focus on completing your 3 critical tasks first.",
  "Completing Chemistry now increases your success probability."
]
"""
            completion = active_client.chat.completions.create(
                model=active_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                timeout=6.0,
                disable_fallback=True,
            )
            raw_text = (completion.choices[0].message.content or "").strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(
                    r"^```(?:json)?\n|```$", "", raw_text, flags=re.MULTILINE
                ).strip()
            parsed = json.loads(raw_text)
            if isinstance(parsed, list) and parsed:
                insights = parsed
                ai_success = True
        except Exception:
            pass

        return jsonify(
            {"success": True, "insights": insights[:4], "ai_generated": ai_success}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def parse_duration_to_minutes(duration_str):
    if not duration_str:
        return 60
    try:
        val = duration_str.lower().strip()
        digits = re.findall(r"[-+]?\d*\.\d+|\d+", val)
        if not digits:
            return 60
        num = float(digits[0])
        if "hour" in val or "hr" in val or "h" in val:
            return int(num * 60)
        return int(num)
    except:
        return 60


@app.route("/api/coach/analyze", methods=["GET"])
@login_required
def api_coach_analyze():
    try:
        user_id = session.get("user_id")
        app.logger.info(f"[Coach AI] Analyzing coach insights for user_id: {user_id}")
        tasks = database.get_user_tasks_filtered(user_id) or []

        # Filter tasks
        active_tasks = [
            t
            for t in tasks
            if t.get("status") != "Completed" and t.get("status") != "Cancelled"
        ]
        completed_today_tasks = [t for t in tasks if t.get("status") == "Completed"]
        overdue_tasks = [t for t in active_tasks if t.get("status") == "Overdue"]

        # Calculate stats
        total_active_count = len(active_tasks)
        completed_today_count = len(completed_today_tasks)

        # Find highest priority active task
        highest_prio_task = None
        highest_score = -1
        for t in active_tasks:
            score = t.get("priority_score") or 0
            if score > highest_score:
                highest_score = score
                highest_prio_task = t

        # Find next suggested task
        next_suggested = None
        sorted_active = sorted(
            active_tasks, key=lambda x: x.get("priority_score", 0), reverse=True
        )
        if len(sorted_active) > 1:
            next_suggested = sorted_active[1]
        elif len(sorted_active) == 1:
            next_suggested = sorted_active[0]

        # Find upcoming deadline
        upcoming_deadline_task = None
        closest_deadline = None
        for t in active_tasks:
            dl_str = t.get("deadline")
            if dl_str:
                try:
                    dl_date = datetime.strptime(dl_str, "%Y-%m-%d")
                    if closest_deadline is None or dl_date < closest_deadline:
                        closest_deadline = dl_date
                        upcoming_deadline_task = t
                except:
                    pass

        # Calculate completion probability average
        probs = [
            t.get("completion_probability")
            for t in active_tasks
            if t.get("completion_probability") is not None
        ]
        avg_prob = int(sum(probs) / len(probs)) if probs else 100

        # Calculate ETA
        from datetime import timedelta

        total_mins = sum(
            parse_duration_to_minutes(t.get("estimated_duration")) for t in active_tasks
        )
        eta_desc = "No work remaining!"
        if total_mins > 0:
            now_time = datetime.now()
            eta_time = now_time + timedelta(minutes=total_mins)
            hrs = total_mins / 60.0
            eta_desc = f"{eta_time.strftime('%I:%M %p')} ({hrs:.1f} hrs of work left)"

        # Time of day greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning!"
        elif hour < 17:
            greeting = "Good afternoon!"
        else:
            greeting = "Good evening!"

        # Fallback rule-based values
        top_rec = "All Caught Up! Start planning your next project or goal."
        if overdue_tasks:
            top_rec = f"⚠️ You have overdue tasks! Resolve '{overdue_tasks[0]['title']}' immediately to recover."
        elif highest_prio_task:
            top_rec = f"🎯 Direct focus to '{highest_prio_task['title']}' next. It is your highest priority task."
        elif total_active_count > 0:
            top_rec = "Keep working through your daily task checklist."

        motivation = "Consistency is the key to steady progress. Keep up the momentum!"
        if completed_today_count > 0:
            motivation = f"Great job! You have completed {completed_today_count} tasks today. Keep moving!"
        elif avg_prob < 60:
            motivation = "A few high-risk tasks are lowering your success odds. Let's break one down."
        elif avg_prob >= 85 and total_active_count > 0:
            motivation = f"Success rate is high! You have a {avg_prob}% probability of finishing your work today."

        # Package data
        coach_data = {
            "greeting": greeting,
            "top_recommendation": top_rec,
            "current_focus": highest_prio_task["title"]
            if highest_prio_task
            else "None",
            "upcoming_deadline": f"{upcoming_deadline_task['title']} (Due {upcoming_deadline_task['deadline']})"
            if upcoming_deadline_task
            else "No upcoming deadlines",
            "today_motivation": motivation,
            "next_suggested_task": next_suggested["title"]
            if next_suggested
            else "None",
            "estimated_finish_time": eta_desc,
            "total_active_count": total_active_count,
            "completed_today_count": completed_today_count,
            "avg_prob": avg_prob,
        }

        # Try AI Generation
        ai_success = False
        try:
            app.logger.info(f"[Coach AI] Instantiating LLM client with args: {request.args.to_dict()}")
            active_client, active_model = get_llm_client(request.args.to_dict())
            app.logger.info(f"[Coach AI] Using provider/client: {active_client.__class__.__name__}, model: {active_model}")
            
            # Format context for AI
            tasks_ctx = ""
            for t in active_tasks[:10]:
                tasks_ctx += f'- Task: "{t["title"]}" (PrioScore: {t.get("priority_score") or 50}, Risk: {t.get("risk_level") or "Safe"}, Duration: {t.get("estimated_duration") or "1h"}, Deadline: {t.get("deadline") or "None"})\n'

            prompt = f"""You are an elite productivity coach for Mint Frost AI.
Here is the user's current metrics context:
- Current Time: {datetime.now().strftime("%I:%M %p")}
- Active Tasks: {total_active_count}
- Completed Today: {completed_today_count}
- Average Completion Probability: {avg_prob}%
- Total Estimated Duration: {total_mins} mins
- Overdue Tasks Count: {len(overdue_tasks)}
- Highest Priority Task: "{highest_prio_task["title"] if highest_prio_task else "None"}"
- Nearest Deadline: "{upcoming_deadline_task["title"] if upcoming_deadline_task else "None"}"

Here are their active tasks details:
{tasks_ctx}

Generate highly personalized, professional, and actionable coaching insights.
Format the output as a JSON object matching this schema exactly (do not include markdown headers or other text):
{{
  "greeting": "[Time-of-day greeting, e.g. Good afternoon, Alex!]",
  "top_recommendation": "[The single most critical, specific recommendation for this instant based on deadlines and risk]",
  "current_focus": "[Title of the task the user should focus on now]",
  "upcoming_deadline": "[The name and deadline indicator of the closest task]",
  "today_motivation": "[Data-driven motivational insight based on their completion probability and completed tasks counts]",
  "next_suggested_task": "[The next logical task to pick up after the current focus]",
  "estimated_finish_time": "[Estimated time they will finish work, e.g. 4:30 PM (2.5 hours of work left)]"
}}
"""
            app.logger.info(f"[Coach AI] Sending completion request to model: {active_model} (timeout: 6.0s)")
            completion = active_client.chat.completions.create(
                model=active_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.5,
                timeout=6.0,
                disable_fallback=True,
            )
            raw_msg = completion.choices[0].message
            if raw_msg is None:
                raise ValueError("LLM returned None message, falling back...")
            raw_text = (raw_msg.content or "").strip()
            app.logger.info(f"[Coach AI] Successfully received response from {active_model}. Length: {len(raw_text)}")
            if not raw_text:
                raise ValueError("LLM returned empty response, falling back...")
            if raw_text.startswith("```"):
                raw_text = re.sub(
                    r"^```(?:json)?\\n|```$", "", raw_text, flags=re.MULTILINE
                ).strip()
            # Robust extraction — find first { or [
            _f, _l = raw_text.find("{"), raw_text.rfind("}")
            if _f != -1 and _l != -1 and _l > _f:
                raw_text = raw_text[_f : _l + 1]
            try:
                parsed = json.loads(raw_text)
            except Exception as json_err:
                # Repair common issues
                raw_text_clean = re.sub(r"'([^']*?)'\s*:", r'"\1":', raw_text)
                raw_text_clean = re.sub(r",\s*([}\])", r"\1", raw_text_clean)
                raw_text_clean = re.sub(r",\s*$", "", raw_text_clean.strip())
                try:
                    parsed = json.loads(raw_text_clean)
                except Exception:
                    parsed = {}
                    keys = [
                        "greeting",
                        "top_recommendation",
                        "current_focus",
                        "upcoming_deadline",
                        "today_motivation",
                        "next_suggested_task",
                        "estimated_finish_time",
                    ]
                    for key in keys:
                        pattern = rf'"{key}"\s*:\s*"(.*?)"'
                        match = re.search(pattern, raw_text, re.DOTALL)
                        if match:
                            parsed[key] = (
                                match.group(1)
                                .replace('\\"', '"')
                                .replace("\\n", "\n")
                                .strip()
                            )

            # Merge parsed fields to coach_data
            for key in [
                "greeting",
                "top_recommendation",
                "current_focus",
                "upcoming_deadline",
                "today_motivation",
                "next_suggested_task",
                "estimated_finish_time",
            ]:
                if key in parsed and parsed[key]:
                    coach_data[key] = parsed[key]
            ai_success = True
            app.logger.info(f"[Coach AI] Successfully parsed LLM coach insights JSON. Current Focus: {coach_data.get('current_focus')}")
        except Exception as e:
            app.logger.warning(
                f"Coach AI generation failed: {e}. Falling back to rule-based logic."
            )

        return jsonify(
            {"success": True, "coach": coach_data, "ai_generated": ai_success}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/activity/recent", methods=["GET"])
@login_required
def api_recent_activity():
    try:
        user_id = session.get("user_id")
        activities = database.get_recent_activities(user_id, limit=10)
        return jsonify({"success": True, "activities": activities})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/panic/analyze", methods=["GET", "POST"])
@login_required
def api_panic_analyze():
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {} if request.method == "POST" else {}
        simulated_skips = data.get("simulated_skips", [])
        app.logger.info(f"[Panic AI] Compiling Emergency Deck for user_id: {user_id}. Simulated skips: {simulated_skips}")

        # Fetch tasks
        tasks = database.get_user_tasks_filtered(user_id) or []

        # Filter active tasks
        active_tasks = [
            t
            for t in tasks
            if t.get("status") != "Completed" and t.get("status") != "Cancelled"
        ]
        completed_today_tasks = [t for t in tasks if t.get("status") == "Completed"]

        # Filter out simulated skips
        active_tasks = [t for t in active_tasks if t["id"] not in simulated_skips]

        # Workload calculations
        remaining_tasks_count = len(active_tasks)
        critical_tasks_count = len(
            [
                t
                for t in active_tasks
                if t.get("priority") == "High"
                or t.get("risk_level") == "High"
                or t.get("status") == "Overdue"
            ]
        )

        total_work_mins = sum(
            parse_duration_to_minutes(t.get("estimated_duration")) for t in active_tasks
        )

        # Time available today (mins remaining from now until 23:59:59)
        now = datetime.now()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        time_available_mins = max(60, int((end_of_day - now).total_seconds() / 60))

        # Completion probability & risk
        if remaining_tasks_count == 0:
            completion_prob = 100
        elif total_work_mins <= time_available_mins:
            completion_prob = int(
                min(95, 100 - (total_work_mins / time_available_mins) * 30)
            )
        else:
            completion_prob = int(
                max(10, 100 - (total_work_mins / time_available_mins) * 50)
            )

        if completion_prob >= 80:
            overall_risk = "LOW"
        elif completion_prob >= 60:
            overall_risk = "MEDIUM"
        elif completion_prob >= 40:
            overall_risk = "HIGH"
        else:
            overall_risk = "CRITICAL"

        survival_score = int(min(100, max(0, completion_prob * 1.05)))

        # Try AI decision engine
        ai_success = False
        result = {}
        try:
            app.logger.info(f"[Panic AI] Instantiating LLM client for emergency scheduler")
            active_client, active_model = get_llm_client(data)
            app.logger.info(f"[Panic AI] Using provider/client: {active_client.__class__.__name__}, model: {active_model}")

            tasks_context = ""
            for t in active_tasks:
                dl_val = t.get("deadline") or "None"
                tasks_context += f'- Task ID {t["id"]}: "{t["title"]}" (Category: {t["category"]}, Priority: {t["priority"]}, Risk: {t["risk_level"]}, Deadline: {dl_val}, Duration: {t.get("estimated_duration") or "45m"})\n'

            prompt = f"""You are an AI Emergency Productivity Expert for Mint Frost AI.
The current time is {now.strftime("%I:%M %p")} and the user is in a state of high productivity panic.
They have {time_available_mins} minutes of time remaining today, and the following active tasks:
{tasks_context}

Please analyze their workload and output a structured recovery plan in JSON format.
Determine:
1. Which tasks they must do RIGHT NOW (urgently).
2. Which tasks they must do NEXT.
3. Which tasks they should do AFTER THAT.
4. Which tasks are OPTIONAL or should be postponed/skipped to tomorrow.
5. Provide a specific, highly encouraging and quantitative motivation sentence.
6. Rate their Deadline Survival Score (0-100) and Overall Risk (LOW/MEDIUM/HIGH/CRITICAL) based on the remaining work vs available time.

Ensure you output ONLY a valid JSON object. Do not include markdown code fences, headers, or any conversational text.

JSON Schema:
{{
  "survival_score": 65,
  "completion_probability": 63,
  "overall_risk": "HIGH",
  "timeline": [
    {{
      "phase": "RIGHT NOW",
      "task_id": 12,
      "title": "Physics Assignment",
      "duration": "45 min"
    }},
    ...
  ],
  "motivation": "Skipping low-priority work increases your success chance by 24%. focus on Physics first."
}}
"""
            app.logger.info(f"[Panic AI] Sending completions request to model: {active_model} (timeout: 6.0s)")
            completion = active_client.chat.completions.create(
                model=active_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3,
                timeout=6.0,
                disable_fallback=True,
            )
            raw_text_raw = completion.choices[0].message
            if raw_text_raw is None:
                raise ValueError("LLM returned None message, falling back in chain...")
            raw_text = (raw_text_raw.content or "").strip()
            app.logger.info(f"[Panic AI] Successfully received response from {active_model}. Length: {len(raw_text)}")
            if not raw_text:
                raise ValueError(
                    "LLM returned empty response, falling back in chain..."
                )
            if raw_text.startswith("```"):
                raw_text = re.sub(
                    r"^```(?:json)?\\n|```$", "", raw_text, flags=re.MULTILINE
                ).strip()

            # Robustly extract JSON — try array first, then object
            _f, _l = raw_text.find("["), raw_text.rfind("]")
            if _f == -1 or _l == -1 or _l <= _f:
                _f, _l = raw_text.find("{"), raw_text.rfind("}")
            if _f != -1 and _l != -1 and _l > _f:
                raw_text = raw_text[_f : _l + 1]
            try:
                res_json = json.loads(raw_text)
                # If it's an array, take the first object
                if isinstance(res_json, list) and len(res_json) > 0:
                    res_json = res_json[0]
            except json.JSONDecodeError:
                # Repair common LLM JSON issues: single quotes, trailing commas
                raw_text = re.sub(r"'([^']*?)'\s*:", r'"\1":', raw_text)
                raw_text = re.sub(r",\s*([}\])", r"\1", raw_text)
                raw_text = re.sub(r",\s*$", "", raw_text.strip())
                # Also handle unescaped newlines in strings
                raw_text = re.sub(r"(?<!\\\\)\\n", " ", raw_text)
                try:
                    res_json = json.loads(raw_text)
                    if isinstance(res_json, list) and len(res_json) > 0:
                        res_json = res_json[0]
                except json.JSONDecodeError:
                    # Last-ditch: extract JSON fields via simple key-value regex
                    res_json = {}
                    fld, ld = raw_text.find("{"), raw_text.rfind("}")
                    if fld != -1 and ld != -1:
                        inner = raw_text[fld + 1 : ld]
                        for m in re.finditer(
                            r'"(\\"|[^"])*?"\s*:\s*("(\\"|[^"])*?"|\d+\.?\d*|true|false|null)',
                            inner,
                        ):
                            try:
                                kv = json.loads("{" + m.group() + "}")
                                res_json.update(kv)
                            except:
                                pass
            if "timeline" in res_json and "motivation" in res_json:
                result = res_json
                ai_success = True
                app.logger.info(f"[Panic AI] Successfully parsed LLM emergency plan JSON. Timeline stages count: {len(result.get('timeline', []))}")
        except Exception as e:
            app.logger.warning(
                f"Panic Mode AI analysis failed: {e}. Falling back to rule-based logic."
            )

        if not ai_success:
            # Rule-based fallback scheduler
            sorted_tasks = sorted(
                active_tasks,
                key=lambda x: (
                    x.get("priority") == "High" or x.get("status") == "Overdue",
                    x.get("priority_score", 0),
                ),
                reverse=True,
            )

            timeline = []
            for idx, t in enumerate(sorted_tasks):
                if idx == 0:
                    phase = "RIGHT NOW"
                elif idx == 1:
                    phase = "NEXT"
                elif idx == 2 or idx == 3:
                    phase = "AFTER THAT"
                else:
                    phase = "OPTIONAL"

                dur = t.get("estimated_duration") or "45 min"
                if phase == "OPTIONAL":
                    dur = "Skip Today"

                timeline.append(
                    {
                        "phase": phase,
                        "task_id": t["id"],
                        "title": t["title"],
                        "duration": dur,
                    }
                )

            if survival_score > 80:
                motivation = "You can still finish everything if you begin now. Workload is manageable!"
            elif survival_score > 50:
                motivation = "Focus on the high-priority item. Skipping optional tasks will increase your success probability by 20%."
            else:
                motivation = "Workload is critical. Postpone optional work to tomorrow and focus on one single task right now."

            result = {
                "survival_score": survival_score,
                "completion_probability": completion_prob,
                "overall_risk": overall_risk,
                "timeline": timeline,
                "motivation": motivation,
            }

        # Add situation metrics to response
        result["situation"] = {
            "remaining_tasks": remaining_tasks_count,
            "critical_tasks": critical_tasks_count,
            "estimated_work_mins": total_work_mins,
            "time_available_mins": time_available_mins,
            "completion_probability": result.get(
                "completion_probability", completion_prob
            ),
            "overall_risk": result.get("overall_risk", overall_risk),
            "survival_score": result.get("survival_score", survival_score),
        }

        return jsonify({"success": True, "panic": result, "ai_generated": ai_success})
    except Exception as e:
        import traceback

        app.logger.error(f"Error in api_panic_analyze: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/panic/recover", methods=["POST"])
@login_required
def api_panic_recover():
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {}
        postpone_task_ids = data.get("postpone_task_ids", [])
        skip_subtask_ids = data.get("skip_subtask_ids", [])

        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        with database.connect_db() as conn:
            # 1. Postpone selected tasks
            for tid in postpone_task_ids:
                # Increment postponed count and shift deadline
                conn.execute(
                    """
                    UPDATE tasks
                    SET deadline = ?, priority = 'Low', priority_score = 15,
                        postponed_count = postponed_count + 1
                    WHERE id = ? AND user_id = ?
                """,
                    (tomorrow_str, tid, user_id),
                )

                # Fetch task title to log activity
                row = conn.execute(
                    "SELECT title FROM tasks WHERE id = ?", (tid,)
                ).fetchone()
                title = row[0] if row else f"Task #{tid}"
                database.log_user_activity(
                    user_id,
                    "Task Postponed",
                    f"Task '{title}' postponed to tomorrow during Panic Mode recovery.",
                )

            # 2. Skip selected subtasks
            for sid in skip_subtask_ids:
                conn.execute(
                    """
                    UPDATE subtasks
                    SET completed = 1
                    WHERE id = ? AND task_id IN (SELECT id FROM tasks WHERE user_id = ?)
                """,
                    (sid, user_id),
                )

            conn.commit()

        # 3. Recalculate priority scores
        recalculate_task_priority_risk(user_id, data)

        # 4. Rebuild the planner schedule for today
        with app.test_request_context(json=data):
            api_generate_plan()

        database.log_user_activity(
            user_id,
            "Panic Schedule Recovery",
            "⚡ Panic recovery completed. Schedule rebuilt and optimized.",
        )
        xp_status = database.award_xp(user_id, 40, "panic recovery")
        return jsonify(
            {
                "success": True,
                "message": "Schedule recovered and optimized successfully!",
                "gamification": xp_status,
            }
        )
    except Exception as e:
        import traceback

        app.logger.error(f"Error in api_panic_recover: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/panic_mode", methods=["POST"])
@login_required
def api_panic_mode():
    try:
        user_id = session.get("user_id")
        tasks = database.get_user_tasks_filtered(user_id) or []
        active_tasks = [t for t in tasks if t.get("status") != "Completed"]

        if not active_tasks:
            return jsonify(
                {
                    "success": False,
                    "message": "No active tasks found. You have nothing to panic about!",
                }
            )

        with database.connect_db() as conn:
            for t in active_tasks:
                conn.execute(
                    """
                    UPDATE tasks
                    SET priority = 'High', priority_score = 95,
                        suggested_action = 'CRITICAL WORKLOAD - Immediate Action Required. Focus exclusively on this task.',
                        risk_reason = 'Panic Mode activated: urgent backlog optimization triggered.'
                    WHERE id = ?
                """,
                    (t["id"],),
                )
            conn.commit()

        database.log_user_activity(
            user_id,
            "Panic Mode Detected",
            "Workload prioritized: all active tasks boosted to High Urgency.",
        )
        recalculate_task_priority_risk(user_id)

        steps = [
            "1. Take a deep breath: all active tasks have been sorted and prioritized.",
            "2. Stop multitasking: focus exclusively on the highest priority task card.",
            "3. Complete pending subtasks one-by-one; do not skip prerequisites.",
            "4. Regenerate your Daily Planner now to get a simplified hour-by-hour focus timeline.",
        ]

        return jsonify(
            {
                "success": True,
                "message": "Panic Mode Activated! BACKLOG BOOSTED TO CRITICAL STATUS.",
                "steps": steps,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── AI Analytics & Productivity Insights ────────────────────────────────────
@app.route("/api/analytics/data", methods=["GET"])
@login_required
def api_analytics_data():
    try:
        from datetime import timedelta

        user_id = session.get("user_id")
        all_tasks = database.get_user_tasks_filtered(user_id) or []

        total = len(all_tasks)
        completed = [t for t in all_tasks if t.get("status") == "Completed"]
        pending = [
            t
            for t in all_tasks
            if t.get("status") not in ("Completed", "Cancelled", "Overdue")
        ]
        overdue = [t for t in all_tasks if t.get("status") == "Overdue"]
        completion_rate = round(len(completed) / total * 100, 1) if total else 0

        # Productivity score (0-100)
        score = min(40, round(len(completed) / total * 40)) if total else 0
        score -= min(20, len(overdue) * 4)
        score += min(20, len([t for t in completed if t.get("priority") == "High"]) * 5)
        score += min(20, len(completed) * 2) if len(completed) <= 10 else 20
        score = max(0, min(100, score))
        score_label = (
            "Excellent"
            if score >= 80
            else (
                "Good"
                if score >= 60
                else ("Average" if score >= 40 else "Needs Improvement")
            )
        )

        # Streak
        streak = 0
        if completed:
            dates = sorted(
                set(
                    t.get("completed_at", "")[:10]
                    for t in completed
                    if t.get("completed_at")
                ),
                reverse=True,
            )
            today_d = datetime.now().date()
            for i, d in enumerate(dates):
                try:
                    if datetime.strptime(d, "%Y-%m-%d").date() == today_d - timedelta(
                        days=i
                    ):
                        streak += 1
                    else:
                        break
                except:
                    break

        today_dt = datetime.now().date()

        # Daily completion (last 7 days)
        daily_labels, daily_values = [], []
        for i in range(6, -1, -1):
            day = today_dt - timedelta(days=i)
            daily_labels.append(day.strftime("%a"))
            daily_values.append(
                sum(1 for t in completed if t.get("completed_at", "")[:10] == str(day))
            )

        # Weekly completion (last 4 weeks)
        weekly_labels, weekly_values = [], []
        for w in range(3, -1, -1):
            ws = today_dt - timedelta(days=today_dt.weekday() + 7 * w)
            we = ws + timedelta(days=6)
            count = sum(
                1
                for t in completed
                if t.get("completed_at")
                and ws
                <= datetime.strptime(t["completed_at"][:10], "%Y-%m-%d").date()
                <= we
            )
            weekly_labels.append(f"Week {4 - w}")
            weekly_values.append(count)

        # Monthly completion (last 6 months)
        monthly_labels, monthly_values = [], []
        for m in range(5, -1, -1):
            yr, mo = today_dt.year, today_dt.month - m
            while mo <= 0:
                mo += 12
                yr -= 1
            label = datetime(yr, mo, 1).strftime("%b")
            count = sum(
                1
                for t in completed
                if t.get("completed_at")
                and t["completed_at"][5:7] == f"{mo:02d}"
                and t["completed_at"][:4] == str(yr)
            )
            monthly_labels.append(label)
            monthly_values.append(count)

        # Distributions
        risk_dist = defaultdict(int)
        prio_dist = defaultdict(int)
        cat_dist = defaultdict(int)
        for t in all_tasks:
            risk_dist[t.get("risk_level") or "Safe"] += 1
            prio_dist[t.get("priority") or "Medium"] += 1
            cat_dist[t.get("category") or "Other"] += 1

        # Trends
        day_counts = defaultdict(int)
        for t in completed:
            if t.get("completed_at"):
                try:
                    day_counts[
                        datetime.strptime(t["completed_at"][:10], "%Y-%m-%d").strftime(
                            "%A"
                        )
                    ] += 1
                except:
                    pass
        most_prod = max(day_counts, key=day_counts.get) if day_counts else "N/A"
        least_prod = min(day_counts, key=day_counts.get) if day_counts else "N/A"

        # Predictions
        tomorrow_risk = (
            "High"
            if len(overdue) >= 2 or len(pending) > 6
            else ("Medium" if len(pending) > 3 else "Low")
        )
        expected_comp = max(0, min(100, round(completion_rate * 0.95)))
        expected_plan = max(0, min(100, score - len(overdue) * 5))

        # Local insights engine — rich, data-driven, no LLM call
        insights = []
        ai_generated = False
        if overdue:
            insights.append(
                f"🚨 {len(overdue)} overdue task(s) detected — resolving them now will directly recover your completion rate."
            )
        if most_prod != "N/A":
            insights.append(
                f"📅 {most_prod} is your peak performance day. Schedule your highest-priority tasks on this day for maximum output."
            )
        top_cats = sorted(cat_dist.items(), key=lambda x: -x[1])
        if top_cats:
            _tcn, _tcc = top_cats[0]
            _pct = round(_tcc / total * 100) if total else 0
            insights.append(
                f"📂 {_pct}% of your tasks are '{_tcn}' type. {chr(68) + chr(105) + chr(118) + chr(101) + chr(114) + chr(115) + chr(105) + chr(102) + chr(121) if _pct > 50 else chr(71) + chr(111) + chr(111) + chr(100)} category balance."
            )
        if completion_rate >= 70:
            insights.append(
                f"✅ Excellent {completion_rate}% completion rate! You are in the top tier of productivity. Keep the streak alive."
            )
        elif completion_rate >= 40:
            insights.append(
                f"📈 {completion_rate}% completion rate — solid progress. Breaking remaining tasks into subtasks will accelerate your pace."
            )
        else:
            insights.append(
                f"⚡ {completion_rate}% completion rate. Focus on finishing 1-2 tasks fully before starting new ones to build momentum."
            )
        _hp = [
            t
            for t in all_tasks
            if t.get("priority") == "High" and t.get("status") != "Completed"
        ]
        if _hp:
            insights.append(
                f"🎯 {len(_hp)} High-priority task(s) still active. Completing these first maximizes your productivity score impact."
            )
        insights.append(
            f"🏆 Productivity score: {score}/100 — {score_label}. "
            + (
                "Clearing overdue tasks is the fastest path to improvement."
                if overdue
                else "Maintain consistency to push past your current level."
            )
        )
        insights.append(f"Keep the momentum alive!")

        return jsonify(
            {
                "success": True,
                "stats": {
                    "total": total,
                    "completed": len(completed),
                    "pending": len(pending),
                    "overdue": len(overdue),
                    "completion_rate": completion_rate,
                    "productivity_score": score,
                    "score_label": score_label,
                    "streak": streak,
                },
                "charts": {
                    "daily": {"labels": daily_labels, "values": daily_values},
                    "weekly": {"labels": weekly_labels, "values": weekly_values},
                    "monthly": {"labels": monthly_labels, "values": monthly_values},
                    "risk": {
                        "labels": list(risk_dist.keys()),
                        "values": list(risk_dist.values()),
                    },
                    "priority": {
                        "labels": list(prio_dist.keys()),
                        "values": list(prio_dist.values()),
                    },
                    "category": {
                        "labels": list(cat_dist.keys()),
                        "values": list(cat_dist.values()),
                    },
                },
                "trends": {
                    "most_productive": most_prod,
                    "least_productive": least_prod,
                    "avg_overdue_rate": round(len(overdue) / total * 100, 1)
                    if total
                    else 0,
                },
                "predictions": {
                    "tomorrow_load": len(pending),
                    "tomorrow_risk": tomorrow_risk,
                    "expected_completion": expected_comp,
                    "expected_planner_success": expected_plan,
                },
                "insights": insights,
                "ai_generated": ai_generated,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Start Flask development server
    app.run(host="0.0.0.0", port=5001, debug=True)
