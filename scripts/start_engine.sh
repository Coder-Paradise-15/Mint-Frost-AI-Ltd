#!/bin/bash
# ==============================================================================
# Mint Frost AI - Automated Codespace Engine & Tunnel Daemon
# Starts frost_engine/server.py and Cloudflare Tunnel automatically,
# extracts the active tunnel URL, and logs cleanly.
# ==============================================================================

set -e

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspaces/Mint-Frost-AI-Ltd}"
if [ ! -d "$WORKSPACE_DIR" ]; then
    WORKSPACE_DIR="$(pwd)"
fi

cd "$WORKSPACE_DIR"

echo "❄️ [Mint Frost AI] Initializing Codespace Engine Daemon..."

# 1. Install or verify cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "⬇️ Installing cloudflared binary..."
    if command -v sudo &> /dev/null; then
        sudo curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
        sudo chmod +x /usr/local/bin/cloudflared
    else
        mkdir -p "$HOME/.local/bin"
        curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "$HOME/.local/bin/cloudflared"
        chmod +x "$HOME/.local/bin/cloudflared"
        export PATH="$HOME/.local/bin:$PATH"
    fi
    echo "✓ cloudflared installed successfully."
fi

# 2. Terminate any previous stale instances
echo "🔄 Cleaning previous instances..."
pkill -f "frost_engine/server.py" || true
pkill -f "cloudflared tunnel" || true
sleep 1

# 3. Start frost_engine/server.py
echo "🚀 Starting frost_engine/server.py on port 11434..."
nohup python frost_engine/server.py > /tmp/frost.log 2>&1 &
SERVER_PID=$!
echo "✓ Server PID: $SERVER_PID"

# Wait for server health
for i in {1..10}; do
    if curl -s http://127.0.0.1:11434/health > /dev/null 2>&1; then
        echo "✓ Server is healthy and listening on port 11434."
        break
    fi
    sleep 1
done

# 4. Start Cloudflare Tunnel
echo "🌐 Launching Cloudflare quick tunnel..."
rm -f /tmp/cloudflared.log
nohup cloudflared tunnel --url http://127.0.0.1:11434 > /tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!
echo "✓ Tunnel PID: $TUNNEL_PID"

# Extract live trycloudflare URL
TUNNEL_URL=""
for i in {1..20}; do
    if [ -f /tmp/cloudflared.log ]; then
        TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9]*\.trycloudflare\.com' /tmp/cloudflared.log | tail -n 1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
    fi
    sleep 1
done

if [ -n "$TUNNEL_URL" ]; then
    echo "===================================================================="
    echo "🎉 AGENT FROSTY ENGINE IS LIVE!"
    echo "🔗 Active Cloudflare Tunnel URL:"
    echo "   $TUNNEL_URL"
    echo "===================================================================="
    echo "$TUNNEL_URL" > /tmp/frost_tunnel_url.txt
    echo "$TUNNEL_URL" > "$WORKSPACE_DIR/.frost_tunnel_url"
else
    echo "⚠️ Tunnel started, but URL extraction is still pending. Check /tmp/cloudflared.log."
fi
