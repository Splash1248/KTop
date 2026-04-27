"""
monitor.py — Entry point. Wires collector → alerts → dashboard → logger.

Reads config from config.yaml, primes the collector, then loops:
  collect → evaluate alerts → draw → log → sleep.
"""

import time
import yaml

import collector
import logger as log_module
from alerts import AlertEngine
from dashboard import draw


def load_config(path="config.yaml"):
    """Load the YAML config. Plain dict, no validation framework needed."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Could not find config file: {path}")
        print("   Make sure config.yaml exists in the same folder as monitor.py")
        raise SystemExit(1)
    except yaml.YAMLError as e:
        print(f"❌ config.yaml has a syntax error:\n   {e}")
        raise SystemExit(1)


def main():
    cfg = load_config()

    # Set up the rotating logger using the path from config.
    log = log_module.setup(cfg["log_file"])

    # Build the alert engine with thresholds from config.
    engine = AlertEngine(
        thresholds=cfg["thresholds"],
        cooldown_seconds=cfg["alert_cooldown_seconds"],
    )

    print("Starting System Health Monitor…")
    print("Priming collector (first CPU reading takes a moment)…")
    collector.prime()
    time.sleep(1)                    # let psutil populate its first delta

    tick_count = 0
    alert_count = 0
    started_at = time.time()

    try:
        while True:
            tick_count += 1

            # 1. Collect a snapshot
            stats = collector.get_stats()

            # 2. Run threshold logic (returns FIRED/RESOLVED events)
            events = engine.evaluate(stats)
            alert_count += sum(1 for e in events if e["status"] == "FIRED")

            # 3. Draw the dashboard
            draw(stats, events, engine)

            # 4. Persist
            log_module.log_stats(log, stats)
            for event in events:
                log_module.log_event(log, event)

            # 5. Sleep until the next tick
            time.sleep(cfg["refresh_interval"])

    except KeyboardInterrupt:
        # Wrapped in its own try so an impatient second Ctrl+C
        # doesn't produce a scary traceback during shutdown.
        try:
            elapsed = int(time.time() - started_at)
            mins, secs = divmod(elapsed, 60)
            print("\n\n──────────────────────────────────────────")
            print("  Monitor stopped.")
            print(f"  Ran for {mins}m {secs}s | {tick_count} ticks "
                  f"| {alert_count} alerts fired")
            print(f"  Log file: {cfg['log_file']}")
            print("──────────────────────────────────────────")
        except KeyboardInterrupt:
            print("\nForced exit.")


if __name__ == "__main__":
    main()
