"""
logger.py — Writes metrics and alerts to a rotating log file.

Improvements over the previous version:
  • Creates the log directory automatically (no more FileNotFoundError
    on a fresh clone).
  • Uses RotatingFileHandler so the log can't grow forever — when it
    hits 1MB, it rolls over and keeps the last 5 files (~5MB total).
  • Path is configurable, not hardcoded.
  • Structured event logging for the new alert engine.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup(log_path):
    """
    Configure the global logger. Call this ONCE at startup.
    Returns the configured logger instance.
    """
    # 1. Make sure the directory exists. exist_ok=True means "don't
    #    crash if it's already there". This single line is what fixes
    #    the FileNotFoundError on first run.
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("health_monitor")
    logger.setLevel(logging.INFO)

    # Avoid attaching duplicate handlers if setup() is called twice.
    if logger.handlers:
        return logger

    # 2. Rotating handler: when the file hits maxBytes, rename it to
    #    health.log.1, start a fresh health.log. Keep up to backupCount
    #    old files. Total disk usage capped at ~5 MB.
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,        # 1 MB per file
        backupCount=5,             # keep 5 old files
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger


def log_stats(logger, stats):
    """Write a one-line stats snapshot at INFO level."""
    logger.info(
        f"CPU {stats['cpu_percent']:>5.1f}% | "
        f"MEM {stats['mem_percent']:>5.1f}% "
        f"({stats['mem_used_mb']}MB/{stats['mem_total_mb']}MB) | "
        f"DISK {stats['disk_percent']:>5.1f}% "
        f"({stats['disk_used_gb']}GB/{stats['disk_total_gb']}GB) | "
        f"NET ↑{stats['net_sent_kbs']}KB/s ↓{stats['net_recv_kbs']}KB/s"
    )


def log_event(logger, event):
    """
    Write a structured alert event.
    Uses WARNING level for FIRED events, INFO for RESOLVED.
    """
    tag = "🔥 FIRED   " if event["status"] == "FIRED" else "✅ RESOLVED"
    line = f"{tag} | {event['severity']:<8} | {event['message']}"
    if event["status"] == "FIRED":
        logger.warning(line)
    else:
        logger.info(line)
