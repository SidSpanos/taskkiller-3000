# Project State

## Current Status

TaskKiller 3000 — stable. Persistent global ops panel with branding assets + telemetry visible across all tabs. Runtime Inspector (v3) unified Node.js + Python process inspection. Pillow used for image scaling and lightweight atmospheric effects (pulse/flicker); native `PhotoImage` fallback if Pillow absent.

## Architecture

- Single-file tkinter application (`port_manager.py`)
- Windows-focused, Python 3.10+
- psutil optional for Port Scanner (falls back to `tasklist`), required for Runtime Inspector
- Pillow optional — enables image scaling and pulse/flicker effects; falls back to native `PhotoImage`
- GitHub Actions configured (Claude PR assistant + code review)
- `DevProcessInspector` base class → `NodeInspector`, `PythonInspector` subclasses
- `RuntimeInspectorPanel` collects from all inspectors and merges into one table
- `ProcessInfo` dataclass carries `runtime` and `venv` fields alongside existing data

### Root Layout

```
root
└── _outer (horizontal Frame, fills root)
    ├── ops_panel  (185px, side=left, fill=y — persistent across all tabs)
    │   ├── head.png    (banner, scaled to 185px wide, optional CRT flicker)
    │   ├── radar.png   (155×155px, slow brightness pulse via after())
    │   └── telemetry metrics (NODE.JS, PYTHON, PORTS ACTIVE, ORPHANED,
    │                          AUTO-REFRESH, LAST SCAN, RUNTIME MON, ENGINE)
    ├── 1px vertical separator
    └── right_area (expand=True)
          ├── status bar  (side=bottom, global)
          └── ttk.Notebook
                ├── Port Scanner tab
                └── Runtime Inspector tab
```

## Completed Features

### Global Ops Panel (persistent, left side)
- Branding: `assets/images/head.png` banner scaled to panel width
- Atmospheric: `assets/images/radar.png` 155×155px, green radar sweep
- Radar pulse: 4-frame brightness cycle, 1800ms/frame (Pillow only)
- Header flicker: 80ms dim at 6–14s random intervals — subtle CRT aesthetic (Pillow only)
- Static image fallback via `PhotoImage.subsample()` if Pillow absent
- Text-only fallback if image files missing
- Live telemetry: NODE.JS count, PYTHON count, PORTS ACTIVE (N/8), ORPHANED (yellow when > 0)
- State metrics: AUTO-REFRESH (on/off), LAST SCAN timestamp, RUNTIME MON (STANDBY/ACTIVE)
- ENGINE label at bottom (psutil version or "tasklist")

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
- Status bar: colored dot indicator (● green/yellow/red), psutil version shown directly
- Activity log: `spacing1=2, spacing3=2` breathing room; dimmer timestamps; ACTIVITY LOG label; `─` separators

### Runtime Inspector (Tab 2)
- Unified table: Node.js (green) and Python (blue) processes in one view
- Columns: Runtime, PID, PPID, Status, Port(s), CPU%, RAM MB, Project, Script, Working Dir
- Sortable columns (click heading)
- Detects orphaned processes (parent PID no longer exists) — shown in yellow
- Detects zombie processes (psutil status == zombie) — shown in red
- Detects parent/child process relationships (shows child PIDs in detail panel)
- Node.js: 24 script type patterns (Vite, Next.js, MCP Server, Nodemon, Electron, etc.)
- Python: 20 script type patterns (Uvicorn, Flask, Streamlit, Gradio, Jupyter, Django, Celery, etc.)
- Python filter: only surfaces processes with listening ports or a recognized dev pattern
- Python venv detection: walks up from exe looking for pyvenv.cfg, falls back to path component matching
- Project name: Node → package.json; Python → pyproject.toml, setup.cfg, package.json, folder name
- Process detail panel: runtime, status, PID/PPID, children, ports, CPU, RAM, venv, project, cwd, exe, full cmdline, warnings
- Safe Stop (graceful taskkill, no /F) + Force Kill with confirmation dialogs showing runtime + project
- Kill All Node shortcut in both tabs
- Auto-refresh (3s, toggle checkbox); CPU% tracks across refreshes (0.0% on first tick)
- Port map via psutil.net_connections() with netstat fallback
- Tab lazy-loads on first visit; kills refresh Port Scanner automatically
- Per-runtime row background tints: green wash (Node), blue wash (Python), amber (orphaned), red (zombie)
- Button toolbar separator between Safe Stop and Force Kill groups
- "PROCESS DETAILS" header with `─` separator in detail panel

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
| tkinter | Required (bundled) | GUI framework |
| psutil | Recommended | Runtime Inspector + richer Port Scanner |
| Pillow | Optional | Image scaling, radar pulse, header flicker |

## Design Rules

- Keep application lightweight and single-file
- Avoid overengineering and unnecessary dependencies
- Preserve tkinter architecture
- No Electron, no web stack, no background services
- Explain destructive actions before executing
- Prioritize stability over feature bloat

## Assets

```
assets/
└── images/
    ├── head.png    # Branding banner — "TASKKILLER 3000 / RUNTIME OPERATIONS MONITOR"
    └── radar.png   # Atmospheric radar sweep — displayed in ops panel
```

## Known Issues

None currently confirmed.

## Next Recommended Improvements

- Port scanning for custom/non-standard ports beyond the dashboard list
- Keyboard shortcut: Ctrl+Enter to run Find → Verify → Kill in sequence
- Tray icon / minimize-to-tray (optional, user-driven)
- OllamaInspector — detect ollama.exe processes, show loaded models if detectable
- DockerInspector — via `docker ps` subprocess or psutil matching `com.docker.*`
- BunInspector — detect bun.exe processes (same framework as NodeInspector)
- Runtime Inspector runtime filter buttons (show All / Node only / Python only)
- Environment variable viewer for selected process (NODE_ENV, PORT, VIRTUAL_ENV, etc.)
- Kill All Python shortcut (with heavy confirmation — broader blast radius than Kill All Node)
