# Port Process Manager

A Windows desktop utility for identifying and killing processes that occupy localhost ports. Built with Python and Tkinter — no web stack, no Electron, no external UI frameworks.

Useful when a dev server fails to start because something is already holding the port.

---

## Screenshots

> _Screenshots coming soon. Place images in a `/screenshots` folder and link here._

<!-- Example:
![Main window](screenshots/main.png)
![Kill confirmation](screenshots/kill-confirm.png)
-->

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| OS | Windows 10 / 11 |
| tkinter | Bundled with Python (no install needed) |
| psutil | Optional — see below |

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
git clone https://github.com/your-username/taskkiller-3000.git
cd taskkiller-3000
```

Or download and extract the ZIP from GitHub.

### 2. Install psutil (optional but recommended)

Without `psutil`, the app falls back to `tasklist` which gives less process detail (no exe path, no command line).

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

- **Find PID** — runs `netstat -ano`, extracts the LISTENING process on the port
- **Verify Process** — shows name, executable path, command line, and status
- **Kill Process** — runs `taskkill /F /PID` after confirmation dialog
- Quick-pick buttons for common ports
- Manual port entry (press Enter to search)
- Kill all `node.exe` processes shortcut
- Auto-refresh every 3 seconds (toggle checkbox)
- Open port in default browser
- Dark theme with color-coded process names

---

## Common development ports

| Port | Typical use |
|---|---|
| `3000` | Node.js, React (CRA), Express |
| `3001` | Secondary React dev server |
| `5173` | Vite (React, Vue, Svelte) |
| `8080` | Generic HTTP, Webpack, Java |
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
TCP  0.0.0.0:3000    0.0.0.0:0       LISTENING    12345   ← this is your Node server (kill this)
TCP  127.0.0.1:52341 127.0.0.1:3000  ESTABLISHED  67890   ← this is a browser tab (ignored)
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

The app works without it using `tasklist` as fallback, but you'll get less process detail.

### App won't start — SyntaxError or TypeError on launch

You're on Python 3.9 or older. Upgrade to Python 3.10+.

---

## Project structure

```
taskkiller-3000/
├── port_manager.py       # Main application (single file)
├── run_port_manager.bat  # Windows launcher
├── requirements.txt      # psutil (optional)
├── .gitignore
└── README.md
```

---

## License

MIT
