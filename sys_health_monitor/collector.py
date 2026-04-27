"""
collector.py — Reads a snapshot of system stats using psutil.

Key design choices:
  • CPU reading is NON-BLOCKING. We warmup once with `prime()`, then every
    subsequent call uses interval=None which returns instantly (psutil
    computes % using the time delta since the last call internally).
  • Disk path is auto-detected so this works on Windows, macOS, and Linux.
  • Network bytes are tracked as a delta between calls (raw counters from
    psutil are cumulative since boot, which isn't useful on its own).
"""

import os
import time
import psutil
from datetime import datetime


# Pick a disk path that exists on every OS.
# On Linux/macOS this is "/", on Windows it's "C:\" (the system drive).
_DISK_PATH = os.path.abspath(os.sep)

# Module-level state for tracking deltas between calls.
# We need this because network and CPU stats are cumulative — to get a
# "per second" rate, we have to remember the previous reading.
_prev_net = None
_prev_net_time = None


def prime():
    """
    Warmup call. Run ONCE at startup before the main loop.

    psutil.cpu_percent() needs two readings to compute a percentage
    (it measures the delta between them). The first call always returns
    0.0 or a meaningless number. By priming, we make sure the first
    real tick in the main loop returns a valid CPU%.
    """
    psutil.cpu_percent(interval=None)
    global _prev_net, _prev_net_time
    _prev_net = psutil.net_io_counters()
    _prev_net_time = time.time()


def _network_rate():
    """
    Compute network bytes/sec since the last call.
    Returns (sent_per_sec, recv_per_sec) in KB/s.
    """
    global _prev_net, _prev_net_time
    now = psutil.net_io_counters()
    now_time = time.time()

    elapsed = now_time - _prev_net_time
    if elapsed <= 0:                         # avoid division-by-zero
        return 0.0, 0.0

    sent_kbs = (now.bytes_sent - _prev_net.bytes_sent) / elapsed / 1024
    recv_kbs = (now.bytes_recv - _prev_net.bytes_recv) / elapsed / 1024

    _prev_net = now
    _prev_net_time = now_time
    return round(sent_kbs, 1), round(recv_kbs, 1)


def _top_processes(limit=5):
    """
    Return the top N processes by CPU usage.
    Each entry is a dict with name, pid, cpu%, memory%.
    """
    procs = []
    # cpu_percent() on individual processes also needs a prime read,
    # but we accept first-tick inaccuracy here — it self-corrects.
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            procs.append({
                "pid": info['pid'],
                "name": (info['name'] or "?")[:25],   # trim long names
                "cpu": info['cpu_percent'] or 0.0,
                "mem": round(info['memory_percent'] or 0.0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process died mid-iteration, or we don't have permission.
            # Skip it silently — this is normal.
            continue

    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:limit]


def _uptime_string():
    """Pretty uptime like '3h 12m' or '2d 4h'."""
    seconds = int(time.time() - psutil.boot_time())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def get_stats():
    """
    Collect a snapshot of current system stats.
    Returns a dictionary with CPU, memory, disk, network, and processes.
    """
    cpu = psutil.cpu_percent(interval=None)            # non-blocking now
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(_DISK_PATH)
    net_sent, net_recv = _network_rate()

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
    }
