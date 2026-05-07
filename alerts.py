"""
alerts.py — Threshold-based alerting with sustained-breach + cooldown.
"""

import time


class AlertEngine:
    def __init__(self, thresholds, cooldown_seconds):
        self.thresholds = thresholds
        self.cooldown = cooldown_seconds

        # Per-metric runtime state:
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
        Returns a list of event dicts. Each dict has the key values:
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
        """
        cfg = self.thresholds[metric]
        if value >= cfg["critical"]:
            return "crit"
        if value >= cfg["warning"]:
            return "warn"
        return "ok"
