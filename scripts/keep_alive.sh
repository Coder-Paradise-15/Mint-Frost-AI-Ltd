#!/bin/bash
# ==============================================================================
# Mint Frost AI - Codespace Keep-Alive & Auto-Heal Daemon
# Prevents idle timeout by generating periodic terminal heartbeats,
# monitors server.py and cloudflared, and auto-restarts them if they drop.
# ==============================================================================

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspaces/Mint-Frost-AI-Ltd}"
if [ ! -d "$WORKSPACE_DIR" ]; then
    WORKSPACE_DIR="$(pwd)"
fi

cd "$WORKSPACE_DIR"

echo "❄️ [Mint Frost AI] Starting Keep-Alive Watchdog..."
echo "Press Ctrl+C to stop. This script maintains active heartbeat and auto-heals processes."

while true; do
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

    # 1. Check if server.py is running
    if ! pgrep -f "frost_engine/server.py" > /dev/null; then
        echo "[$TIMESTAMP] ⚠️ server.py is NOT running! Restarting..."
        nohup python frost_engine/server.py > /tmp/frost.log 2>&1 &
        sleep 2
    fi

    # 2. Check if cloudflared is running
    if ! pgrep -f "cloudflared tunnel" > /dev/null; then
        echo "[$TIMESTAMP] ⚠️ cloudflared tunnel is NOT running! Restarting..."
        nohup cloudflared tunnel --url http://127.0.0.1:11434 > /tmp/cloudflared.log 2>&1 &
        sleep 3
    fi

    # 3. Read current URL
    CURRENT_URL=$(cat "$WORKSPACE_DIR/.frost_tunnel_url" 2>/dev/null || echo "Unknown")

    # 4. Terminal heartbeat to prevent Codespace idle timeout
    echo "[$TIMESTAMP] 💓 Heartbeat OK | Server: Active | Tunnel: Active | URL: $CURRENT_URL"

    # Sleep for 60 seconds before next check
    sleep 60
done
