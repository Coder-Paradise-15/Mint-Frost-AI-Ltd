import os
import sys
import socket
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mintfrost.server")


def get_bindable_ports(candidate_ports):
    """Filter candidate ports to those that can be bound without permission errors."""
    bindable = []
    for p_str in candidate_ports:
        try:
            p = int(p_str)
            if p < 1 or p > 65535:
                continue
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", p))
            s.close()
            bindable.append(str(p))
        except Exception as ex:
            logger.warning("Port %s cannot be bound (%s), skipping.", p_str, ex)
    return bindable


def start():
    logger.info("Initializing Mint Frost AI Server...")

    try:
        from app import app
        logger.info("Flask application loaded successfully.")
    except Exception as e:
        logger.exception("FATAL: Failed to import Flask application: %s", e)
        sys.exit(1)

    # Primary port from environment (Suga, Cloud Run, Render, etc.)
    env_port = os.environ.get("PORT", "8080").strip()

    # Standard container ports that platforms / proxies might route to
    candidate_ports = [env_port, "8080", "8000", "3000", "5000"]
    unique_candidates = []
    for cp in candidate_ports:
        if cp and cp not in unique_candidates:
            unique_candidates.append(cp)

    # Find ports that can actually be bound
    bindable = get_bindable_ports(unique_candidates)
    if not bindable:
        bindable = [env_port or "8080"]

    listen_specs = " ".join(f"*:{p}" for p in bindable)

    # 1. Preferred: Waitress (production multi-threaded WSGI server)
    try:
        from waitress import serve
        logger.info("Starting Waitress WSGI server on: %s (threads=50, channel_timeout=120)", listen_specs)
        serve(app, listen=listen_specs, threads=50, channel_timeout=120)
        return
    except Exception as e:
        logger.warning("Multi-port Waitress failed (%s). Falling back to single port %s.", e, env_port)

    # 2. Fallback: Waitress on primary port
    try:
        from waitress import serve
        target_port = int(env_port) if env_port.isdigit() else 8080
        logger.info("Starting Waitress WSGI server on 0.0.0.0:%s", target_port)
        serve(app, host="0.0.0.0", port=target_port, threads=50, channel_timeout=120)
        return
    except Exception as e2:
        logger.warning("Single-port Waitress failed (%s). Falling back to Flask WSGI.", e2)

    # 3. Last-resort fallback: Built-in Flask server
    target_port = int(env_port) if env_port.isdigit() else 8080
    logger.info("Starting Flask server on 0.0.0.0:%s", target_port)
    app.run(host="0.0.0.0", port=target_port, threaded=True)


if __name__ == "__main__":
    start()
