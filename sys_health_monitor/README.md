# System Health Monitor

A real-time CLI tool that watches your computer's CPU, memory, disk, and network — alerts you when something looks wrong, and keeps a log of everything for later.

Think of it as a tiny, personal version of Datadog or Grafana. Built with Python.

---

## What it looks like

When you run it, you get a live, color-coded terminal dashboard that refreshes every 2 seconds. It shows three resource bars (CPU, memory, disk), a network section with upload/download rates, and a table of your top CPU-hogging processes. Bars are green when fine, yellow when stressed, red when in trouble.

When something goes critical, you'll see an alert event:

```
FIRED    CPU at 92% (>= 85% for 3 ticks)
```

When it recovers:

```
RESOLVED CPU recovered to 47%
```

---

## What it does

Three things, done well:

**1. Real-time monitoring dashboard.** Live gauges for CPU, memory, disk, and network. A table showing your top CPU-hogging processes. Color-coded so a glance tells you if you're fine, stressed, or in trouble.

**2. Smart alerts.** Instead of screaming every time CPU briefly spikes, it only fires when a problem is sustained — and then quietly stays silent until either the situation changes or a cooldown window expires. No spam.

**3. Historical logging.** Every reading and every alert is written to a rotating log file you can read with any text editor. The log auto-rotates so it can't fill your disk.

---

## Quick start

You need Python 3.9 or newer. That's it.

```
cd system-health-monitor

python -m venv .venv

source .venv/bin/activate           # macOS / Linux
.venv\Scripts\activate              # Windows

pip install -r requirements.txt

python monitor.py
```

Press Ctrl+C whenever you want to stop. The first run automatically creates a `logs/` folder for you.

---

## What's in this project

```
system-health-monitor/
  monitor.py          The main file. This is what you run.
  collector.py        Reads system stats using psutil.
  alerts.py           Decides when to fire/resolve alerts.
  dashboard.py        Draws the live dashboard.
  logger.py           Writes everything to logs/health.log.
  config.yaml         All your settings live here.
  requirements.txt    The libraries this project needs.
  logs/               Created on first run.
    health.log
```

Each file has one job. If you want to understand the project, read them in this order: config.yaml, monitor.py, collector.py, alerts.py, dashboard.py, logger.py.

---

## How it works

Every 2 seconds, in a loop:

1. Collect — collector.py asks the OS for current CPU, memory, disk, network, and process stats.
2. Evaluate — alerts.py checks if any value crossed a threshold and decides whether to fire or resolve an alert.
3. Display — dashboard.py redraws the screen with the new numbers.
4. Log — logger.py writes a line to logs/health.log with the snapshot, plus separate lines for any alerts.
5. Sleep — wait 2 seconds, repeat.

That's the whole architecture. One collector, multiple consumers (display, alerts, log).

---

## Configuration

Everything you might want to tweak is in config.yaml. No code changes needed — just edit and restart.

```
refresh_interval: 2          # seconds between checks

thresholds:
  cpu:
    warning: 70              # bar turns yellow at 70%
    critical: 85             # bar turns red AND alert fires at 85%
    sustained_ticks: 3       # but only after 3 ticks in a row
  memory:
    warning: 75
    critical: 90
    sustained_ticks: 3
  disk:
    warning: 80
    critical: 90
    sustained_ticks: 2

alert_cooldown_seconds: 60   # don't re-fire the same alert for 60s

log_file: "logs/health.log"
top_processes: 5             # how many processes to show
```

### What "sustained_ticks" means

This is the key feature. Say cpu.critical is 85 and sustained_ticks is 3.

- If CPU hits 95% for one second, then drops, no alert fires (probably just a brief blip).
- If CPU stays above 85% for 3 ticks in a row (about 6 seconds), the alert fires.

This kills 90% of false alarms.

### What "cooldown" means

Once an alert fires, it shuts up for alert_cooldown_seconds even if the problem continues. Without this, a sustained problem would spam your log every couple of seconds.

When the metric finally drops below threshold, you get one RESOLVED event so you know the fire is out.

---

## Reading the log

Open logs/health.log in any text editor, or use cat (macOS/Linux) or type (Windows):

```
2026-04-28 14:23:11 | INFO    | CPU 42.1% | MEM 78.3% (12042MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 12.4KB/s down 87.2KB/s
2026-04-28 14:23:13 | INFO    | CPU 44.0% | MEM 78.7% (12063MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 11.0KB/s down 72.4KB/s
2026-04-28 14:23:15 | INFO    | CPU 92.5% | MEM 79.1% (12091MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 10.7KB/s down 69.3KB/s
2026-04-28 14:23:17 | INFO    | CPU 95.1% | MEM 79.4% (12106MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 9.8KB/s down 68.0KB/s
2026-04-28 14:23:19 | INFO    | CPU 91.8% | MEM 79.6% (12118MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 10.2KB/s down 71.1KB/s
2026-04-28 14:23:19 | WARNING | FIRED    | CRITICAL | CPU at 91.8% (>= 85% for 3 ticks)
2026-04-28 14:23:21 | INFO    | CPU 43.2% | MEM 78.9% (12055MB/16384MB) | DISK 24.0% (119GB/500GB) | NET up 11.5KB/s down 80.3KB/s
2026-04-28 14:23:21 | INFO    | RESOLVED | INFO     | CPU recovered to 43.2%
```

The log file rotates automatically — when it hits 1MB, it becomes health.log.1 and a fresh health.log starts. The 5 most recent files are kept, older ones deleted. So your disk usage is capped at about 5MB no matter how long you run it.

---

## Want to see an alert fire?

The easiest way to demo all the features at once: open a few extra browser tabs, play a YouTube video in 4K, or run any heavy program. Memory will climb. After about 6 seconds of being above 90%, you'll see:

```
FIRED    MEMORY at 91.4% (>= 90% for 3 ticks)
```

Close the heavy apps, wait a couple ticks, and:

```
RESOLVED MEMORY recovered to 67.2%
```

That's the full alert lifecycle in 30 seconds.

---

## Tech stack

- **psutil** — Reads CPU, memory, disk, and network stats. Works the same on Windows, macOS, and Linux.
- **rich** — Makes the terminal dashboard pretty (colors, panels, tables).
- **PyYAML** — Reads the config.yaml file.
- **logging** (built-in) — Writes the rotating log file.

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'psutil'"**
You skipped the pip install step, or you're not in the virtual environment. Run `pip install -r requirements.txt` again.

**"Could not find config file: config.yaml"**
You're running monitor.py from a different folder. Make sure you cd into the project folder first.

**The dashboard looks plain (no colors or boxes)**
rich didn't install. The program falls back to a simpler ANSI-color view automatically. To get the full experience, run `pip install rich`.

**Numbers all show 0% or look stuck**
You're probably looking at the very first tick. CPU% needs two readings to compute (it measures the delta), so it might show 0 on the very first frame. The next tick will be accurate.

**On Windows: I don't see colors in CMD**
The default Windows command prompt has limited color support. Use Windows Terminal or PowerShell 7+ for the full color experience.

**The screen is flickering**
Some terminals don't handle the clear-and-redraw cleanly. Try a different terminal (Windows Terminal, iTerm2, modern GNOME Terminal). On slower machines, increase refresh_interval to 3 or 4 seconds in config.yaml.

---

