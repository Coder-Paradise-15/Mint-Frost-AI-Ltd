# Gunicorn configuration file for Mint Frost AI
import os

# Port assigned by the hosting platform (Suga, Render, etc.)
port = os.environ.get("PORT", "5001")
bind = f"0.0.0.0:{port}"

# Number of worker processes and threads for SSE streaming support
workers = 2
threads = 4
worker_class = "gthread"

# Timeout settings
timeout = 120
graceful_timeout = 30
keepalive = 5
