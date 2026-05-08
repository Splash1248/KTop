"""
monitor.py — Entry point. Wires collector → alerts → dashboard → logger.
"""

import time
import yaml

import collector
import logger as log_module
from alerts import AlertEngine
from dashboard import draw, stop


def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Could not find config file: {path}")
        print("Make sure config.yaml exists in the same folder as monitor.py")
        raise SystemExit(1)
    except yaml.YAMLError as e:
        print(f"config.yaml has a syntax error:\n   {e}")
        raise SystemExit(1)


def main():
    cfg = load_config()

    log = log_module.setup(cfg["log_file"])

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

            stats = collector.get_stats()

            events = engine.evaluate(stats)
            alert_count += sum(1 for e in events if e["status"] == "FIRED")

            draw(stats, events, engine)

            log_module.log_stats(log, stats)
            for event in events:
                log_module.log_event(log, event)

            time.sleep(cfg["refresh_interval"])

    except KeyboardInterrupt:
        try:
            stop()
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
