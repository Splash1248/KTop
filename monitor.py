# monitor.py
"""
monitor.py — Entry point. Wires collector → alerts → dashboard → logger.

Reads config from config.yaml, primes the collector, then loops:
  collect → evaluate alerts → draw → log → sleep.
"""
import time
import yaml
import argparse

import collector
import logger as log_module
import themes

from alerts import AlertEngine
from dashboard import draw, stop


# ==========================================
# CONFIG LOADER
# ==========================================

def load_config(path="config.yaml"):

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ==========================================
# MAIN
# ==========================================

def main():

    parser = argparse.ArgumentParser(
        description="KTOP System Monitor"
    )

    parser.add_argument(
        "--theme",
        type=str,
        default="catppuccin",
        help="Theme name"
    )

    args = parser.parse_args()

    # ==========================================
    # VALIDATE THEME
    # ==========================================

    if args.theme not in themes.THEMES:

        print(f"\nUnknown theme: {args.theme}\n")

        print("Available themes:\n")
        print("  - catppuccin")
        print("  - tokyo_night")
        print("  - dracula")
        print("  - cyberpunk")
        print("  - matrix")
        print("  - oled")

        return

    # APPLY THEME

    themes.CURRENT_THEME = themes.THEMES[args.theme]

    # ==========================================
    # STARTUP INFO
    # ==========================================

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("        KTOP SYSTEM MONITOR")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print(f"\nLoaded theme: {args.theme}")

    print("\nAvailable themes:")
    print("  - catppuccin")
    print("  - tokyo_night")
    print("  - dracula")
    print("  - cyberpunk")
    print("  - matrix")
    print("  - oled")

    print("\nExample:")
    print("  python3 monitor.py --theme dracula")

    print("\nPress Ctrl+C to stop.\n")

    # ==========================================
    # LOAD CONFIG
    # ==========================================

    cfg = load_config()

    log = log_module.setup(cfg["log_file"])

    engine = AlertEngine(
        thresholds=cfg["thresholds"],
        cooldown_seconds=cfg["alert_cooldown_seconds"],
    )

    # PRIME CPU %

    collector.prime()

    tick_count = 0
    alert_count = 0

    started_at = time.time()

    # ==========================================
    # MAIN LOOP
    # ==========================================

    try:

        while True:

            tick_count += 1

            # COLLECT STATS

            stats = collector.get_stats()

            # ALERTS

            events = engine.evaluate(stats)

            alert_count += sum(
                1 for e in events
                if e["status"] == "FIRED"
            )

            # DRAW

            draw(stats, events, engine)

            # LOGGING

            log_module.log_stats(log, stats)

            for event in events:
                log_module.log_event(log, event)

            # REFRESH

            time.sleep(cfg["refresh_interval"])

    except KeyboardInterrupt:

        stop()

        elapsed = int(time.time() - started_at)

        mins, secs = divmod(elapsed, 60)

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("           KTOP STOPPED")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        print(f"\nRuntime: {mins}m {secs}s")
        print(f"Ticks: {tick_count}")
        print(f"Alerts Fired: {alert_count}")
        print(f"Log File: {cfg['log_file']}")

        print("\nGoodbye.\n")


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()
