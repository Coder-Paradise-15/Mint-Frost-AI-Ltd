"""
Frost-V1 Dual-Scope System Telemetry Collector
Provides differential telemetry based on user privilege level (Admin vs Regular User).
"""

import os
import sqlite3
import time
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_system_telemetry(user_id=None, is_admin=False, db_conn=None):
    """
    Collects real-time telemetry tailored for Frost-V1 cognitive awareness.
    Admins receive infrastructure metrics; regular users receive personal productivity metrics.
    """
    now = datetime.now()
    telemetry = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "role": "admin" if is_admin else "user",
        "scope": "infrastructure" if is_admin else "personal"
    }

    if is_admin:
        admin_metrics = {
            "os_environment": "Linux / Codespace Container" if os.name != "nt" else "Windows NT",
            "server_time": now.strftime("%H:%M:%S UTC"),
        }

        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=None)
                admin_metrics["cpu_load_percent"] = cpu
                admin_metrics["ram_used_gb"] = round(mem.used / (1024 ** 3), 2)
                admin_metrics["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
                admin_metrics["ram_percent"] = mem.percent
            except Exception:
                pass
        else:
            # Fallback estimation for containerized environments without psutil
            admin_metrics["runtime"] = "Containerized vCPU / Headless"

        # Check DB Status if connection or file available
        db_path = os.path.join(os.path.dirname(__file__), "..", "databases", "database.db")
        if os.path.exists(db_path):
            try:
                admin_metrics["db_size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
                wal_path = db_path + "-wal"
                admin_metrics["db_wal_active"] = os.path.exists(wal_path)
            except Exception:
                pass

        telemetry["admin_diagnostics"] = admin_metrics
    else:
        # Regular user telemetry: Focused on user habits and productivity
        user_metrics = {
            "status": "Active Session",
            "time_of_day": "Morning" if now.hour < 12 else "Afternoon" if now.hour < 18 else "Evening"
        }
        telemetry["user_context"] = user_metrics

    return telemetry


def format_telemetry_prompt_block(telemetry):
    """Formats telemetry dictionary into clean system prompt context"""
    role = telemetry.get("role", "user")
    lines = [f"[System Telemetry Context - Role: {role.upper()}]"]

    if role == "admin" and "admin_diagnostics" in telemetry:
        diag = telemetry["admin_diagnostics"]
        lines.append(f"- Environment: {diag.get('os_environment', 'Container')}")
        if "cpu_load_percent" in diag:
            lines.append(f"- CPU Load: {diag['cpu_load_percent']}% | RAM: {diag.get('ram_used_gb', 0)}GB / {diag.get('ram_total_gb', 16)}GB ({diag.get('ram_percent', 0)}%)")
        if "db_size_mb" in diag:
            lines.append(f"- DB Size: {diag['db_size_mb']} MB (WAL Mode: {'Active' if diag.get('db_wal_active') else 'Standard'})")
    else:
        uctx = telemetry.get("user_context", {})
        lines.append(f"- User Session: {uctx.get('status', 'Active')}")
        lines.append(f"- Local Time Phase: {uctx.get('time_of_day', 'Day')}")

    return "\n".join(lines)
