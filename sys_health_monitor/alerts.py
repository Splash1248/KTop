"""
alerts.py — Threshold-based alerting with sustained-breach + cooldown.

The naive approach (old version) fires an alert every single tick a
metric is over threshold. If memory stays at 85% for a minute, you
get 30 alerts. That's spam, not signal.

This version uses TWO mechanisms to be quiet but useful:

  1. Sustained breach
     A metric must be over the critical threshold for N CONSECUTIVE
     ticks before an alert fires. Single-tick spikes are ignored.

  2. Cooldown
     After an alert fires, the same alert is suppressed for
     `cooldown_seconds` seconds — even if the breach continues.

When the metric returns to normal, ONE "resolved" event is emitted
so you know the situation is over.
"""

import time


class AlertEngine:
    """Tracks per-metric breach state across ticks."""

    def __init__(self, thresholds, cooldown_seconds):
        """
        thresholds: dict like {"cpu": {"critical": 85, "sustained_ticks": 3}, ...}
        cooldown_seconds: int, e.g. 60
        """
        self.thresholds = thresholds
        self.cooldown = cooldown_seconds

        # Per-metric runtime state.
        # breach_count    → how many consecutive ticks over threshold
        # last_alert_at   → unix time the last alert fired (for cooldown)
        # firing          → True if we've fired and not yet resolved
        self._state = {
            metric: {"breach_count": 0, "last_alert_at": 0, "firing": False}
            for metric in thresholds
        }

    # Map metric keys to the field name in the stats dict.
    _METRIC_FIELDS = {
        "cpu": "cpu_percent",
        "memory": "mem_percent",
        "disk": "disk_percent",
    }

    def evaluate(self, stats):
        """
        Run all metrics through threshold logic for one tick.

        Returns a list of event dicts. Each event has:
          severity : "CRITICAL" or "INFO"
          metric   : "cpu" / "memory" / "disk"
          value    : current reading
          status   : "FIRED" or "RESOLVED"
          message  : human-readable string
        """
        events = []
        now = time.time()

        for metric, cfg in self.thresholds.items():
            field = self._METRIC_FIELDS[metric]
            value = stats[field]
            state = self._state[metric]

            over_critical = value >= cfg["critical"]

            if over_critical:
                state["breach_count"] += 1
                # Fire if: breach has lasted long enough AND we're not in cooldown.
                cooldown_ok = (now - state["last_alert_at"]) >= self.cooldown
                long_enough = state["breach_count"] >= cfg["sustained_ticks"]

                if long_enough and cooldown_ok:
                    state["last_alert_at"] = now
                    state["firing"] = True
                    events.append({
                        "severity": "CRITICAL",
                        "metric": metric,
                        "value": value,
                        "status": "FIRED",
                        "message": (
                            f"{metric.upper()} at {value}% "
                            f"(>= {cfg['critical']}% for "
                            f"{state['breach_count']} ticks)"
                        ),
                    })
            else:
                # Metric is back below threshold. If we were firing, resolve it.
                if state["firing"]:
                    events.append({
                        "severity": "INFO",
                        "metric": metric,
                        "value": value,
                        "status": "RESOLVED",
                        "message": f"{metric.upper()} recovered to {value}%",
                    })
                    state["firing"] = False
                state["breach_count"] = 0    # reset the breach counter

        return events

    def status(self, metric, value):
        """
        Classify a value as 'ok' / 'warn' / 'crit' for dashboard coloring.
        Pure read — does not affect alert state.
        """
        cfg = self.thresholds[metric]
        if value >= cfg["critical"]:
            return "crit"
        if value >= cfg["warning"]:
            return "warn"
        return "ok"
