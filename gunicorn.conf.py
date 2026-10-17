# Gunicorn configuration file for Mint Frost AI
import os
import sys

# Port assigned by the hosting platform (Suga, Render, Cloud Run, etc.)
port = os.environ.get("PORT", "8080")
bind = f"0.0.0.0:{port}"

# Number of worker processes and threads for concurrent requests & SSE streaming
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = int(os.environ.get("GUNICORN_THREADS", 4))
worker_class = "gthread"

# Timeout settings
timeout = 120
graceful_timeout = 30
keepalive = 5

# CRITICAL FIX 1: Disable sendfile
# In Python 3.12, socket.sendfile raises "ValueError: non-blocking sockets are not supported"
# when running with gthread. Setting sendfile = False uses standard chunked writes.
sendfile = False

# Maximum requests before worker restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# CRITICAL FIX 2: Monkey-patch gunicorn.util.write to prevent BlockingIOError: [Errno 11]
# When gthread handles large responses (>64KB like index.html, static assets), the socket
# is in non-blocking mode. If the OS send buffer is temporarily full, sock.sendall raises
# BlockingIOError: [Errno 11] Resource temporarily unavailable. Setting a positive timeout
# allows Python's sock.sendall() to loop and wait for the buffer to flush cleanly.
try:
    import gunicorn.util
    _orig_write = gunicorn.util.write

    def _safe_write(sock, val, chunked=False):
        try:
            cur_timeout = sock.gettimeout()
            if cur_timeout is None or cur_timeout == 0:
                sock.settimeout(30.0)
        except Exception:
            pass
        return _orig_write(sock, val, chunked=chunked)

    gunicorn.util.write = _safe_write
except Exception as e:
    pass
