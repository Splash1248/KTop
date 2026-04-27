"""
dashboard.py — Renders the live dashboard.

Tries to use the `rich` library for a polished UI (gauges, panels,
process table). If `rich` isn't installed, falls back to a plain
ANSI version (the old style, but with the cross-platform clear bug
fixed).
"""

import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.text import Text
    _HAS_RICH = True
    _console = Console()
except ImportError:
    _HAS_RICH = False


# Cross-platform screen clear. The old version used `os.system('clear')`
# which silently does nothing on Windows. `cls` is the Windows equivalent.
def _clear():
    os.system("cls" if os.name == "nt" else "clear")


# Map our internal status keys to terminal color names.
_COLORS = {"ok": "green", "warn": "yellow", "crit": "red"}


# ─────────────────────────────────────────────────────────────
#  Rich version (preferred)
# ─────────────────────────────────────────────────────────────

def _draw_rich(stats, events, engine):
    _clear()

    cpu_status = engine.status("cpu", stats["cpu_percent"])
    mem_status = engine.status("memory", stats["mem_percent"])
    disk_status = engine.status("disk", stats["disk_percent"])

    # Header panel
    header = Text()
    header.append("  SYSTEM HEALTH MONITOR  ", style="bold white on blue")
    header.append(f"   {stats['timestamp']}", style="dim")
    header.append(f"   ↑ uptime: {stats['uptime']}", style="dim")
    _console.print(header)
    _console.print()

    # Metrics table with bars
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", style="bold")
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_column(justify="left", style="dim")

    def row(label, pct, status, detail):
        bar_len = 30
        filled = int(pct / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        bar_text = Text(bar, style=_COLORS[status])
        pct_text = Text(f"{pct:>5.1f}%", style=_COLORS[status] + " bold")
        table.add_row(label, bar_text, pct_text, detail)

    row("CPU",  stats["cpu_percent"],  cpu_status,
        f"{stats['cpu_cores']} cores")
    row("MEM",  stats["mem_percent"],  mem_status,
        f"{stats['mem_used_mb']} / {stats['mem_total_mb']} MB")
    row("DISK", stats["disk_percent"], disk_status,
        f"{stats['disk_used_gb']} / {stats['disk_total_gb']} GB")

    _console.print(Panel(table, title="Resources", border_style="cyan"))

    # Network panel
    net_text = (
        f"  ↑ {stats['net_sent_kbs']:>8.1f} KB/s sent     "
        f"↓ {stats['net_recv_kbs']:>8.1f} KB/s received"
    )
    _console.print(Panel(net_text, title="Network", border_style="cyan"))

    # Top processes table
    if stats["top_processes"]:
        proc_table = Table(show_header=True, header_style="bold cyan",
                           border_style="cyan")
        proc_table.add_column("PID", justify="right", width=8)
        proc_table.add_column("Name", width=25)
        proc_table.add_column("CPU %", justify="right", width=8)
        proc_table.add_column("MEM %", justify="right", width=8)
        for p in stats["top_processes"]:
            proc_table.add_row(
                str(p["pid"]),
                p["name"],
                f"{p['cpu']:.1f}",
                f"{p['mem']:.1f}",
            )
        _console.print(Panel(proc_table, title="Top Processes",
                             border_style="cyan"))

    # Recent alert events for THIS tick
    if events:
        for e in events:
            style = "red bold" if e["status"] == "FIRED" else "green bold"
            tag = "🔥 FIRED   " if e["status"] == "FIRED" else "✅ RESOLVED"
            _console.print(f"[{style}]{tag}[/] {e['message']}")
    else:
        _console.print("[green]✓ All systems normal.[/]")

    _console.print()
    _console.print("[dim]Press Ctrl+C to stop.[/]")


# ─────────────────────────────────────────────────────────────
#  Fallback version (works without rich)
# ─────────────────────────────────────────────────────────────

def _ansi(text, color):
    codes = {"green": "92", "yellow": "93", "red": "91"}
    return f"\033[{codes[color]}m{text}\033[0m"


def _bar(pct, width=30):
    filled = int(pct / 100 * width)
    return "[" + "#" * filled + " " * (width - filled) + "]"


def _draw_plain(stats, events, engine):
    _clear()
    print("=" * 60)
    print("       SYSTEM HEALTH MONITOR")
    print(f"       {stats['timestamp']}   uptime: {stats['uptime']}")
    print("=" * 60)

    for label, key, metric in [
        ("CPU ", "cpu_percent", "cpu"),
        ("MEM ", "mem_percent", "memory"),
        ("DISK", "disk_percent", "disk"),
    ]:
        pct = stats[key]
        c = _COLORS[engine.status(metric, pct)]
        print(f"{label} {_ansi(_bar(pct), c)}  {_ansi(f'{pct:5.1f}%', c)}")

    print(f"\nNET   ↑ {stats['net_sent_kbs']} KB/s   ↓ {stats['net_recv_kbs']} KB/s")
    print("-" * 60)
    if events:
        for e in events:
            tag = "FIRED   " if e["status"] == "FIRED" else "RESOLVED"
            color = "red" if e["status"] == "FIRED" else "green"
            print(_ansi(f"[{tag}] {e['message']}", color))
    else:
        print(_ansi("All systems normal.", "green"))
    print("-" * 60)
    print("Press Ctrl+C to stop.")


# ─────────────────────────────────────────────────────────────
#  Public entrypoint
# ─────────────────────────────────────────────────────────────

def draw(stats, events, engine):
    """Render one frame of the dashboard."""
    if _HAS_RICH:
        _draw_rich(stats, events, engine)
    else:
        _draw_plain(stats, events, engine)
