# TaskKiller 3000

A Windows desktop utility for developer process management. Identify, inspect, and kill processes holding localhost ports — with deep visibility into Node.js and Python environments before you terminate anything.

Built with Python and Tkinter — no web stack, no Electron, no external UI frameworks.

---

## Screenshots

### Port Scanner with Persistent Operations Panel

![Port Scanner — operational dashboard](screenshots/ops-panel-port-scanner.png)

Port Scanner tab with the persistent left operations panel. Live telemetry shows NODE.JS count, PYTHON count, PORTS ACTIVE (1/8), ORPHANED count, AUTO-REFRESH state, LAST SCAN timestamp, and RUNTIME MON status. Port 11434 (`ollama.exe`) detected as OCCUPIED. The procedural radar sweep and terminal-style branding are visible at the left. ACTIVITY LOG below the scanner table shows timestamped INFO and WARN events.

### Runtime Inspector with Persistent Operations Panel

![Runtime Inspector — process intelligence panel](screenshots/ops-panel-runtime-inspector.png)

Runtime Inspector tab — the left operations panel remains visible and live across all tab switches. Two Node.js processes shown: one RUNNING (green row), one ORPHANED (amber row). The persistent status bar at the bottom shows READY with a colored indicator dot. Telemetry in the sidebar continues updating: ORPHANED count = 1, RUNTIME MON = ACTIVE.

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or newer | Required — uses `int \| None` union type syntax |
| OS | Windows 10 / 11 | Required |
| tkinter | Bundled with Python | No install needed |
| psutil | Optional / Recommended | Optional for Port Scanner — **required for Runtime Inspector** |

> **Why Python 3.10?**  
> The app uses `int | None` union type syntax introduced in Python 3.10. It will not start on older versions.

### Check your Python version

```
python --version
```

---

## Installation

### 1. Clone or download

```
git clone https://github.com/SidSpanos/taskkiller-3000.git
cd taskkiller-3000
```

Or download and extract the ZIP from GitHub.

### 2. Install psutil (recommended)

Without `psutil`, Port Scanner falls back to `tasklist` (less process detail). Runtime Inspector requires psutil — it will show a notice if missing.

```
pip install psutil
```

Or install from the requirements file:

```
pip install -r requirements.txt
```

### 3. No other dependencies required

`tkinter`, `subprocess`, `os`, `re`, `math`, `webbrowser` are all Python standard library. The procedural ops panel (radar, scan line, blinking indicators) requires no external packages.

---

## How to run

**Option A — Python directly:**

```
python port_manager.py
```

**Option B — Batch launcher:**

```
run_port_manager.bat
```

Double-clicking `run_port_manager.bat` also works from Explorer.

---

## Features

The application has a **persistent left operations panel** and two tabs: **Port Scanner** and **Runtime Inspector**.

---

### Persistent Operations Panel

A fixed 210px left panel visible across all tabs. Acts as the application identity and global runtime monitoring dashboard. Entirely procedural — no external image assets or dependencies required.

#### Terminal-style branding (Canvas)
- `TASKKILLER 3000` rendered in Consolas 13pt bold green — integrated into the UI as Canvas text
- `RUNTIME OPS MONITOR` subtitle in dim green below
- Slow horizontal scan line (~22fps) scrolls across the header — single coordinate update per frame, negligible CPU

#### Procedural radar (Canvas)
- Rotating sweep line at 2°/frame, ~12fps — one full revolution every ~15 seconds
- 22-step afterglow trail behind the sweep (brightness falls off linearly)
- Random blip dots seed at the sweep tip (4% chance per frame), fade via exponential decay
- Concentric rings, crosshairs, and 30° tick marks drawn once at startup — never redrawn
- All animation via `after()` scheduling — no threads, no busy loops

#### Live telemetry indicator dots
- `●` blinks next to NODE.JS (green), PYTHON (blue), ORPHANED (yellow)
- Each dot blinks independently at a random 1600–2800ms interval — never sync

#### Live telemetry
| Metric | Description |
|---|---|
| NODE.JS | Count of active Node.js processes |
| PYTHON | Count of active Python dev processes |
| PORTS ACTIVE | Occupied ports / total monitored (e.g. 2 / 8) |
| ORPHANED | Orphaned process count (turns yellow when > 0) |
| AUTO-REFRESH | on / off state of Port Scanner auto-refresh |
| LAST SCAN | Timestamp of last port scan |
| RUNTIME MON | STANDBY or ACTIVE (green when Runtime Inspector has data) |
| ENGINE | psutil version or "tasklist" (fallback mode) |

---

### Tab 1: Port Scanner

#### Port Scanner dashboard
- Scans 8 common dev ports simultaneously in a single `netstat` pass
- Shows Port / Status / Process / PID / Type in a live table
- `OCCUPIED` rows highlighted in red, protected system processes in yellow
- Double-click any occupied row → loads port into entry and runs Find PID automatically
- **Scan All** button for manual refresh; auto-refresh checkbox (5s) for live monitoring

#### Process Detail (3-step workflow)
- **1) Find PID** — runs `netstat -ano`, extracts the LISTENING process on the port
- **2) Verify Process** — shows name, executable path, command line, and status
- **3) Kill Process** — runs `taskkill /F /PID` after confirmation dialog

#### Process classification
Recognizes and labels: Node.js, Python, Ollama, Docker, Java, Electron, Bun, Browser, Unknown

#### Protected process safety
Hard blocks termination of critical Windows processes (`svchost`, `lsass`, `csrss`, `explorer`, `dwm`, `winlogon`, and others). Shows an error dialog — no confirmation prompt is ever shown for protected processes.

#### Other
- Manual port entry (press Enter to search)
- Kill all `node.exe` processes shortcut
- Open port in default browser
- Kill success auto-refreshes the scanner
- Dark theme with color-coded process names in log output

---

### Tab 2: Runtime Inspector

Unified view of all active dev runtime processes — Node.js and Python in a single table. Shows what each process actually is, what project owns it, and whether it is healthy, before you decide to terminate it.

**Node.js rows are shown in green. Python rows are shown in blue.**

#### Process table

| Column | Description |
|---|---|
| Runtime | `Node.js` or `Python` |
| PID | Process ID |
| PPID | Parent process ID |
| Status | RUNNING, ORPHANED, or ZOMBIE |
| Port(s) | Listening ports owned by this process |
| CPU% | CPU utilisation (updated each refresh) |
| RAM MB | Resident memory in megabytes |
| Project | Resolved from `package.json`, `pyproject.toml`, or `setup.cfg` |
| Script | Detected framework or script type |
| Working Dir | Current working directory |

Click any column heading to sort ascending/descending.

#### Node.js script detection

| Script Type | Detected when command line contains |
|---|---|
| MCP Server | `mcp` |
| Vite | `vite` |
| Next.js | `next` |
| Nuxt | `nuxt` |
| Svelte | `svelte` |
| Remix | `remix` |
| Webpack | `webpack` |
| Nodemon | `nodemon` |
| ts-node | `ts-node`, `tsx` |
| Vitest | `vitest` |
| Jest | `jest` |
| Mocha | `mocha` |
| Express | `express` |
| Fastify | `fastify` |
| NestJS | `@nestjs` |
| Turborepo | `turbo` |
| Electron | `electron` |
| Storybook | `storybook` |
| TypeScript | `tsc` |
| esbuild | `esbuild` |
| Node.js | (anything else) |

#### Python script detection

Python processes are only shown if they have listening ports **or** match a recognized dev pattern — generic `python.exe` invocations without a port or known framework are hidden to avoid noise.

| Script Type | Detected when command line contains |
|---|---|
| Uvicorn | `uvicorn` |
| Gunicorn | `gunicorn` |
| Hypercorn | `hypercorn` |
| Daphne | `daphne` |
| Streamlit | `streamlit` |
| Gradio | `gradio` |
| Jupyter | `jupyter`, `notebook` |
| JupyterLab | `lab` |
| Flask | `flask` |
| FastAPI | `fastapi` |
| Django | `django`, `manage.py` |
| Celery | `celery` |
| pytest | `pytest` |
| MkDocs | `mkdocs` |
| HuggingFace | `huggingface` |
| LangChain | `langchain` |
| Python | (anything else with a port) |

#### Virtual environment detection (Python)

For Python processes, the inspector attempts to detect the active virtual environment by walking up from the executable path looking for `pyvenv.cfg` (the standard venv marker). If found, the venv directory name (e.g. `.venv`, `myenv`) is shown in the detail panel.

#### Project name detection

- **Node.js**: reads `package.json` → `name` field, walks up 2 directories
- **Python**: reads `pyproject.toml` → `[project] name`, then `setup.cfg` → `[metadata] name`, then `package.json`, then falls back to the folder name

#### Process detail panel

Select any row to see:

- Runtime type and status
- PID, parent PID, and child PIDs
- Listening ports
- CPU% and RAM
- Virtual environment name (Python only, if detected)
- Project name and working directory
- Full executable path
- Full untruncated command-line arguments
- Warnings for orphaned or zombie status

#### Orphaned process detection

A process is marked **ORPHANED** (yellow) when its parent PID no longer exists. Common causes:
- Terminal or shell closed without shutting down child processes
- Dev server spawned child workers and the parent crashed
- A process manager (PM2, nodemon) exited and left workers running

#### Zombie process detection

A process is marked **ZOMBIE** (red) when it has finished but has not been reaped by its parent. Zombie processes hold a PID slot and port entry but are no longer executing.

#### Safe Stop vs Force Kill

| Action | Command | Behaviour |
|---|---|---|
| **Safe Stop** | `taskkill /PID <pid>` (no `/F`) | Sends a graceful exit signal. Processes that handle shutdown events will flush logs and release ports cleanly. |
| **Force Kill** | `taskkill /PID <pid> /F` | Immediately terminates the process. Use this if Safe Stop does not work within a few seconds. |

Both actions show a confirmation dialog with runtime type, project name, script type, and affected ports before proceeding.

#### Kill All Node

Terminates every `node.exe` process on the machine at once (`taskkill /IM node.exe /F`). Available in both tabs. Shows a count before asking for confirmation.

#### Port detection

Port mapping uses `psutil.net_connections()` (LISTEN state only) with `netstat -ano` as fallback. Each process row shows all listening ports. No open port is shown as `—`.

#### Auto-refresh

**Auto (3s)** checkbox refreshes every 3 seconds. CPU% is tracked across refreshes — first tick shows `0.0%`, real values appear after the second tick.

Killing a process in the Runtime Inspector automatically refreshes the Port Scanner tab.

---

## Common development ports

All 8 ports are scanned by the Port Scanner dashboard automatically on startup.

| Port | Typical use |
|---|---|
| `3000` | Node.js, React (CRA), Express |
| `3001` | Secondary React dev server |
| `4200` | Angular CLI |
| `5000` | Flask, FastAPI |
| `5173` | Vite (React, Vue, Svelte) |
| `8000` | Django, generic HTTP |
| `8080` | Webpack, Java, generic HTTP |
| `11434` | Ollama (local AI) |

---

## LISTENING vs ESTABLISHED — what's the difference?

When you run `netstat -ano`, you'll see two types of connections on a port:

| Type | What it is | Should you kill it? |
|---|---|---|
| `LISTENING` | The **server** — the app that owns the port and waits for connections | **Yes** — this frees the port |
| `ESTABLISHED` | A **client** — e.g. a browser tab connected to the server | No — killing this only disconnects the client temporarily |

Port Process Manager only targets `LISTENING` entries.  
`ESTABLISHED` connections from Chrome, Edge, and Firefox are intentionally ignored.

**Example scenario:**

```
TCP  0.0.0.0:3000    0.0.0.0:0       LISTENING    12345   ← your Node server (kill this)
TCP  127.0.0.1:52341 127.0.0.1:3000  ESTABLISHED  67890   ← a browser tab (ignored)
```

---

## Troubleshooting

### "Port is in use" but app finds nothing

The process may have already exited. The port can linger briefly in `TIME_WAIT` state. Wait a few seconds and retry.

### "Access is denied" when killing

Run the app as Administrator:

1. Right-click `run_port_manager.bat` → **Run as administrator**  
   Or: right-click `python.exe` / your terminal → **Run as administrator**

Some system processes and services require elevated privileges to terminate.

### Runtime Inspector shows no processes

psutil is required. Install it:

```
pip install psutil
```

Then restart the application.

### Runtime Inspector CPU% shows 0.0% on first load

Expected. psutil's `cpu_percent` needs two measurements to calculate a delta. Enable **Auto (3s)** and real values appear after the first refresh tick.

### Python processes not appearing

Python processes are only shown when they have a listening port **or** match a recognized dev framework pattern (Uvicorn, Flask, Streamlit, etc.). Generic `python.exe` scripts without a port are filtered out by design.

### App shows a browser process on the port

Browsers show as `ESTABLISHED` (client), not `LISTENING` (server). If the app is reporting a browser as the LISTENING process, the actual server may have already exited and left a stale netstat entry. Restart your server.

### `python` is not recognized

Python is not on your PATH. Either:
- Use the full path: `C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe port_manager.py`
- Or add Python to PATH during installation (check the box in the Python installer)

### psutil not available warning

Install it:

```
pip install psutil
```

The Port Scanner works without it using `tasklist` as fallback, but you'll get less process detail. Runtime Inspector is unavailable without psutil.

### App won't start — SyntaxError or TypeError on launch

You're on Python 3.9 or older. Upgrade to Python 3.10+.

---

## Project structure

```
taskkiller-3000/
├── port_manager.py                      # Main application (single file)
├── run_port_manager.bat                 # Windows launcher
├── requirements.txt                     # psutil (optional)
├── .gitignore
├── README.md
├── CLAUDE.md                            # AI assistant instructions
├── PROJECT_STATE.md                     # Project status and roadmap
├── assets/
│   └── images/                          # Retained for reference (not used by app)
│       ├── head.png
│       └── radar.png
├── screenshots/
│   ├── ops-panel-port-scanner.png       # Port Scanner + ops panel
│   ├── ops-panel-runtime-inspector.png  # Runtime Inspector + ops panel
│   ├── main.png                         # Earlier Port Scanner screenshot
│   ├── runtime-inspector.png            # Earlier Runtime Inspector screenshot
│   └── node-inspector.png               # Historical (kept for git history)
└── .github/
    └── workflows/
        ├── claude.yml                   # Claude PR assistant
        └── claude-code-review.yml       # Claude code review
```

---

## Extensibility

The Runtime Inspector is built on a `DevProcessInspector` base class. Adding a new runtime (Ollama, Docker, Bun, Java) requires:

1. Subclass `DevProcessInspector`
2. Set `PROCESS_NAMES`, `RUNTIME_LABEL`, `DEFAULT_LABEL`, `SCRIPT_PATTERNS`
3. Optionally override `should_include()`, `_detect_project()`, `_detect_venv()`
4. Add the new inspector instance to `RuntimeInspectorPanel.inspectors`

No changes to the UI code are required.

---

## License

MIT
