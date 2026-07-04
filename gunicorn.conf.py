# Gunicorn configuration file for Mint Frost AI (v7.0)
import os

# Port assigned by the hosting platform (Suga, Render, etc.)
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Number of worker processes (usually 2-4 per CPU core)
workers = 4

# Increase timeout to 120 seconds to prevent workers from being killed 
# during slow upstream API calls (e.g. free models on OpenRouter)
timeout = 120

# Graceful shutdown timeout
graceful_timeout = 30

# Keepalive connection timeout
keepalive = 2
