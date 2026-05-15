# Project State

## Current Status

TaskKiller 3000 — stable. Node Inspector added (v2).
Repository is clean. psutil recommended for full Node Inspector functionality.

## Architecture

- Single-file tkinter application (`port_manager.py`)
- Windows-focused, Python 3.10+
- psutil optional (falls back to `tasklist`)
- GitHub Actions configured (Claude PR assistant + code review)

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

### Node Inspector (Tab 2)
- Detects all active node.exe processes via psutil
- Shows PID, parent PID, status, port(s), CPU%, RAM, project name, script type, working dir
- Detects orphaned processes (parent PID no longer exists)
- Detects zombie processes (psutil status == zombie)
- Detects parent/child process relationships (shows child PIDs)
- Classifies script type: Vite, Next.js, Nuxt, Svelte, Remix, Webpack, Nodemon, MCP Server, ts-node, Jest, Vitest, Mocha, Express, Fastify, NestJS, Strapi, Prisma, esbuild, Rollup, Turborepo, Electron, Storybook, TypeScript
- Detects project name from package.json (walks up to 2 parent dirs)
- Safe Stop (graceful, no /F) + Force Kill options with confirmation dialogs
- Kill All Node shortcut (also available in Port Scanner tab)
- Sortable columns (click heading)
- Process detail panel: full cmdline, ports, CPU, RAM, parent chain, cwd, exe, warnings
- Auto-refresh (3s, toggle checkbox)
- Port map via psutil.net_connections() with netstat fallback
- Tab lazy-loads on first visit
- Both tabs share port scanner data — kills in Node Inspector refresh Port Scanner too

### Modular Inspector Framework
- `DevProcessInspector` base class — subclass + set PROCESS_NAMES + SCRIPT_PATTERNS
- `NodeInspector(DevProcessInspector)` — ready
- Future inspectors: PythonInspector, OllamaInspector, DockerInspector, ElectronInspector

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
- Python inspector tab (reuse DevProcessInspector framework)
- Ollama inspector tab
- Docker inspector tab (via docker ps subprocess or Docker SDK)
- MCP server inspector (detect MCP config files, show which server owns which process)
- Environment variable viewer for selected process (NODE_ENV, PORT, etc.)
