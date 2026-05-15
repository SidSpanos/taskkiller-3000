# TaskKiller 3000

A Windows desktop utility for developer process management. Identify, inspect, and kill processes holding localhost ports — with deep visibility into Node.js environments before you terminate anything.

Built with Python and Tkinter — no web stack, no Electron, no external UI frameworks.

---

## Screenshots

### Port Scanner

![Port Scanner — main window](screenshots/main.png)

Port scanner on startup — 8080 (`wslrelay.exe`) and 11434 (`ollama.exe`) detected as OCCUPIED. Double-click any red row to load it into the Find → Verify → Kill workflow below.

### Node Inspector

![Node Inspector — process intelligence panel](screenshots/node-inspector.png)

Node Inspector tab showing active Node.js processes with their project names, script types (Vite, Next.js, MCP Server, etc.), listening ports, CPU/RAM usage, and parent/child relationships. Orphaned processes are highlighted in yellow.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| OS | Windows 10 / 11 |
| tkinter | Bundled with Python (no install needed) |
| psutil | Optional for Port Scanner — **required for Node Inspector** |

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

Without `psutil`, Port Scanner falls back to `tasklist` (less process detail). Node Inspector requires psutil — it will show a notice if missing.

```
pip install psutil
```

Or install from the requirements file:

```
pip install -r requirements.txt
```

### 3. No other dependencies required

`tkinter`, `subprocess`, `os`, `re`, `webbrowser` are all Python standard library.

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

The application has two tabs: **Port Scanner** and **Node Inspector**.

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

### Tab 2: Node Inspector

Provides deep visibility into every running Node.js process before you decide to terminate it. Shows what each process actually is, what project owns it, and whether it is healthy.

#### Process table

Each row in the table shows:

| Column | Description |
|---|---|
| PID | Process ID |
| PPID | Parent process ID |
| Status | RUNNING, ORPHANED, or ZOMBIE |
| Port(s) | Listening ports owned by this process |
| CPU% | CPU utilisation (updated each refresh) |
| RAM MB | Resident memory in megabytes |
| Project | Name from `package.json`, or folder name |
| Script | Detected script type (see list below) |
| Working Dir | Current working directory |

Click any column heading to sort ascending/descending.

#### Script type detection

The inspector classifies each Node process by scanning its command-line arguments:

| Script Type | Detected when command line contains |
|---|---|
| Vite | `vite` |
| Next.js | `next` |
| Nuxt | `nuxt` |
| Svelte | `svelte` |
| Remix | `remix` |
| Webpack | `webpack` |
| Nodemon | `nodemon` |
| MCP Server | `mcp` |
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

#### Process detail panel

Select any row to see full details in the panel below the table:

- Full command-line arguments (untruncated)
- Listening ports
- CPU and RAM usage
- Parent PID and child PIDs
- Working directory and executable path
- Project name (resolved from `package.json`)
- Warnings for orphaned or zombie status

#### Orphaned process detection

A process is marked **ORPHANED** (yellow) when its parent PID no longer exists. This commonly happens when:
- A terminal or shell was closed without cleanly shutting down child processes
- A dev server spawned child workers and the parent crashed
- A process manager (PM2, nodemon) exited and left workers running

Orphaned processes keep holding their ports and consuming resources. The Node Inspector surfaces them so you can clean them up deliberately.

#### Zombie process detection

A process is marked **ZOMBIE** (red) when it has finished execution but has not been reaped by its parent. Zombie processes hold a PID slot and a port entry but are no longer doing any work. They should be cleaned up.

#### Safe Stop vs Force Kill

| Action | Command | Behaviour |
|---|---|---|
| **Safe Stop** | `taskkill /PID <pid>` (no `/F`) | Sends a graceful exit signal. Node.js processes that handle `SIGTERM` or close events will shut down cleanly, flush logs, and release ports properly. |
| **Force Kill** | `taskkill /PID <pid> /F` | Immediately terminates the process. Use this if Safe Stop does not work within a few seconds. |

Both actions show a confirmation dialog with the project name, script type, and affected ports before proceeding.

#### Kill All Node

Terminates every `node.exe` process on the machine at once (`taskkill /IM node.exe /F`). Available in both tabs. Shows a count of processes that will be affected before asking for confirmation.

#### Port detection

Port mapping is built from `psutil.net_connections()` (LISTEN state only), with `netstat -ano` as a fallback. Each process row shows all ports it is currently listening on. A process with no open ports is shown with `—`.

#### Auto-refresh

The **Auto (3s)** checkbox enables automatic refresh every 3 seconds. CPU percentages are tracked across refreshes — the first tick shows `0.0%`, subsequent ticks show real utilisation.

Both tabs have independent auto-refresh controls. Killing a process in the Node Inspector automatically refreshes the Port Scanner tab.

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

### Node Inspector shows no processes

psutil is required. Install it:

```
pip install psutil
```

Then restart the application.

### Node Inspector CPU% shows 0.0% on first load

This is expected. psutil's `cpu_percent` requires two measurements to calculate a delta. Enable **Auto (3s)** and real values will appear after the first refresh tick.

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

The Port Scanner works without it using `tasklist` as fallback, but you'll get less process detail. Node Inspector is unavailable without psutil.

### App won't start — SyntaxError or TypeError on launch

You're on Python 3.9 or older. Upgrade to Python 3.10+.

---

## Project structure

```
taskkiller-3000/
├── port_manager.py           # Main application (single file)
├── run_port_manager.bat      # Windows launcher
├── requirements.txt          # psutil (optional)
├── .gitignore
├── README.md
├── CLAUDE.md                 # AI assistant instructions
├── PROJECT_STATE.md          # Project status and roadmap
├── screenshots/
│   ├── main.png              # Port Scanner tab
│   └── node-inspector.png    # Node Inspector tab
└── .github/
    └── workflows/
        ├── claude.yml                # Claude PR assistant
        └── claude-code-review.yml   # Claude code review
```

---

## Extensibility

The Node Inspector is built on a modular `DevProcessInspector` base class. Adding support for a new process type (Python, Ollama, Docker, Electron, MCP servers) requires:

1. Subclassing `DevProcessInspector`
2. Setting `PROCESS_NAMES` (e.g. `("python.exe", "python")`)
3. Setting `SCRIPT_PATTERNS` (keyword → label mapping)
4. Adding a new tab in the notebook

No changes to the existing code are required.

---

## License

MIT
