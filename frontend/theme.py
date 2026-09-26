"""Shared colors + fonts (one place to restyle the whole app)."""
import sys

BG      = "#1e2030"   # left panel
PANEL   = "#262a3d"   # inputs / lists / editor
SURFACE = "#1a1c29"   # right panel background
FG      = "#e6e8f2"
MUTED   = "#8b91a8"
ACCENT  = "#5b8cff"

UI_FONT   = "Segoe UI" if sys.platform.startswith("win") else "DejaVu Sans"
MONO_FONT = "Consolas"  if sys.platform.startswith("win") else "DejaVu Sans Mono"