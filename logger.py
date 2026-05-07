"""
logger.py — Writes metrics and alerts to a rotating log file.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup(log_path):
    """
    Note to others:
        The global logger. Call this ONCE at startup.
        Returns the logger instance.
    """
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("health_monitor")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

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
    Uses WARNING level for FIRED events, INFO for RESOLVED.
    """
    tag = "FIRED   " if event["status"] == "FIRED" else "RESOLVED"
    line = f"{tag} | {event['severity']:<8} | {event['message']}"
    if event["status"] == "FIRED":
        logger.warning(line)
    else:
        logger.info(line)
