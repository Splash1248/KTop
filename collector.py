"""
collector.py — Reads a snapshot of system stats using psutil.
Now includes historical tracking for time-series graphs.
"""

import os
import time
import psutil
from datetime import datetime
from collections import deque

_DISK_PATH = os.path.abspath(os.sep)

_prev_net = None
_prev_net_time = None

# Store the last 50 data points for our graphs
_HISTORY_LEN = 50
_history = {
    "cpu": deque([0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN),
    "mem": deque([0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN),
    "disk": deque([0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN),
    "net_sent": deque([0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN),
    "net_recv": deque([0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN),
}

def prime():
    psutil.cpu_percent(interval=None)
    global _prev_net, _prev_net_time
    _prev_net = psutil.net_io_counters()
    _prev_net_time = time.time()

def _network_rate():
    global _prev_net, _prev_net_time
    now = psutil.net_io_counters()
    now_time = time.time()
    elapsed = now_time - _prev_net_time
    if elapsed <= 0: return 0.0, 0.0

    sent_kbs = (now.bytes_sent - _prev_net.bytes_sent) / elapsed / 1024
    recv_kbs = (now.bytes_recv - _prev_net.bytes_recv) / elapsed / 1024

    _prev_net = now
    _prev_net_time = now_time
    return round(sent_kbs, 1), round(recv_kbs, 1)

def _top_processes(limit=5):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            procs.append({
                "pid": info['pid'],
                "name": (info['name'] or "?")[:25],
                "cpu": info['cpu_percent'] or 0.0,
                "mem": round(info['memory_percent'] or 0.0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:limit]

def _uptime_string():
    seconds = int(time.time() - psutil.boot_time())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days: return f"{days}d {hours}h"
    if hours: return f"{hours}h {minutes}m"
    return f"{minutes}m"

def get_stats():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(_DISK_PATH)
    net_sent, net_recv = _network_rate()

    # Append newest data to our rolling history
    _history["cpu"].append(cpu)
    _history["mem"].append(mem.percent)
    _history["disk"].append(disk.percent)
    _history["net_sent"].append(net_sent)
    _history["net_recv"].append(net_recv)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": _uptime_string(),
        "cpu_percent": round(cpu, 1),
        "cpu_cores": psutil.cpu_count(logical=True),
        "mem_percent": mem.percent,
        "mem_used_mb": mem.used // (1024 ** 2),
        "mem_total_mb": mem.total // (1024 ** 2),
        "disk_percent": disk.percent,
        "disk_used_gb": disk.used // (1024 ** 3),
        "disk_total_gb": disk.total // (1024 ** 3),
        "net_sent_kbs": net_sent,
        "net_recv_kbs": net_recv,
        "top_processes": _top_processes(),
        "history": {
            "cpu": list(_history["cpu"]),
            "mem": list(_history["mem"]),
            "disk": list(_history["disk"]),
            "net_sent": list(_history["net_sent"]),
            "net_recv": list(_history["net_recv"]),
        }
    }
