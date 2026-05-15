# -*- coding: utf-8 -*-
"""
TaskKiller 3000
====================
A Windows desktop utility for process management and developer environment intelligence.

- Port Scanner:       identify and kill processes listening on localhost ports
- Runtime Inspector:  inspect and control dev runtime processes (Node.js, Python)

Requires: Python 3.10+, tkinter (bundled with Python), psutil (optional but recommended)

Install dependency (optional but recommended):
    pip install psutil

Run:
    python port_manager.py
"""

import dataclasses
import json
import os
import re
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar, StringVar,
    IntVar, Checkbutton, END, DISABLED, NORMAL, messagebox,
)
from tkinter import ttk

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
BG_DARK       = "#1e1e1e"
BG_PANEL      = "#252526"
BG_OUTPUT     = "#0f0f0f"
BG_TELEM      = "#1c1c1d"   # telemetry sidebar — very slightly darker than BG_DARK
FG_TEXT       = "#e6e6e6"
FG_DIM        = "#6e7a80"
FG_MID        = "#9eacb4"
ACCENT        = "#007acc"
ACCENT_HOVER  = "#1a8fdc"
BTN_KILL      = "#c0392b"
BTN_KILL_HVR  = "#e04030"
BTN_VERIFY    = "#27ae60"
BTN_VERIFY_HV = "#2ecc71"
BTN_QUICK     = "#3c3c3c"
BTN_QUICK_HV  = "#505050"

# Row tints used in the Runtime Inspector treeview
ROW_NODE      = "#0f1f12"   # very subtle dark green tint
ROW_PYTHON    = "#0d1520"   # very subtle dark blue tint
ROW_ORPHAN    = "#1e1a00"   # dark amber tint
ROW_ZOMBIE    = "#1e0a0a"   # dark red tint

PROCESS_COLORS = {
    "node":     "#2ecc71",
    "python":   "#3498db",
    "docker":   "#1abc9c",
    "bun":      "#f1c40f",
    "npm":      "#2ecc71",
    "chrome":   "#f39c12",
    "msedge":   "#f39c12",
    "firefox":  "#f39c12",
    "brave":    "#f39c12",
    "electron": "#9b59b6",
    "ollama":   "#00cec9",
    "java":     "#e67e22",
    "unknown":  "#e74c3c",
}

PROCESS_LABELS: dict[str, str] = {
    "node":     "Node.js",
    "npm":      "Node.js",
    "python":   "Python",
    "docker":   "Docker",
    "bun":      "Bun",
    "chrome":   "Browser",
    "msedge":   "Browser",
    "firefox":  "Browser",
    "brave":    "Browser",
    "electron": "Electron",
    "ollama":   "Ollama",
    "java":     "Java",
}

SCAN_PORTS = ["3000", "3001", "4200", "5000", "5173", "8000", "8080", "11434"]

PROTECTED_PROCESSES = frozenset({
    "system", "svchost.exe", "lsass.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "smss.exe", "services.exe", "explorer.exe", "dwm.exe",
    "spoolsv.exe", "registry", "memory compression", "taskhostw.exe",
    "sihost.exe", "fontdrvhost.exe",
})

# Node.js script type patterns — first match wins
NODE_SCRIPT_PATTERNS: dict[str, str] = {
    "mcp":       "MCP Server",
    "vite":      "Vite",
    "next":      "Next.js",
    "nuxt":      "Nuxt",
    "svelte":    "Svelte",
    "remix":     "Remix",
    "webpack":   "Webpack",
    "nodemon":   "Nodemon",
    "ts-node":   "ts-node",
    "tsx":       "ts-node",
    "vitest":    "Vitest",
    "jest":      "Jest",
    "mocha":     "Mocha",
    "express":   "Express",
    "fastify":   "Fastify",
    "@nestjs":   "NestJS",
    "strapi":    "Strapi",
    "prisma":    "Prisma",
    "esbuild":   "esbuild",
    "rollup":    "Rollup",
    "turbo":     "Turborepo",
    "electron":  "Electron",
    "storybook": "Storybook",
    "tsc":       "TypeScript",
}

# Python dev workflow patterns — first match wins
PYTHON_SCRIPT_PATTERNS: dict[str, str] = {
    "uvicorn":     "Uvicorn",
    "gunicorn":    "Gunicorn",
    "hypercorn":   "Hypercorn",
    "daphne":      "Daphne",
    "streamlit":   "Streamlit",
    "gradio":      "Gradio",
    "jupyter":     "Jupyter",
    "notebook":    "Jupyter",
    "lab":         "JupyterLab",
    "flask":       "Flask",
    "fastapi":     "FastAPI",
    "django":      "Django",
    "manage.py":   "Django",
    "celery":      "Celery",
    "pytest":      "pytest",
    "mkdocs":      "MkDocs",
    "huggingface": "HuggingFace",
    "diffusers":   "Diffusers",
    "langchain":   "LangChain",
    "llm":         "LLM",
}


# ---------------------------------------------------------------------------
# Process data model
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class ProcessInfo:
    pid:          int
    ppid:         int
    name:         str
    exe:          str
    cmdline:      list[str]
    cwd:          str
    proc_status:  str
    cpu_percent:  float
    ram_mb:       float
    ports:        list[str]
    project_name: str
    script_type:  str
    is_orphaned:  bool
    is_zombie:    bool
    children:     list[int]
    runtime:      str = "Unknown"
    venv:         str = ""

    @property
    def status_display(self) -> str:
        if self.is_zombie:
            return "ZOMBIE"
        if self.is_orphaned:
            return "ORPHANED"
        return self.proc_status.upper()

    @property
    def cmdline_str(self) -> str:
        return " ".join(self.cmdline) if self.cmdline else "<unknown>"


# ---------------------------------------------------------------------------
# Modular inspector base class
# Subclass: set PROCESS_NAMES, SCRIPT_PATTERNS, RUNTIME_LABEL, DEFAULT_LABEL.
# Override should_include(), _detect_project(), _detect_venv() as needed.
# ---------------------------------------------------------------------------
class DevProcessInspector:
    PROCESS_NAMES:   tuple[str, ...] = ()
    SCRIPT_PATTERNS: dict[str, str]  = {}
    RUNTIME_LABEL:   str = "Unknown"
    DEFAULT_LABEL:   str = "Process"

    def __init__(self):
        self._cpu_procs: dict[int, "psutil.Process"] = {}

    def should_include(self, info: ProcessInfo) -> bool:
        return True

    def collect(self, port_map: dict[int, list[str]]) -> list[ProcessInfo]:
        if not PSUTIL_AVAILABLE:
            return []

        results:    list[ProcessInfo] = []
        found_pids: set[int]          = set()

        try:
            all_pids = {p.pid for p in psutil.process_iter(["pid"])}
        except Exception:
            all_pids = set()

        for proc in psutil.process_iter(["pid", "ppid", "name", "status"]):
            try:
                if proc.info["name"].lower() not in self.PROCESS_NAMES:
                    continue
                pid = proc.info["pid"]
                found_pids.add(pid)
                if pid not in self._cpu_procs:
                    self._cpu_procs[pid] = proc
                    try:
                        proc.cpu_percent(interval=None)
                    except Exception:
                        pass
                info = self._gather(self._cpu_procs[pid], port_map, all_pids)
                if info and self.should_include(info):
                    results.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                continue

        for dead in list(self._cpu_procs):
            if dead not in found_pids:
                del self._cpu_procs[dead]

        return results

    def _gather(
        self,
        proc: "psutil.Process",
        port_map: dict[int, list[str]],
        all_pids: set[int],
    ) -> "ProcessInfo | None":
        try:
            with proc.oneshot():
                pid  = proc.pid
                ppid = proc.ppid()
                name = proc.name()
                try:    exe = proc.exe()
                except Exception: exe = ""
                try:    cmdline = proc.cmdline()
                except Exception: cmdline = []
                try:    cwd = proc.cwd()
                except Exception: cwd = ""
                proc_status = proc.status()
                try:    cpu_pct = proc.cpu_percent(interval=None)
                except Exception: cpu_pct = 0.0
                try:    ram_mb = proc.memory_info().rss / (1024 * 1024)
                except Exception: ram_mb = 0.0
                try:    children = [c.pid for c in proc.children()]
                except Exception: children = []

            return ProcessInfo(
                pid=pid, ppid=ppid, name=name, exe=exe, cmdline=cmdline,
                cwd=cwd, proc_status=proc_status, cpu_percent=cpu_pct,
                ram_mb=ram_mb, ports=port_map.get(pid, []),
                project_name=self._detect_project(cwd),
                script_type=self._classify_script(cmdline),
                is_orphaned=(ppid != 0 and ppid not in all_pids),
                is_zombie=(proc_status == "zombie"),
                children=children,
                runtime=self.RUNTIME_LABEL,
                venv=self._detect_venv(exe, cwd),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _detect_venv(self, exe: str, cwd: str) -> str:
        return ""

    def _detect_project(self, cwd: str) -> str:
        if not cwd:
            return "<unknown>"
        try:
            p = Path(cwd)
            for candidate in (p, p.parent, p.parent.parent):
                try:
                    pkg = candidate / "package.json"
                    if pkg.exists():
                        data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
                        name = (data.get("name") or "").strip()
                        if name:
                            return name
                except Exception:
                    pass
            return p.name or "<unknown>"
        except Exception:
            return "<unknown>"

    def _classify_script(self, cmdline: list[str]) -> str:
        if not cmdline:
            return self.DEFAULT_LABEL
        cmd = " ".join(cmdline).lower()
        for pattern, label in self.SCRIPT_PATTERNS.items():
            if pattern in cmd:
                return label
        return self.DEFAULT_LABEL


# ---------------------------------------------------------------------------
# Node.js inspector
# ---------------------------------------------------------------------------
class NodeInspector(DevProcessInspector):
    PROCESS_NAMES   = ("node.exe", "node")
    RUNTIME_LABEL   = "Node.js"
    DEFAULT_LABEL   = "Node.js"
    SCRIPT_PATTERNS = NODE_SCRIPT_PATTERNS


# ---------------------------------------------------------------------------
# Python inspector
# ---------------------------------------------------------------------------
class PythonInspector(DevProcessInspector):
    PROCESS_NAMES   = ("python.exe", "python3.exe", "python", "python3")
    RUNTIME_LABEL   = "Python"
    DEFAULT_LABEL   = "Python"
    SCRIPT_PATTERNS = PYTHON_SCRIPT_PATTERNS

    def should_include(self, info: ProcessInfo) -> bool:
        return bool(info.ports) or info.script_type != self.DEFAULT_LABEL

    def _detect_venv(self, exe: str, cwd: str) -> str:
        if not exe:
            return ""
        try:
            p = Path(exe)
            for candidate in (p.parent, p.parent.parent, p.parent.parent.parent):
                if (candidate / "pyvenv.cfg").exists():
                    return candidate.name
            for part in p.parts:
                low = part.lower()
                if low in (".venv", "venv", "env", ".env"):
                    return part
                if "venv" in low and part not in ("", "\\", "/"):
                    return part
        except Exception:
            pass
        return ""

    def _detect_project(self, cwd: str) -> str:
        if not cwd:
            return "<unknown>"
        try:
            p = Path(cwd)
            for candidate in (p, p.parent, p.parent.parent):
                try:
                    ppt = candidate / "pyproject.toml"
                    if ppt.exists():
                        content = ppt.read_text(encoding="utf-8", errors="ignore")
                        m = re.search(
                            r'^\s*name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE
                        )
                        if m:
                            return m.group(1).strip()
                except Exception:
                    pass
                try:
                    scfg = candidate / "setup.cfg"
                    if scfg.exists():
                        content = scfg.read_text(encoding="utf-8", errors="ignore")
                        m = re.search(r'^\s*name\s*=\s*(.+)$', content, re.MULTILINE)
                        if m:
                            name = m.group(1).split(";")[0].strip()
                            if name:
                                return name
                except Exception:
                    pass
                try:
                    pkg = candidate / "package.json"
                    if pkg.exists():
                        data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
                        name = (data.get("name") or "").strip()
                        if name:
                            return name
                except Exception:
                    pass
            return p.name or "<unknown>"
        except Exception:
            return "<unknown>"


# ---------------------------------------------------------------------------
# Runtime Inspector UI panel — Node.js + Python unified table
# ---------------------------------------------------------------------------
class RuntimeInspectorPanel:

    def __init__(self, parent: Frame, app: "PortProcessManager"):
        self.parent     = parent
        self.app        = app
        self.root       = app.root
        self.inspectors = [NodeInspector(), PythonInspector()]
        self.processes: list[ProcessInfo] = []
        self._auto_var  = IntVar(value=0)
        self._auto_job  = None
        self._port_map: dict[int, list[str]] = {}
        self._sort_col  = "runtime"
        self._sort_rev  = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Toolbar
        toolbar = Frame(self.parent, bg=BG_PANEL, padx=10, pady=8)
        toolbar.pack(fill="x")

        Label(
            toolbar, text="Runtime Inspector",
            bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 14))

        # Action group: safe operations
        self._btn(toolbar, "Refresh",    self.refresh,     ACCENT,     ACCENT_HOVER ).pack(side="left", padx=(0, 4))
        self._btn(toolbar, "Safe Stop",  self._safe_stop,  BTN_VERIFY, BTN_VERIFY_HV).pack(side="left", padx=(0, 2))

        # Thin separator between safe and destructive actions
        Frame(toolbar, bg="#3a3a3a", width=1).pack(side="left", padx=8, fill="y", pady=4)

        # Destructive group
        self._btn(toolbar, "Force Kill",    self._force_kill,    BTN_KILL, BTN_KILL_HVR).pack(side="left", padx=(0, 4))
        self._btn(toolbar, "Kill All Node", self._kill_all_node, BTN_KILL, BTN_KILL_HVR).pack(side="left")

        Checkbutton(
            toolbar, text="Auto (3s)", variable=self._auto_var,
            command=self._toggle_auto,
            bg=BG_PANEL, fg=FG_TEXT, selectcolor=BG_DARK,
            activebackground=BG_PANEL, activeforeground=FG_TEXT,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=10)

        self._status_var = StringVar(value="")
        Label(
            toolbar, textvariable=self._status_var,
            bg=BG_PANEL, fg=FG_MID, font=("Consolas", 9),
        ).pack(side="right", padx=4)

        # Paned: treeview (top) + detail panel (bottom)
        paned = ttk.PanedWindow(self.parent, orient="vertical")
        paned.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        tree_frame = Frame(paned, bg=BG_DARK)
        paned.add(tree_frame, weight=3)

        cols = ("runtime", "pid", "ppid", "status", "ports", "cpu", "ram",
                "project", "script", "cwd")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Dashboard.Treeview", selectmode="browse",
        )
        for cid, heading, width, anchor in (
            ("runtime", "Runtime",      80,  "center"),
            ("pid",     "PID",          65,  "center"),
            ("ppid",    "PPID",         65,  "center"),
            ("status",  "Status",       90,  "center"),
            ("ports",   "Port(s)",      90,  "center"),
            ("cpu",     "CPU%",         60,  "center"),
            ("ram",     "RAM MB",       70,  "center"),
            ("project", "Project",     140,  "w"),
            ("script",  "Script",      110,  "center"),
            ("cwd",     "Working Dir", 260,  "w"),
        ):
            self.tree.heading(cid, text=heading,
                              command=lambda c=cid: self._sort_by(c))
            self.tree.column(cid, width=width, minwidth=50,
                             anchor=anchor, stretch=(cid == "cwd"))

        # Per-runtime row tints for at-a-glance distinction
        self.tree.tag_configure("node_ok",  foreground="#2ecc71", background=ROW_NODE)
        self.tree.tag_configure("py_ok",    foreground="#3498db", background=ROW_PYTHON)
        self.tree.tag_configure("orphaned", foreground="#f1c40f", background=ROW_ORPHAN)
        self.tree.tag_configure("zombie",   foreground="#e74c3c", background=ROW_ZOMBIE)

        sb_v = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        sb_h = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)
        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail panel
        detail_frame = Frame(paned, bg=BG_DARK)
        paned.add(detail_frame, weight=1)

        Label(
            detail_frame, text="PROCESS DETAILS",
            bg=BG_DARK, fg=FG_DIM, font=("Consolas", 8, "bold"),
        ).pack(anchor="w", padx=10, pady=(6, 2))

        Frame(detail_frame, bg="#2a2a2a", height=1).pack(fill="x", padx=8, pady=(0, 4))

        di = Frame(detail_frame, bg=BG_DARK)
        di.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.detail = Text(
            di, wrap="word", bg=BG_OUTPUT, fg=FG_TEXT,
            insertbackground=FG_TEXT, font=("Consolas", 10),
            relief="flat", padx=12, pady=10, state=DISABLED,
        )
        sb_d = Scrollbar(di, command=self.detail.yview)
        self.detail.configure(yscrollcommand=sb_d.set)
        self.detail.pack(side="left", fill="both", expand=True)
        sb_d.pack(side="right", fill="y")

        for tag, fg, bold in (
            ("key",    ACCENT,    True),
            ("val",    FG_TEXT,   False),
            ("ok",     "#2ecc71", False),
            ("warn",   "#f1c40f", False),
            ("error",  "#e74c3c", False),
            ("header", ACCENT,    True),
            ("dim",    FG_DIM,    False),
            ("pyblue", "#3498db", False),
        ):
            self.detail.tag_configure(
                tag, foreground=fg,
                font=("Consolas", 10, "bold") if bold else ("Consolas", 10),
            )

        if not PSUTIL_AVAILABLE:
            self._show_no_psutil()

    def _btn(self, parent, text, cmd, bg=ACCENT, hover=ACCENT_HOVER, width=None):
        b = Button(
            parent, text=text, command=cmd, bg=bg, fg="white",
            relief="flat", font=("Segoe UI", 10, "bold"),
            activebackground=hover, activeforeground="white",
            cursor="hand2", padx=10, pady=6, borderwidth=0,
        )
        if width:
            b.config(width=width)
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def refresh(self):
        self._port_map = self._build_port_map()
        self.processes = []
        for inspector in self.inspectors:
            self.processes.extend(inspector.collect(self._port_map))

        self._populate_tree()
        self.app._update_telemetry()  # push fresh data to sidebar

        node_count = sum(1 for p in self.processes if p.runtime == "Node.js")
        py_count   = sum(1 for p in self.processes if p.runtime == "Python")
        orphans    = sum(1 for p in self.processes if p.is_orphaned)
        zombies    = sum(1 for p in self.processes if p.is_zombie)
        ts         = datetime.now().strftime("%H:%M:%S")

        parts: list[str] = []
        if node_count: parts.append(f"{node_count} Node")
        if py_count:   parts.append(f"{py_count} Python")
        if not parts:  parts.append("0 processes")
        if orphans:    parts.append(f"{orphans} orphaned")
        if zombies:    parts.append(f"{zombies} zombie")
        self._status_var.set("  |  ".join(parts) + f"  —  {ts}")

    def _build_port_map(self) -> dict[int, list[str]]:
        result: dict[int, list[str]] = {}
        if PSUTIL_AVAILABLE:
            try:
                for conn in psutil.net_connections(kind="inet"):
                    if conn.status == "LISTEN" and conn.pid:
                        result.setdefault(conn.pid, []).append(str(conn.laddr.port))
                return result
            except Exception:
                pass
        try:
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for ln in out.stdout.splitlines():
                if "LISTENING" not in ln.upper():
                    continue
                parts = ln.split()
                if len(parts) < 5:
                    continue
                m = re.search(r":(\d+)$", parts[1])
                if m and parts[-1].isdigit():
                    result.setdefault(int(parts[-1]), []).append(m.group(1))
        except Exception:
            pass
        return result

    # ------------------------------------------------------------------
    # Treeview
    # ------------------------------------------------------------------
    def _populate_tree(self):
        sel = self.tree.selection()
        sel_pid = int(sel[0]) if sel else None
        self.tree.delete(*self.tree.get_children())

        for p in sorted(self.processes, key=lambda x: (x.runtime, x.pid)):
            if p.is_zombie:
                tag = "zombie"
            elif p.is_orphaned:
                tag = "orphaned"
            elif p.runtime == "Python":
                tag = "py_ok"
            else:
                tag = "node_ok"

            cwd_d = ("..." + p.cwd[-47:]) if len(p.cwd) > 50 else p.cwd
            self.tree.insert("", "end", iid=str(p.pid), values=(
                p.runtime,
                p.pid, p.ppid, p.status_display,
                ", ".join(p.ports) if p.ports else "—",
                f"{p.cpu_percent:.1f}%",
                f"{p.ram_mb:.0f}",
                p.project_name, p.script_type, cwd_d,
            ), tags=(tag,))

        if sel_pid and self.tree.exists(str(sel_pid)):
            self.tree.selection_set(str(sel_pid))

    def _sort_by(self, col: str):
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        numeric = {"pid", "ppid", "cpu", "ram"}

        def key(iid):
            v = self.tree.set(iid, col)
            if col in numeric:
                try:
                    return float(v.replace("%", "").strip())
                except Exception:
                    return 0.0
            return v.lower()

        items = list(self.tree.get_children(""))
        items.sort(key=key, reverse=self._sort_rev)
        for i, iid in enumerate(items):
            self.tree.move(iid, "", i)

    # ------------------------------------------------------------------
    # Selection + details
    # ------------------------------------------------------------------
    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        pid  = int(sel[0])
        proc = next((p for p in self.processes if p.pid == pid), None)
        if proc:
            self._show_details(proc)

    def _show_details(self, p: ProcessInfo):
        self.detail.config(state=NORMAL)
        self.detail.delete("1.0", END)

        def kv(k: str, v: str, vtag: str = "val"):
            self.detail.insert(END, f"  {k:<24}", "key")
            self.detail.insert(END, f"{v}\n", vtag)

        self.detail.insert(END, f"  {p.name}  ·  PID {p.pid}  ·  {p.script_type}\n\n", "header")

        runtime_tag = "pyblue" if p.runtime == "Python" else "ok"
        kv("Runtime:",        p.runtime, runtime_tag)
        status_tag = "error" if p.is_zombie else ("warn" if p.is_orphaned else "ok")
        kv("Status:",         p.status_display, status_tag)
        kv("PID / Parent:",   f"{p.pid}  →  {p.ppid}")
        if p.children:
            kv("Children:", ", ".join(str(c) for c in p.children))
        kv("Listening Ports:", ", ".join(p.ports) if p.ports else "none")
        kv("CPU:",            f"{p.cpu_percent:.2f}%")
        kv("RAM:",            f"{p.ram_mb:.1f} MB")
        if p.venv:
            kv("Virtual Env:", p.venv, "pyblue")
        kv("Project:",        p.project_name)
        kv("Working Dir:",    p.cwd or "<unknown>")
        kv("Executable:",     p.exe or "<unknown>")

        self.detail.insert(END, "\n  Command Line:\n", "key")
        self.detail.insert(END, f"  {p.cmdline_str}\n", "dim")

        if p.is_orphaned:
            self.detail.insert(
                END, "\n  WARNING: Parent process no longer exists (orphaned).\n", "warn",
            )
        if p.is_zombie:
            self.detail.insert(
                END, "\n  WARNING: Process is a zombie (finished but not reaped).\n", "error",
            )

        self.detail.config(state=DISABLED)

    def _show_no_psutil(self):
        self.detail.config(state=NORMAL)
        self.detail.insert(END, "\n  Runtime Inspector requires psutil.\n\n", "warn")
        self.detail.insert(END, "  Install:  ", "val")
        self.detail.insert(END, "pip install psutil\n\n", "key")
        self.detail.insert(END, "  Then restart the application.\n", "dim")
        self.detail.config(state=DISABLED)
        self._status_var.set("psutil required — pip install psutil")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _get_selected(self) -> "ProcessInfo | None":
        sel = self.tree.selection()
        if not sel:
            return None
        pid = int(sel[0])
        return next((p for p in self.processes if p.pid == pid), None)

    def _safe_stop(self):
        proc = self._get_selected()
        if not proc:
            messagebox.showwarning("No Selection", "Select a process first.")
            return
        if not messagebox.askyesno(
            "Safe Stop",
            f"Send graceful stop to:\n\n"
            f"  Runtime: {proc.runtime}\n"
            f"  PID:     {proc.pid}\n"
            f"  Project: {proc.project_name}\n"
            f"  Script:  {proc.script_type}\n"
            f"  Port(s): {', '.join(proc.ports) or 'none'}\n\n"
            f"Process will be asked to exit gracefully.\n"
            f"Use Force Kill if it does not terminate.",
        ):
            return
        try:
            r = subprocess.run(
                ["taskkill", "/PID", str(proc.pid)],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if r.returncode == 0:
                self._status_var.set(f"Safe stop sent to PID {proc.pid}")
                self.root.after(3000, self.refresh)
                self.root.after(3100, self.app.scan_all_ports)
            else:
                messagebox.showerror("Safe Stop Failed",
                                     (r.stderr or r.stdout).strip() or "Unknown error.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _force_kill(self):
        proc = self._get_selected()
        if not proc:
            messagebox.showwarning("No Selection", "Select a process first.")
            return
        if proc.name.lower() in PROTECTED_PROCESSES:
            messagebox.showerror("Blocked", f"'{proc.name}' is a protected system process.")
            return
        if not messagebox.askyesno(
            "Force Kill",
            f"Forcefully terminate:\n\n"
            f"  Runtime: {proc.runtime}\n"
            f"  PID:     {proc.pid}\n"
            f"  Project: {proc.project_name}\n"
            f"  Script:  {proc.script_type}\n"
            f"  Port(s): {', '.join(proc.ports) or 'none'}\n\n"
            f"This cannot be undone.",
        ):
            return
        try:
            r = subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if r.returncode == 0:
                self._status_var.set(f"PID {proc.pid} force-killed.")
                self.root.after(500, self.refresh)
                self.root.after(600, self.app.scan_all_ports)
            else:
                err = (r.stderr or r.stdout).strip()
                if "access is denied" in err.lower():
                    messagebox.showerror("Access Denied", "Run as Administrator.")
                else:
                    messagebox.showerror("Kill Failed", err or "Unknown error.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _kill_all_node(self):
        count = sum(1 for p in self.processes if p.runtime == "Node.js")
        if count == 0:
            messagebox.showinfo("No Processes", "No node.exe processes are running.")
            return
        if not messagebox.askyesno(
            "Kill ALL Node Processes",
            f"Forcefully terminate all {count} node.exe process(es)?\n\nThis cannot be undone.",
        ):
            return
        try:
            r = subprocess.run(
                ["taskkill", "/IM", "node.exe", "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            out = (r.stdout + r.stderr).strip()
            if r.returncode != 0 and "not found" not in out.lower():
                messagebox.showerror("Error", out)
            else:
                self._status_var.set("All node.exe processes terminated.")
            self.root.after(500, self.refresh)
            self.root.after(600, self.app.scan_all_ports)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _toggle_auto(self):
        if self._auto_var.get():
            self._auto_tick()
        else:
            if self._auto_job is not None:
                try:
                    self.root.after_cancel(self._auto_job)
                except Exception:
                    pass
                self._auto_job = None

    def _auto_tick(self):
        if not self._auto_var.get():
            return
        try:
            self.refresh()
        except Exception:
            pass
        self._auto_job = self.root.after(3000, self._auto_tick)

    def cancel_auto(self):
        if self._auto_job is not None:
            try:
                self.root.after_cancel(self._auto_job)
            except Exception:
                pass
            self._auto_job = None


# ---------------------------------------------------------------------------
# Main application — Port Scanner tab
# ---------------------------------------------------------------------------
class PortProcessManager:

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("TaskKiller 3000")
        self.root.geometry("1200x860")
        self.root.minsize(820, 640)
        self.root.configure(bg=BG_DARK)

        self.current_pid: int | None = None
        self.current_port: str | None = None
        self.auto_refresh_var = IntVar(value=0)
        self.status_var = StringVar(value="READY")
        self._auto_refresh_job = None

        # Telemetry sidebar StringVars
        self._tv_node    = StringVar(value="—")
        self._tv_py      = StringVar(value="—")
        self._tv_ports   = StringVar(value=f"— / {len(SCAN_PORTS)}")
        self._tv_orphan  = StringVar(value="—")
        self._tv_auto    = StringVar(value="off")
        self._tv_scan    = StringVar(value="—")
        self._tv_monitor = StringVar(value="STANDBY")

        self._setup_styles()

        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        self.port_tab = Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(self.port_tab, text="  Port Scanner  ")

        self.runtime_tab = Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(self.runtime_tab, text="  Runtime Inspector  ")

        # Status bar goes into port_tab first (reserves bottom space before content fill)
        self._build_status_bar()

        # Horizontal content split: left (ops panel) + right (scanner content)
        self.port_content = Frame(self.port_tab, bg=BG_DARK)
        self.port_content.pack(fill="both", expand=True)

        self.port_right = Frame(self.port_content, bg=BG_TELEM, width=185)
        self.port_right.pack_propagate(False)
        self.port_right.pack(side="left", fill="y")

        Frame(self.port_content, bg="#2a2a2c", width=1).pack(side="left", fill="y")

        self.port_left = Frame(self.port_content, bg=BG_DARK)
        self.port_left.pack(side="left", fill="both", expand=True)

        # Build Port Scanner UI into port_left
        self._build_top_section()
        self._build_scanner_panel()
        self._build_action_buttons()
        self._build_output_area()

        # Build telemetry sidebar into port_right
        self._build_telemetry_panel()

        # Build Runtime Inspector
        self.runtime_panel = RuntimeInspectorPanel(self.runtime_tab, self)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self.log("TaskKiller 3000 started.", level="INFO")
        if not PSUTIL_AVAILABLE:
            self.log("psutil not detected — install with: pip install psutil", level="WARN")
        else:
            self.log(f"psutil {psutil.__version__} detected.", level="INFO")

        self.root.after(150, self.scan_all_ports)

    def _on_tab_change(self, _event=None):
        idx = self.notebook.index(self.notebook.select())
        if idx == 1 and not self.runtime_panel.processes:
            self.root.after(50, self.runtime_panel.refresh)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dashboard.Treeview",
            background=BG_PANEL, foreground=FG_TEXT,
            fieldbackground=BG_PANEL, rowheight=26,
            font=("Consolas", 10), borderwidth=0,
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            background=BG_DARK, foreground=FG_MID,
            font=("Segoe UI", 9, "bold"), relief="flat", borderwidth=0,
        )
        style.map(
            "Dashboard.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")],
        )

        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL, foreground=FG_DIM,
            font=("Segoe UI", 10), padding=[14, 7],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_DARK), ("active", "#333333")],
            foreground=[("selected", FG_TEXT),  ("active", FG_TEXT)],
        )
        style.configure("TPanedwindow", background=BG_DARK)

    # ------------------------------------------------------------------
    # Telemetry sidebar
    # ------------------------------------------------------------------
    def _build_telemetry_panel(self):
        p = self.port_right

        # Identity header
        Label(p, text="TASKKILLER", bg=BG_TELEM, fg="#2d3840",
              font=("Consolas", 13, "bold"), anchor="w").pack(fill="x", padx=12, pady=(12, 0))
        Label(p, text="OPS CONSOLE", bg=BG_TELEM, fg=FG_DIM,
              font=("Consolas", 7, "bold"), anchor="w").pack(fill="x", padx=14, pady=(0, 4))
        Frame(p, bg="#303035", height=1).pack(fill="x", padx=12, pady=(0, 10))

        def metric(label: str, var: StringVar, val_color: str = "#2ecc71") -> Label:
            Label(p, text=label, bg=BG_TELEM, fg=FG_DIM,
                  font=("Consolas", 7, "bold"), anchor="w").pack(fill="x", padx=14, pady=(0, 1))
            lbl = Label(p, textvariable=var, bg=BG_TELEM, fg=val_color,
                        font=("Consolas", 13, "bold"), anchor="w")
            lbl.pack(fill="x", padx=14, pady=(0, 8))
            return lbl

        metric("NODE.JS",      self._tv_node,   "#2ecc71")
        metric("PYTHON",       self._tv_py,      "#3498db")
        metric("PORTS ACTIVE", self._tv_ports,   ACCENT)
        self._orphan_label = metric("ORPHANED",  self._tv_orphan, "#2ecc71")

        Frame(p, bg="#303035", height=1).pack(fill="x", padx=12, pady=(2, 10))

        metric("AUTO-REFRESH", self._tv_auto, FG_MID)
        metric("LAST SCAN",    self._tv_scan, FG_MID)

        Frame(p, bg="#303035", height=1).pack(fill="x", padx=12, pady=(2, 10))

        Label(p, text="RUNTIME MON", bg=BG_TELEM, fg=FG_DIM,
              font=("Consolas", 7, "bold"), anchor="w").pack(fill="x", padx=14, pady=(0, 1))
        self._monitor_label = Label(
            p, textvariable=self._tv_monitor,
            bg=BG_TELEM, fg=FG_DIM,
            font=("Consolas", 10, "bold"), anchor="w",
        )
        self._monitor_label.pack(fill="x", padx=14, pady=(0, 8))

        # Engine — anchor bottom
        Frame(p, bg=BG_TELEM).pack(fill="both", expand=True)  # spacer
        Frame(p, bg="#303035", height=1).pack(fill="x", padx=12)
        engine_str = f"psutil {psutil.__version__}" if PSUTIL_AVAILABLE else "tasklist"
        Label(p, text="ENGINE", bg=BG_TELEM, fg=FG_DIM,
              font=("Consolas", 7, "bold"), anchor="w").pack(fill="x", padx=14, pady=(6, 1))
        Label(p, text=engine_str, bg=BG_TELEM, fg=FG_MID,
              font=("Consolas", 8), anchor="w").pack(fill="x", padx=14, pady=(0, 10))

    def _update_telemetry(self):
        """Refresh telemetry sidebar values from runtime panel data."""
        if not hasattr(self, "runtime_panel"):
            return

        procs = self.runtime_panel.processes
        node_n   = sum(1 for p in procs if p.runtime == "Node.js")
        py_n     = sum(1 for p in procs if p.runtime == "Python")
        orphan_n = sum(1 for p in procs if p.is_orphaned)

        self._tv_node.set(str(node_n) if node_n else "—")
        self._tv_py.set(str(py_n) if py_n else "—")

        orphan_str = str(orphan_n) if procs else "—"
        self._tv_orphan.set(orphan_str)
        orphan_color = "#f1c40f" if orphan_n > 0 else "#2ecc71"
        self._orphan_label.config(fg=orphan_color)

        if procs:
            self._tv_monitor.set("ACTIVE")
            self._monitor_label.config(fg="#2ecc71")
        else:
            self._tv_monitor.set("STANDBY")
            self._monitor_label.config(fg=FG_DIM)

    # ------------------------------------------------------------------
    # Port Scanner UI construction (targets self.port_left)
    # ------------------------------------------------------------------
    def _build_top_section(self):
        top = Frame(self.port_left, bg=BG_PANEL, padx=12, pady=10)
        top.pack(fill="x", padx=8, pady=(10, 4))

        Label(top, text="Port:", bg=BG_PANEL, fg=FG_TEXT,
              font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 8))

        self.port_entry = Entry(
            top, width=10, font=("Consolas", 12),
            bg=BG_OUTPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=ACCENT,
        )
        self.port_entry.insert(0, "3000")
        self.port_entry.pack(side="left", padx=(0, 12), ipady=4)
        self.port_entry.bind("<Return>", lambda e: self.find_pid())

        self.auto_chk = Checkbutton(
            top, text="Auto Refresh (5s)", variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
            bg=BG_PANEL, fg=FG_TEXT, selectcolor=BG_DARK,
            activebackground=BG_PANEL, activeforeground=FG_TEXT,
            font=("Segoe UI", 10),
        )
        self.auto_chk.pack(side="right")

        self._make_button(top, "Open in Browser", self.open_in_browser,
                          bg=BTN_QUICK, hover=BTN_QUICK_HV).pack(side="right", padx=(0, 10))

    def _build_scanner_panel(self):
        outer = Frame(self.port_left, bg=BG_DARK, padx=8, pady=2)
        outer.pack(fill="x", padx=8)

        toolbar = Frame(outer, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 4))

        Label(toolbar, text="PORT SCANNER", bg=BG_DARK, fg=FG_DIM,
              font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 10))

        self._make_button(toolbar, "Scan All", self.scan_all_ports,
                          bg=ACCENT, hover=ACCENT_HOVER, width=10).pack(side="left", padx=(0, 6))
        self._make_button(toolbar, "Kill All Node", self.kill_all_node,
                          bg=BTN_KILL, hover=BTN_KILL_HVR, width=14).pack(side="left")

        self._scan_time_var = StringVar(value="")
        Label(toolbar, textvariable=self._scan_time_var,
              bg=BG_DARK, fg=FG_DIM, font=("Consolas", 8)).pack(side="right")
        Label(toolbar, text="double-click row to load →",
              bg=BG_DARK, fg=FG_DIM, font=("Consolas", 8)).pack(side="right", padx=(0, 12))

        tree_frame = Frame(outer, bg=BG_DARK)
        tree_frame.pack(fill="x")

        cols = ("port", "status", "process", "pid", "type")
        self.scan_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Dashboard.Treeview", selectmode="browse",
            height=len(SCAN_PORTS),
        )
        for cid, heading, width, anchor in (
            ("port",    "Port",    70,  "center"),
            ("status",  "Status",  100, "center"),
            ("process", "Process", 260, "w"),
            ("pid",     "PID",     70,  "center"),
            ("type",    "Type",    110, "center"),
        ):
            self.scan_tree.heading(cid, text=heading)
            self.scan_tree.column(cid, width=width, minwidth=width,
                                  anchor=anchor, stretch=(cid == "process"))

        self.scan_tree.tag_configure("occupied",  foreground="#e74c3c")
        self.scan_tree.tag_configure("protected", foreground="#f1c40f")
        self.scan_tree.tag_configure("free",      foreground=FG_DIM)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.scan_tree.yview)
        self.scan_tree.configure(yscrollcommand=sb.set)
        self.scan_tree.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")

        self.scan_tree.bind("<Double-1>", self._on_scan_row_select)
        self.scan_tree.bind("<Return>",   self._on_scan_row_select)

    def _build_action_buttons(self):
        actions = Frame(self.port_left, bg=BG_DARK, padx=8, pady=8)
        actions.pack(fill="x", padx=8)

        self._make_button(actions, "1) Find PID",       self.find_pid,
                          bg=ACCENT, hover=ACCENT_HOVER, width=18).pack(side="left", padx=4)
        self._make_button(actions, "2) Verify Process", self.verify_process,
                          bg=BTN_VERIFY, hover=BTN_VERIFY_HV, width=18).pack(side="left", padx=4)
        self._make_button(actions, "3) Kill Process",   self.kill_process,
                          bg=BTN_KILL, hover=BTN_KILL_HVR, width=18).pack(side="left", padx=4)
        self._make_button(actions, "Clear Output",      self.clear_output,
                          bg=BTN_QUICK, hover=BTN_QUICK_HV, width=14).pack(side="right", padx=4)

    def _build_output_area(self):
        # Section label
        log_header_row = Frame(self.port_left, bg=BG_DARK)
        log_header_row.pack(fill="x", padx=16, pady=(4, 0))
        Label(log_header_row, text="ACTIVITY LOG", bg=BG_DARK, fg=FG_DIM,
              font=("Consolas", 8, "bold")).pack(side="left")

        wrapper = Frame(self.port_left, bg=BG_DARK)
        wrapper.pack(fill="both", expand=True, padx=16, pady=(2, 8))

        self.output = Text(
            wrapper, wrap="word", bg=BG_OUTPUT, fg=FG_TEXT,
            insertbackground=FG_TEXT, font=("Consolas", 10),
            relief="flat", padx=10, pady=10, state=DISABLED,
            spacing1=2, spacing3=2,   # adds breathing room between log lines
        )
        self.output.pack(side="left", fill="both", expand=True)

        sb = Scrollbar(wrapper, command=self.output.yview)
        sb.pack(side="right", fill="y")
        self.output.config(yscrollcommand=sb.set)

        self.output.tag_configure("INFO",   foreground="#b0bec5")
        self.output.tag_configure("WARN",   foreground="#f1c40f")
        self.output.tag_configure("ERROR",  foreground="#e74c3c")
        self.output.tag_configure("OK",     foreground="#2ecc71")
        self.output.tag_configure("TIME",   foreground="#4a5a62")  # dim timestamp
        self.output.tag_configure("HEADER", foreground=ACCENT,
                                  font=("Consolas", 10, "bold"))
        for name, color in PROCESS_COLORS.items():
            self.output.tag_configure(f"proc_{name}", foreground=color,
                                      font=("Consolas", 10, "bold"))

    def _build_status_bar(self):
        bar = Frame(self.port_tab, bg=BG_PANEL, padx=12, pady=5)
        bar.pack(fill="x", side="bottom")

        # Colored status dot indicator
        self.status_dot = Label(
            bar, text="●", bg=BG_PANEL, fg="#2ecc71",
            font=("Segoe UI", 9),
        )
        self.status_dot.pack(side="left", padx=(0, 4))

        Label(bar, text="Status:", bg=BG_PANEL, fg=FG_DIM,
              font=("Segoe UI", 9)).pack(side="left")

        self.status_label = Label(
            bar, textvariable=self.status_var,
            bg=BG_PANEL, fg="#2ecc71", font=("Segoe UI", 10, "bold"),
        )
        self.status_label.pack(side="left", padx=(6, 0))

        engine = f"psutil {psutil.__version__}" if PSUTIL_AVAILABLE else "tasklist"
        Label(bar, text=engine, bg=BG_PANEL, fg=FG_DIM,
              font=("Consolas", 8)).pack(side="right")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_button(self, parent, text, cmd,
                     bg=ACCENT, hover=ACCENT_HOVER, width=None):
        btn = Button(
            parent, text=text, command=cmd,
            bg=bg, fg="white", relief="flat",
            font=("Segoe UI", 10, "bold"),
            activebackground=hover, activeforeground="white",
            cursor="hand2", padx=10, pady=6, borderwidth=0,
        )
        if width:
            btn.config(width=width)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _set_status(self, text: str, color: str = "#2ecc71"):
        self.status_var.set(text)
        self.status_label.config(fg=color)
        self.status_dot.config(fg=color)

    def log(self, message: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.output.config(state=NORMAL)
        self.output.insert(END, f"[{ts}]  ", "TIME")
        self.output.insert(END, f"{level:<5}  ",
                           level if level in ("INFO", "WARN", "ERROR", "OK") else "INFO")
        self.output.insert(END, f"{message}\n")
        self.output.see(END)
        self.output.config(state=DISABLED)

    def log_header(self, title: str):
        self.output.config(state=NORMAL)
        self.output.insert(END, f"\n  {title}\n", "HEADER")
        self.output.insert(END, f"  {'─' * 56}\n", "HEADER")
        self.output.see(END)
        self.output.config(state=DISABLED)

    def log_process_name(self, name: str):
        key = "unknown"
        low = (name or "").lower()
        for k in PROCESS_COLORS:
            if k in low:
                key = k
                break
        self.output.config(state=NORMAL)
        self.output.insert(END, f"{name}\n", f"proc_{key}")
        self.output.see(END)
        self.output.config(state=DISABLED)

    def clear_output(self):
        self.output.config(state=NORMAL)
        self.output.delete("1.0", END)
        self.output.config(state=DISABLED)
        self.log("Output cleared.", level="INFO")

    def _validate_port(self) -> "str | None":
        raw = self.port_entry.get().strip()
        if not raw:
            self.log("Port input is empty.", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return None
        if not raw.isdigit():
            self.log(f"Invalid port: '{raw}' is not numeric.", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return None
        port = int(raw)
        if not (0 < port < 65536):
            self.log(f"Port {port} out of range (1–65535).", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return None
        return str(port)

    @staticmethod
    def _classify_process(name: str) -> str:
        low = (name or "").lower()
        for key, label in PROCESS_LABELS.items():
            if key in low:
                return label
        return "Unknown"

    @staticmethod
    def _is_protected(name: str) -> bool:
        return (name or "").lower().strip() in PROTECTED_PROCESSES

    def _get_process_name(self, pid: int) -> str:
        if PSUTIL_AVAILABLE:
            try:
                return psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return "<unknown>"
        try:
            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            first = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
            if first and first.startswith('"'):
                return first.split('","')[0].strip('"')
        except Exception:
            pass
        return "<unknown>"

    # ------------------------------------------------------------------
    # Scanner
    # ------------------------------------------------------------------
    def scan_all_ports(self):
        try:
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception as exc:
            self._set_status("SCAN ERROR", "#e74c3c")
            self.log(f"netstat failed: {exc}", level="ERROR")
            return

        listening: dict[str, int] = {}
        for ln in result.stdout.splitlines():
            if "LISTENING" not in ln.upper():
                continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            m = re.search(r":(\d+)$", parts[1])
            if not m:
                continue
            pid_str = parts[-1]
            if pid_str.isdigit():
                listening[m.group(1)] = int(pid_str)

        self.scan_tree.delete(*self.scan_tree.get_children())
        for port in SCAN_PORTS:
            if port in listening:
                pid   = listening[port]
                name  = self._get_process_name(pid)
                ptype = self._classify_process(name)
                tag   = "protected" if self._is_protected(name) else "occupied"
                self.scan_tree.insert("", "end", values=(
                    port, "OCCUPIED", name, str(pid), ptype,
                ), tags=(tag,))
            else:
                self.scan_tree.insert("", "end", values=(
                    port, "free", "—", "—", "—",
                ), tags=("free",))

        ts = datetime.now().strftime("%H:%M:%S")
        self._scan_time_var.set(f"Last scan: {ts}")
        occupied = sum(1 for p in SCAN_PORTS if p in listening)
        self._set_status(
            f"SCAN COMPLETE  —  {occupied}/{len(SCAN_PORTS)} occupied",
            "#2ecc71" if occupied == 0 else "#f1c40f",
        )

        # Update telemetry sidebar
        self._tv_ports.set(f"{occupied} / {len(SCAN_PORTS)}")
        self._tv_scan.set(ts)
        self._update_telemetry()

    def _on_scan_row_select(self, _event=None):
        sel = self.scan_tree.selection()
        if not sel:
            return
        values = self.scan_tree.item(sel[0], "values")
        port, status = values[0], values[1]
        self.port_entry.delete(0, END)
        self.port_entry.insert(0, port)
        if status == "OCCUPIED":
            self.find_pid()
        else:
            self._set_status(f"Port {port} is free", "#2ecc71")

    # ------------------------------------------------------------------
    # Step 1 — Find PID
    # ------------------------------------------------------------------
    def find_pid(self):
        port = self._validate_port()
        if port is None:
            return
        self.current_port = port
        self.log_header(f"STEP 1  ·  Find PID for port {port}")
        try:
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except FileNotFoundError:
            self.log("`netstat` not found.", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return
        except Exception as exc:
            self.log(f"netstat failed: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        needle   = f":{port}"
        matching = [ln for ln in result.stdout.splitlines() if needle in ln]
        if not matching:
            self.log(f"No netstat entries for port {port}.", level="WARN")
            self.current_pid = None
            self._set_status("READY", "#f1c40f")
            return

        self.log("netstat output (filtered):", level="INFO")
        self.output.config(state=NORMAL)
        for ln in matching:
            self.output.insert(END, f"    {ln}\n")
        self.output.config(state=DISABLED)
        self.output.see(END)

        listening_pid = self._parse_listening_pid(matching, port)
        if listening_pid is None:
            self.log(
                f"No LISTENING entry on port {port}. "
                "Entries are likely ESTABLISHED browser connections, not a server.",
                level="WARN",
            )
            self.current_pid = None
            self._set_status("READY", "#f1c40f")
            return

        self.current_pid = listening_pid
        self.log(f"LISTENING PID: {listening_pid}", level="OK")
        self._set_status("PROCESS FOUND", "#2ecc71")

    def _parse_listening_pid(self, lines: list[str], port: str) -> "int | None":
        for ln in lines:
            if "LISTENING" not in ln.upper():
                continue
            parts = ln.split()
            if len(parts) < 5 or not parts[1].endswith(f":{port}"):
                continue
            pid_str = parts[-1]
            if pid_str.isdigit():
                return int(pid_str)
        return None

    # ------------------------------------------------------------------
    # Step 2 — Verify
    # ------------------------------------------------------------------
    def verify_process(self):
        if self.current_pid is None:
            self.log("No PID stored. Click 'Find PID' first.", level="WARN")
            return
        self.log_header(f"STEP 2  ·  Verify PID {self.current_pid}")
        if PSUTIL_AVAILABLE:
            self._verify_with_psutil(self.current_pid)
        else:
            self._verify_with_tasklist(self.current_pid)

    def _verify_with_psutil(self, pid: int):
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                name = p.name()
                try:    exe = p.exe()
                except Exception: exe = "<access denied>"
                try:    cmdline = " ".join(p.cmdline()) or "<n/a>"
                except Exception: cmdline = "<access denied>"
                status = p.status()

            self.output.config(state=NORMAL)
            self.output.insert(END, "  PID            : ")
            self.output.insert(END, f"{pid}\n", "OK")
            self.output.insert(END, "  Process Name   : ")
            self.output.config(state=DISABLED)
            self.log_process_name(f"  -> {name}")
            self.output.config(state=NORMAL)
            self.output.insert(END, f"  Executable     : {exe}\n")
            self.output.insert(END, f"  Command Line   : {cmdline}\n")
            self.output.insert(END, "  Status         : ")
            self.output.insert(END, f"{status}\n", "OK")
            self.output.config(state=DISABLED)
            self._classify_and_warn(name)
        except psutil.NoSuchProcess:
            self.log(f"PID {pid} no longer exists.", level="WARN")
            self._set_status("READY", "#f1c40f")
        except psutil.AccessDenied:
            self.log(f"Access denied on PID {pid}. Run as Administrator.", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
        except Exception as exc:
            self.log(f"Unexpected error: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")

    def _verify_with_tasklist(self, pid: int):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/V", "/FO", "LIST"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception as exc:
            self.log(f"tasklist failed: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        if "No tasks" in result.stdout or not result.stdout.strip():
            self.log(f"PID {pid} not found in tasklist.", level="WARN")
            self._set_status("READY", "#f1c40f")
            return

        self.output.config(state=NORMAL)
        for ln in result.stdout.splitlines():
            if ln.strip():
                self.output.insert(END, f"  {ln}\n")
        self.output.config(state=DISABLED)
        self.output.see(END)

        m = re.search(r"Image Name:\s*(\S+)", result.stdout)
        if m:
            self._classify_and_warn(m.group(1))

    def _classify_and_warn(self, name: str):
        if self._is_protected(name):
            self.log(f"PROTECTED SYSTEM PROCESS: {name}. Do not kill.", level="ERROR")
            return
        label = self._classify_process(name)
        if label == "Browser":
            self.log(
                f"WARNING: '{name}' looks like a browser. "
                "Browsers connect TO ports — they don't own them.",
                level="WARN",
            )
        elif label == "Unknown":
            self.log(f"Identified: Unknown / generic process ({name}).", level="WARN")
        else:
            self.log(f"Identified: {label} ({name}).", level="OK")

    # ------------------------------------------------------------------
    # Step 3 — Kill
    # ------------------------------------------------------------------
    def kill_process(self):
        if self.current_pid is None:
            self.log("No PID stored. Click 'Find PID' first.", level="WARN")
            return

        name = self._get_process_name(self.current_pid)
        if self._is_protected(name):
            messagebox.showerror(
                "Protected Process — Kill Blocked",
                f"'{name}'  (PID {self.current_pid}) is a protected system process.\n\n"
                "Operation blocked.",
            )
            self.log(f"Kill blocked: '{name}' is protected.", level="ERROR")
            self._set_status("PROTECTED — BLOCKED", "#e74c3c")
            return

        if not messagebox.askyesno(
            "Confirm kill",
            f"Forcefully terminate  {name}  (PID {self.current_pid})"
            f"\non port {self.current_port}?\n\nThis cannot be undone.",
        ):
            self.log("Kill cancelled by user.", level="INFO")
            return

        self.log_header(f"STEP 3  ·  Kill PID {self.current_pid} ({name})")
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(self.current_pid), "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception as exc:
            self.log(f"taskkill failed: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode == 0:
            if stdout:
                self.log(stdout, level="OK")
            self.log(
                f"PID {self.current_pid} terminated. Port {self.current_port} is now free.",
                level="OK",
            )
            self._set_status("PROCESS KILLED", "#2ecc71")
            self.current_pid = None
            self.root.after(500, self.scan_all_ports)
        else:
            msg = stderr or stdout or "taskkill failed."
            if "access is denied" in msg.lower():
                self.log("Access denied. Run as Administrator.", level="ERROR")
            else:
                self.log(f"taskkill error: {msg}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")

    def kill_all_node(self):
        if not messagebox.askyesno(
            "Kill ALL Node processes",
            "Forcefully terminate EVERY node.exe process on this machine?\n\nProceed?",
        ):
            self.log("Kill-all-node cancelled.", level="INFO")
            return

        self.log_header("Kill ALL node.exe processes")
        try:
            result = subprocess.run(
                ["taskkill", "/IM", "node.exe", "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception as exc:
            self.log(f"taskkill failed: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            self.log(output or "All node.exe processes terminated.", level="OK")
            self._set_status("PROCESS KILLED", "#2ecc71")
        else:
            if "not found" in output.lower():
                self.log("No node.exe processes were running.", level="INFO")
                self._set_status("READY", "#2ecc71")
            else:
                self.log(output or "taskkill failed.", level="ERROR")
                self._set_status("ERROR", "#e74c3c")

        self.root.after(500, self.scan_all_ports)

    # ------------------------------------------------------------------
    # Extras
    # ------------------------------------------------------------------
    def open_in_browser(self):
        port = self._validate_port()
        if port is None:
            return
        url = f"http://localhost:{port}"
        try:
            webbrowser.open(url, new=2)
            self.log(f"Opened {url} in default browser.", level="INFO")
        except Exception as exc:
            self.log(f"Failed to open browser: {exc}", level="ERROR")

    def _toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            self.log("Auto-refresh enabled (every 5 seconds).", level="INFO")
            self._tv_auto.set("ON (5s)")
            self._auto_refresh_tick()
        else:
            self.log("Auto-refresh disabled.", level="INFO")
            self._tv_auto.set("off")
            if self._auto_refresh_job is not None:
                try:
                    self.root.after_cancel(self._auto_refresh_job)
                except Exception:
                    pass
                self._auto_refresh_job = None

    def _auto_refresh_tick(self):
        if not self.auto_refresh_var.get():
            return
        try:
            self.scan_all_ports()
        except Exception as exc:
            self.log(f"Auto-refresh error: {exc}", level="ERROR")
        self._auto_refresh_job = self.root.after(5000, self._auto_refresh_tick)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    root = Tk()
    try:
        root.option_add("*Font", "Segoe\\ UI 10")
    except Exception:
        pass
    app = PortProcessManager(root)

    def on_close():
        if app._auto_refresh_job is not None:
            try:
                root.after_cancel(app._auto_refresh_job)
            except Exception:
                pass
        app.runtime_panel.cancel_auto()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
