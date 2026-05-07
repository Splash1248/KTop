"""
themes.py — Stable clean themes for KTOP
"""

THEMES = {

    "catppuccin": {
        "header":           "bold white on #1e1e2e",

        "ok":               "#a6e3a1",
        "warn":             "#f9e2af",
        "crit":             "#f38ba8",

        "dim":              "#585b70",

        "network_up":       "#cba6f7",
        "network_down":     "#89dceb",

        "network_border":   "#89b4fa",

        "process_header":   "bold #89b4fa",
        "process_border":   "#45475a",

        "panel_border":     "#313244",
        "panel_bg":         "on #181825",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    },

    "tokyo_night": {
        "header":           "bold #c0caf5 on #16161e",

        "ok":               "#9ece6a",
        "warn":             "#e0af68",
        "crit":             "#f7768e",

        "dim":              "#565f89",

        "network_up":       "#bb9af7",
        "network_down":     "#7dcfff",

        "network_border":   "#3d59a1",

        "process_header":   "bold #7aa2f7",
        "process_border":   "#292e42",

        "panel_border":     "#1f2335",
        "panel_bg":         "on #16161e",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    },

    "dracula": {
        "header":           "bold #f8f8f2 on #282a36",

        "ok":               "#50fa7b",
        "warn":             "#f1fa8c",
        "crit":             "#ff5555",

        "dim":              "#6272a4",

        "network_up":       "#ff79c6",
        "network_down":     "#8be9fd",

        "network_border":   "#bd93f9",

        "process_header":   "bold #bd93f9",
        "process_border":   "#44475a",

        "panel_border":     "#44475a",
        "panel_bg":         "on #21222c",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    },

    "cyberpunk": {
        "header":           "bold #00ffff on #0a0a0f",

        "ok":               "#39ff14",
        "warn":             "#ffdd00",
        "crit":             "#ff003c",

        "dim":              "#444466",

        "network_up":       "#ff00ff",
        "network_down":     "#00e5ff",

        "network_border":   "#ff00ff",

        "process_header":   "bold #00e5ff",
        "process_border":   "#ff00ff",

        "panel_border":     "#220033",
        "panel_bg":         "on #0a0014",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    },

    "matrix": {
        "header":           "bold #00ff41 on #0d0d0d",

        "ok":               "#00ff41",
        "warn":             "#aaff00",
        "crit":             "#ff4444",

        "dim":              "#1a4a1a",

        "network_up":       "#00cc33",
        "network_down":     "#00ff99",

        "network_border":   "#003300",

        "process_header":   "bold #00ff41",
        "process_border":   "#003300",

        "panel_border":     "#001a00",
        "panel_bg":         "on #060d06",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    },

    "oled": {
        "header":           "bold #e0e0e0 on #000000",

        "ok":               "#80ff80",
        "warn":             "#ffdd66",
        "crit":             "#ff6060",

        "dim":              "#404040",

        "network_up":       "#cc88ff",
        "network_down":     "#66ddff",

        "network_border":   "#303030",

        "process_header":   "bold #cccccc",
        "process_border":   "#222222",

        "panel_border":     "#1a1a1a",
        "panel_bg":         "on #000000",

        "icons": {
            "system": "󰍛",
            "cpu":    "󰻠",
            "mem":    "󰘚",
            "disk":   "󰋊",
            "net":    "󰖩"
        }
    }
}

CURRENT_THEME = THEMES["catppuccin"]