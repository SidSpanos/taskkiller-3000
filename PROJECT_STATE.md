# Project State

## Current Status

TaskKiller 3000 — stable. Runtime Inspector (v3) with operational dashboard UI. Telemetry sidebar on Port Scanner tab shows live process counts, port status, and runtime monitor state. Row tints, status dot, and activity log improvements shipped.

## Architecture

- Single-file tkinter application (`port_manager.py`)
- Windows-focused, Python 3.10+
- psutil optional for Port Scanner (falls back to `tasklist`), required for Runtime Inspector
- GitHub Actions configured (Claude PR assistant + code review)
- `DevProcessInspector` base class → `NodeInspector`, `PythonInspector` subclasses
- `RuntimeInspectorPanel` collects from all inspectors and merges into one table
- `ProcessInfo` dataclass carries `runtime` and `venv` fields alongside existing data

## Completed Features

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
- **Telemetry sidebar** (210px fixed, right of scanner): live NODE.JS count, PYTHON count, PORTS ACTIVE (N/8), ORPHANED count (yellow when > 0), AUTO-REFRESH status, LAST SCAN time, RUNTIME MON state (STANDBY/ACTIVE)
- Status bar: colored dot indicator (● green/yellow/red), psutil version shown directly
- Activity log: `spacing1=2, spacing3=2` breathing room; dimmer timestamps (TIME tag); ACTIVITY LOG label above output; `─` separators in log headers

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
- **Per-runtime row background tints**: `ROW_NODE="#0f1f12"` (green wash), `ROW_PYTHON="#0d1520"` (blue wash), `ROW_ORPHAN="#1e1a00"` (amber wash), `ROW_ZOMBIE="#1e0a0a"` (red wash)
- Button toolbar separator between Safe Stop and Force Kill group
- "PROCESS DETAILS" header with `─` separator in detail panel

### DevProcessInspector Framework
- `DevProcessInspector` base class: PROCESS_NAMES, SCRIPT_PATTERNS, RUNTIME_LABEL, DEFAULT_LABEL
- Override: `should_include()`, `_detect_project()`, `_detect_venv()`
- `NodeInspector(DevProcessInspector)` — production
- `PythonInspector(DevProcessInspector)` — production
- Future: OllamaInspector, DockerInspector, BunInspector (add to RuntimeInspectorPanel.inspectors)

## Design Rules

- Keep application lightweight and single-file
- Avoid overengineering and unnecessary dependencies
- Preserve tkinter architecture
- No Electron, no web stack, no background services
- Explain destructive actions before executing
- Prioritize stability over feature bloat

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
