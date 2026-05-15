# Project State

## Current Status

TaskKiller 3000 — stable. Procedural terminal-style global operations panel active. Runtime Inspector (v3) with unified Node.js + Python process inspection. No external UI dependencies beyond psutil.

## Architecture

- Single-file tkinter application (`port_manager.py`)
- Windows-focused, Python 3.10+
- psutil optional for Port Scanner (falls back to `tasklist`), required for Runtime Inspector
- No external UI frameworks — ops panel is entirely procedural tkinter Canvas
- GitHub Actions configured (Claude PR assistant + code review)
- `DevProcessInspector` base class → `NodeInspector`, `PythonInspector` subclasses
- `RuntimeInspectorPanel` collects from all inspectors and merges into one table
- `ProcessInfo` dataclass carries `runtime` and `venv` fields alongside existing data

### Root Layout

```
root
└── _outer (horizontal Frame, fills root)
    ├── ops_panel  (210px, side=left, fill=y — persistent across all tabs)
    │   ├── Header Canvas (210×68px)
    │   │   ├── "TASKKILLER 3000" — Canvas text, Consolas 13pt bold green
    │   │   ├── "RUNTIME OPS MONITOR" — dim subtitle
    │   │   └── Scan line — 1px horizontal, ~22fps via after()
    │   ├── OPS CONSOLE label (ghost marker, ~invisible)
    │   ├── Separator
    │   ├── Telemetry metrics (NODE.JS ●, PYTHON ●, PORTS ACTIVE, ORPHANED ●)
    │   ├── Separator
    │   ├── AUTO-REFRESH, LAST SCAN
    │   ├── Separator
    │   ├── RUNTIME MON
    │   ├── Spacer (expand)
    │   ├── Radar Canvas (210×168px)
    │   │   ├── Static: 4 concentric rings, crosshairs, 30° tick marks
    │   │   ├── Sweep: rotating line, 2°/frame, ~12fps via after()
    │   │   ├── Trail: 22-step afterglow behind sweep
    │   │   └── Blips: random seeds at sweep tip, exponential fade
    │   └── ENGINE label (psutil version, anchored bottom)
    ├── 1px vertical separator
    └── right_area (expand=True)
          ├── status bar  (side=bottom, global — colored dot + status text)
          └── ttk.Notebook
                ├── Port Scanner tab
                └── Runtime Inspector tab
```

## Completed Features

### Global Ops Panel (persistent, left side)
- **Header Canvas** — "TASKKILLER 3000" + "RUNTIME OPS MONITOR" as Canvas text items
- **Scan line** — 1px horizontal line scrolls top-to-bottom at ~22fps; single `coords()` update per frame
- **Telemetry metrics** — NODE.JS, PYTHON, PORTS ACTIVE, ORPHANED, AUTO-REFRESH, LAST SCAN, RUNTIME MON, ENGINE
- **Indicator dots** — `●` next to NODE.JS (green), PYTHON (blue), ORPHANED (yellow); each blinks independently at random 1600–2800ms intervals; never sync
- **Procedural radar Canvas** — 210×168px:
  - 4 concentric rings, crosshairs, 30° tick marks — static, drawn once
  - Rotating sweep at 2°/frame, ~12fps → 1 revolution every ~15s
  - 22-step afterglow trail (linear brightness decay behind sweep)
  - Blip seeding at 4% chance/frame, exponential fade (×0.93/frame)
  - All animation via `after(82, ...)` — no threads, negligible CPU
- Ops panel persists across Port Scanner ↔ Runtime Inspector tab switches

### Port Scanner (Tab 1)
- Port lookup via `netstat -ano`
- LISTENING process detection (ignores ESTABLISHED browser sessions)
- Process verification (name, exe path, command line, status)
- Safe termination workflow with confirmation dialog
- Manual port entry + Enter key shortcut
- Multi-port scanner dashboard (8 ports, single netstat pass, ttk.Treeview)
- Process classification labels (Node.js, Python, Ollama, Docker, Java, Electron, Bun, Browser, Unknown)
- Protected process safety — hard blocks kill on 16 critical Windows processes
- Kill all `node.exe` processes shortcut
- Auto-refresh scanner (5s, toggle checkbox)
- Open port in default browser
- Kill success auto-refreshes scanner
- Dark theme with color-coded log output
- Activity log: `spacing1=2, spacing3=2` breathing room; dimmer timestamps; ACTIVITY LOG label; `─` separators

### Runtime Inspector (Tab 2)
- Unified table: Node.js (green) and Python (blue) processes in one view
- Columns: Runtime, PID, PPID, Status, Port(s), CPU%, RAM MB, Project, Script, Working Dir
- Sortable columns (click heading)
- Detects orphaned processes (parent PID no longer exists) — shown in amber
- Detects zombie processes (psutil status == zombie) — shown in red
- Detects parent/child process relationships (shows child PIDs in detail panel)
- Node.js: 24 script type patterns (Vite, Next.js, MCP Server, Nodemon, Electron, etc.)
- Python: 20 script type patterns (Uvicorn, Flask, Streamlit, Gradio, Jupyter, Django, Celery, etc.)
- Python filter: only surfaces processes with listening ports or a recognized dev pattern
- Python venv detection: walks up from exe looking for pyvenv.cfg, falls back to path component matching
- Project name: Node → package.json; Python → pyproject.toml, setup.cfg, package.json, folder name
- Process detail panel: runtime, status, PID/PPID, children, ports, CPU, RAM, venv, project, cwd, exe, full cmdline, warnings
- Safe Stop (graceful taskkill, no /F) + Force Kill with confirmation dialogs
- Kill All Node shortcut in both tabs
- Auto-refresh (3s, toggle checkbox); CPU% tracks across refreshes
- Port map via psutil.net_connections() with netstat fallback
- Tab lazy-loads on first visit; kills refresh Port Scanner automatically
- Per-runtime row background tints: green wash (Node), blue wash (Python), amber (orphaned), red (zombie)
- Button toolbar separator between Safe Stop and Force Kill groups

### Global UI
- Status bar: colored dot indicator (● green/yellow/red) + status text — persistent bottom bar
- Dark theme: `BG_DARK="#1e1e1e"`, `BG_PANEL="#252526"`, `BG_OUTPUT="#0f0f0f"`, `BG_TELEM="#1c1c1d"`

### DevProcessInspector Framework
- `DevProcessInspector` base class: PROCESS_NAMES, SCRIPT_PATTERNS, RUNTIME_LABEL, DEFAULT_LABEL
- Override: `should_include()`, `_detect_project()`, `_detect_venv()`
- `NodeInspector(DevProcessInspector)` — production
- `PythonInspector(DevProcessInspector)` — production
- Future: OllamaInspector, DockerInspector, BunInspector (add to RuntimeInspectorPanel.inspectors)

## Dependencies

| Package | Required | Purpose |
|---|---|---|
| Python 3.10+ | Required | Union type syntax (`int \| None`) |
| tkinter | Required (bundled) | GUI framework, Canvas for ops panel |
| math, random | Required (stdlib) | Procedural animation math |
| psutil | Recommended | Runtime Inspector + richer Port Scanner |

## Design Rules

- Keep application lightweight and single-file
- Avoid overengineering and unnecessary dependencies
- Preserve tkinter architecture
- No Electron, no web stack, no background services
- Explain destructive actions before executing
- Prioritize stability over feature bloat
- Ops panel is procedural-only — no image assets in the UI path

## Known Issues

None currently confirmed.

## Next Recommended Improvements

### Process Management
- Port scanning for custom/non-standard ports beyond the dashboard list
- Keyboard shortcut: Ctrl+Enter to run Find → Verify → Kill in sequence
- Kill All Python shortcut (with heavy confirmation — broader blast radius than Kill All Node)
- Tray icon / minimize-to-tray (optional, user-driven)

### Runtime Inspectors
- OllamaInspector — detect ollama.exe processes, show loaded models if detectable
- DockerInspector — via `docker ps` subprocess or psutil matching `com.docker.*`
- BunInspector — detect bun.exe processes (same framework pattern as NodeInspector)
- Runtime Inspector runtime filter buttons (show All / Node only / Python only)
- Environment variable viewer for selected process (NODE_ENV, PORT, VIRTUAL_ENV, etc.)

### Process Details Panel
- Clickable port links in detail panel (opens in browser)
- Show process start time and uptime
- Show open file handles count
- Parent process name in addition to PPID

### Telemetry + Logging
- Save / export activity log to file (plain text or JSON)
- Diagnostic snapshot export: capture all running dev processes + port states to a file
- Per-session log history with scroll-back
- Configurable log verbosity (INFO / WARN / DEBUG)

### Operational Dashboard
- Telemetry history sparklines in ops panel (tiny inline graphs for CPU / process count over time)
- Ops panel width user-configurable (drag to resize)
- Alert threshold: highlight ORPHANED metric differently if count exceeds user-set limit
- Optional sound/notification on process crash or orphan detection

### Procedural UI Refinements
- Additional scan line variants (diagonal, random flicker)
- Radar blip persistence tuning (user-configurable decay rate)
- Optional CRT-style subtle vignette around the main content area
- Terminal cursor blink in header (`▌`) alongside TASKKILLER 3000
