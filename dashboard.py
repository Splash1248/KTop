"""
dashboard.py — Renders the live dashboard.
Now uses rich.live to eliminate flickering!
"""

import os

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    import plotext as plt
    _HAS_RICH_AND_PLT = True
    _console = Console()
    _live_display = None
except ImportError:
    _HAS_RICH_AND_PLT = False

def _clear():
    os.system("cls" if os.name == "nt" else "clear")

_COLORS = {"ok": "green", "warn": "yellow", "crit": "red"}

def _generate_plot_ansi(data, color, max_val=100, is_net=False, data2=None, color2=None):
    plt.clf()
    plt.plotsize(40, 10)
    if is_net:
        plt.plot(data, color=color, marker="braille", label="Up (KB/s)")
        plt.plot(data2, color=color2, marker="braille", label="Down (KB/s)")
    else:
        plt.plot(data, color=color, marker="braille")
        plt.ylim(0, max_val)
    plt.theme('clear')
    return plt.build()

def _draw_rich(stats, events, engine):
    global _live_display

    cpu_status = engine.status("cpu", stats["cpu_percent"])
    mem_status = engine.status("memory", stats["mem_percent"])
    disk_status = engine.status("disk", stats["disk_percent"])

    header = Text()
    header.append("  SYSTEM HEALTH MONITOR  ", style="bold white on blue")
    header.append(f"   {stats['timestamp']}   ↑ uptime: {stats['uptime']}", style="dim")

    cpu_plot = Text.from_ansi(_generate_plot_ansi(stats["history"]["cpu"], _COLORS[cpu_status]))
    cpu_panel = Panel(cpu_plot, title=f"CPU ({stats['cpu_percent']}%)", border_style=_COLORS[cpu_status])

    mem_plot = Text.from_ansi(_generate_plot_ansi(stats["history"]["mem"], _COLORS[mem_status]))
    mem_panel = Panel(mem_plot, title=f"MEM ({stats['mem_percent']}%)", border_style=_COLORS[mem_status])

    disk_plot = Text.from_ansi(_generate_plot_ansi(stats["history"]["disk"], _COLORS[disk_status]))
    disk_panel = Panel(disk_plot, title=f"DISK ({stats['disk_percent']}%)", border_style=_COLORS[disk_status])

    net_plot = Text.from_ansi(_generate_plot_ansi(
        stats["history"]["net_sent"], "red",
        is_net=True, data2=stats["history"]["net_recv"], color2="cyan"
    ))
    net_panel = Panel(net_plot, title=f"NET (↑{stats['net_sent_kbs']}KB/s ↓{stats['net_recv_kbs']}KB/s)", border_style="blue")

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()
    grid.add_row(cpu_panel, mem_panel)
    grid.add_row(disk_panel, net_panel)

    elements = [header, Text(), grid]

    if stats["top_processes"]:
        proc_table = Table(show_header=True, header_style="bold cyan", border_style="cyan", expand=True)
        proc_table.add_column("PID", justify="right", style="dim")
        proc_table.add_column("Name")
        proc_table.add_column("CPU %", justify="right", style="red")
        proc_table.add_column("MEM %", justify="right", style="green")
        for p in stats["top_processes"]:
            proc_table.add_row(str(p["pid"]), p["name"], f"{p['cpu']:.1f}", f"{p['mem']:.1f}")
        elements.append(Panel(proc_table, title="Top Processes", border_style="cyan"))

    alerts_text = Text()
    if events:
        for e in events:
            style = "red bold" if e["status"] == "FIRED" else "green bold"
            tag = "🔥 FIRED   " if e["status"] == "FIRED" else "✅ RESOLVED"
            alerts_text.append(f"[{style}]{tag}[/] {e['message']}\n")
    else:
        alerts_text.append("✓ All systems normal.\n", style="green")
    alerts_text.append("\nPress Ctrl+C to stop.", style="dim")

    elements.append(alerts_text)
    layout = Group(*elements)

    if _live_display is None:
        _live_display = Live(layout, console=_console, refresh_per_second=4)
        _live_display.start()
    else:
        _live_display.update(layout)

def _draw_plain(stats, events, engine):
    _clear()
    print("=" * 60)
    print("Please install 'rich' and 'plotext' for the graph dashboard.")
    print("pip install -r requirements.txt")
    print("=" * 60)

def draw(stats, events, engine):
    if _HAS_RICH_AND_PLT:
        _draw_rich(stats, events, engine)
    else:
        _draw_plain(stats, events, engine)

def stop():
    """Stops the Live display so the terminal un-blocks correctly."""
    global _live_display
    if _HAS_RICH_AND_PLT and _live_display is not None:
        _live_display.stop()
