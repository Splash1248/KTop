"""
dashboard.py — Stable dashboard renderer for KTop
"""

import plotext as plt
import themes

from rich.live import Live
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align


# ==========================================
# CONSOLE
# ==========================================

_console = Console(color_system="truecolor")

_live_display = None


# ==========================================
# START LIVE
# ==========================================

def _ensure_live(layout):

    global _live_display

    if _live_display is None:

        _live_display = Live(
            layout,
            console=_console,
            refresh_per_second=4,
            screen=False,
            auto_refresh=False
        )

        _live_display.start()


# ==========================================
# STOP LIVE
# ==========================================

def stop():

    global _live_display

    if _live_display:

        _live_display.stop()
        _live_display = None


# ==========================================
# PLOT GENERATOR
# ==========================================

def _generate_plot_ansi(
    data,
    color,
    max_val=100,
    is_net=False,
    data2=None,
    color2=None
):

    plt.clf()

    plt.plotsize(40, 10)

    if is_net:

        plt.plot(
            data,
            color=color,
            marker="braille",
            label="Upload"
        )

        plt.plot(
            data2,
            color=color2,
            marker="braille",
            label="Download"
        )

    else:

        plt.plot(
            data,
            color=color,
            marker="braille"
        )

        plt.ylim(0, max_val)

    plt.theme("pro")

    return plt.build()


# ==========================================
# HEADER
# ==========================================

def _build_header(stats, theme):

    icons = theme["icons"]

    header = Text()

    header.append(
        f" {icons['system']} KTOP SYSTEM MONITOR ",
        style=theme["header"]
    )

    header.append(
        f"   {stats['timestamp']}   ↑ uptime: {stats['uptime']}",
        style=theme["dim"]
    )

    return Align.center(header)


# ==========================================
# PANEL BUILDER
# ==========================================

def _build_stat_panel(title, icon, value, plot, border, bg):

    plot_text = Text()

    if bg:

        plot_text.append_text(plot)
        plot_text.stylize(bg)

    else:

        plot_text = plot

    return Panel(
        plot_text,
        title=f"{icon} {title} ({value}%)",
        border_style=border,
        padding=(1, 2),
        expand=True,
        style=bg
    )


# ==========================================
# DRAW
# ==========================================

def _draw_rich(stats, events, engine):

    theme = themes.CURRENT_THEME

    icons = theme["icons"]

    bg = theme.get("panel_bg", "")

    cpu_status = engine.status(
        "cpu",
        stats["cpu_percent"]
    )

    mem_status = engine.status(
        "memory",
        stats["mem_percent"]
    )

    disk_status = engine.status(
        "disk",
        stats["disk_percent"]
    )

    # HEADER

    header = _build_header(stats, theme)

    # CPU PANEL

    cpu_plot = Text.from_ansi(
        _generate_plot_ansi(
            stats["history"]["cpu"],
            theme[cpu_status]
        )
    )

    cpu_panel = _build_stat_panel(
        "CPU",
        icons["cpu"],
        stats["cpu_percent"],
        cpu_plot,
        theme[cpu_status],
        bg
    )

    # MEMORY PANEL

    mem_plot = Text.from_ansi(
        _generate_plot_ansi(
            stats["history"]["mem"],
            theme[mem_status]
        )
    )

    mem_panel = _build_stat_panel(
        "MEMORY",
        icons["mem"],
        stats["mem_percent"],
        mem_plot,
        theme[mem_status],
        bg
    )

    # DISK PANEL

    disk_plot = Text.from_ansi(
        _generate_plot_ansi(
            stats["history"]["disk"],
            theme[disk_status]
        )
    )

    disk_panel = _build_stat_panel(
        "DISK",
        icons["disk"],
        stats["disk_percent"],
        disk_plot,
        theme[disk_status],
        bg
    )

    # NETWORK PANEL

    net_plot = Text.from_ansi(
        _generate_plot_ansi(
            stats["history"]["net_sent"],
            theme["network_up"],
            is_net=True,
            data2=stats["history"]["net_recv"],
            color2=theme["network_down"]
        )
    )

    if bg:
        net_plot.stylize(bg)

    net_panel = Panel(
        net_plot,
        title=(
            f"{icons['net']} NETWORK "
            f"(↑{stats['net_sent_kbs']}KB/s "
            f"↓{stats['net_recv_kbs']}KB/s)"
        ),
        border_style=theme["network_border"],
        padding=(1, 2),
        expand=True,
        style=bg
    )

    # GRID

    grid = Table.grid(expand=True)

    grid.add_column()
    grid.add_column()

    grid.add_row(cpu_panel, mem_panel)
    grid.add_row(disk_panel, net_panel)

    elements = [
        header,
        Text(),
        grid
    ]

    # PROCESS TABLE

    if stats["top_processes"]:

        proc_table = Table(
            show_header=True,
            header_style=theme["process_header"],
            border_style=theme["process_border"],
            expand=True
        )

        proc_table.add_column(
            "PID",
            justify="right",
            style=theme["dim"]
        )

        proc_table.add_column("Process")

        proc_table.add_column(
            "CPU %",
            justify="right",
            style=theme["crit"]
        )

        proc_table.add_column(
            "MEM %",
            justify="right",
            style=theme["ok"]
        )

        for p in stats["top_processes"]:

            proc_table.add_row(
                str(p["pid"]),
                p["name"],
                f"{p['cpu']:.1f}",
                f"{p['mem']:.1f}"
            )

        elements.append(
            Panel(
                proc_table,
                title="󰣇 TOP PROCESSES",
                border_style=theme["process_border"],
                padding=(1, 2),
                style=bg
            )
        )

    # ALERTS

    alerts_text = Text()

    if events:

        for e in events:

            if e["status"] == "FIRED":

                alerts_text.append(
                    f" ALERT    {e['message']}\n",
                    style=f"bold {theme['crit']}"
                )

            else:

                alerts_text.append(
                    f" RESOLVED {e['message']}\n",
                    style=f"bold {theme['ok']}"
                )

    else:

        alerts_text.append(
            "✓ All systems operating normally.\n",
            style=theme["ok"]
        )

    alerts_text.append(
        "\nCtrl+C to stop.",
        style=theme["dim"]
    )

    elements.append(
        Panel(
            alerts_text,
            border_style=theme["panel_border"],
            padding=(1, 2),
            style=bg
        )
    )

    # FINAL LAYOUT

    layout = Group(*elements)

    _ensure_live(layout)

    _live_display.update(layout, refresh=True)


# ==========================================
# PUBLIC DRAW
# ==========================================

def draw(stats, events, engine):

    _draw_rich(stats, events, engine)
