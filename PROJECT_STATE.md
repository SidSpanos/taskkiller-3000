# Project State

## Current Status

Port Process Manager is stable and synced with GitHub.
All planned v1 features shipped. Repository is clean.

## Architecture

- Single-file tkinter application (`port_manager.py`)
- Windows-focused, Python 3.10+
- psutil optional (falls back to `tasklist`)
- GitHub Actions configured (Claude PR assistant + code review)

## Completed Features

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
- README with screenshot, troubleshooting, port reference table
- .gitignore, requirements.txt, CLAUDE.md

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
- Resizable/collapsible scanner panel
- Tray icon / minimize-to-tray (optional, user-driven)
