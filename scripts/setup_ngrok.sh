#!/bin/bash
# ==============================================================================
# Mint Frost AI - One-Step Ngrok Setup for Codespaces
# Installs ngrok and configures authtoken (No credit card needed)
# Usage: bash scripts/setup_ngrok.sh <YOUR_NGROK_AUTHTOKEN> [OPTIONAL_STATIC_DOMAIN]
# ==============================================================================

set -e

AUTHTOKEN="$1"
STATIC_DOMAIN="$2"

echo "❄️ [Mint Frost AI] Installing Ngrok in Codespaces..."

if ! command -v ngrok &> /dev/null; then
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
      && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
      | sudo tee /etc/apt/sources.list.d/ngrok.list \
      && sudo apt update && sudo apt install ngrok -y
    echo "✓ Ngrok installed successfully!"
else
    echo "✓ Ngrok is already installed."
fi

if [ -n "$AUTHTOKEN" ]; then
    echo "🔑 Configuring Ngrok authtoken..."
    ngrok config add-authtoken "$AUTHTOKEN"
    echo "✓ Authtoken saved."
fi

pkill -f "ngrok http" || true
sleep 1

echo "🌐 Starting Ngrok tunnel on port 11434..."
if [ -n "$STATIC_DOMAIN" ]; then
    nohup ngrok http --url="$STATIC_DOMAIN" 11434 > /tmp/ngrok.log 2>&1 &
else
    nohup ngrok http 11434 > /tmp/ngrok.log 2>&1 &
fi

sleep 3

NGROK_URL=""
for i in {1..10}; do
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | grep -o 'https://[-a-zA-Z0-9\.]*\.ngrok-free\.app' | head -n 1 || true)
    if [ -n "$NGROK_URL" ]; then
        break
    fi
    sleep 1
done

if [ -n "$NGROK_URL" ]; then
    echo "===================================================================="
    echo "🎉 NGROK TUNNEL IS ACTIVE (100% FREE - NO CREDIT CARDS):"
    echo "🔗 Active Ngrok URL:"
    echo "   $NGROK_URL"
    echo "===================================================================="
    echo "$NGROK_URL" > /tmp/frost_tunnel_url.txt
    echo "$NGROK_URL" > "$(pwd)/.frost_tunnel_url"
else
    echo "⚠️ Ngrok launched. Check /tmp/ngrok.log or http://127.0.0.1:4040 for details."
fi
