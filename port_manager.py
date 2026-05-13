"""
Port Process Manager
====================
A Windows desktop application to identify and kill processes
that are listening on specific localhost ports (e.g. 3000, 5173, 8080).

Author: Generated for Isidoros
Requires: Python 3.x, tkinter (bundled with Python), psutil (optional but recommended)

Install dependency (optional but recommended):
    pip install psutil

Run:
    python port_manager.py
"""

import os
import re
import sys
import subprocess
import threading
import webbrowser
from datetime import datetime
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar, StringVar,
    IntVar, Checkbutton, END, DISABLED, NORMAL, messagebox
)

# Try to import psutil (preferred). Fall back to `tasklist` if missing.
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Theme constants (dark theme)
# ---------------------------------------------------------------------------
BG_DARK       = "#1e1e1e"
BG_PANEL      = "#252526"
BG_OUTPUT     = "#0f0f0f"
FG_TEXT       = "#e6e6e6"
FG_DIM        = "#a0a0a0"
ACCENT        = "#007acc"
ACCENT_HOVER  = "#1a8fdc"
BTN_KILL      = "#c0392b"
BTN_KILL_HVR  = "#e04030"
BTN_VERIFY    = "#27ae60"
BTN_VERIFY_HV = "#2ecc71"
BTN_QUICK     = "#3c3c3c"
BTN_QUICK_HV  = "#505050"

# Colors used to tag process names in the output
PROCESS_COLORS = {
    "node":     "#2ecc71",   # green
    "python":   "#3498db",   # blue
    "docker":   "#1abc9c",   # teal
    "bun":      "#f1c40f",   # yellow
    "npm":      "#2ecc71",   # green
    "chrome":   "#f39c12",   # yellow / orange
    "msedge":   "#f39c12",
    "firefox":  "#f39c12",
    "electron": "#9b59b6",
    "unknown":  "#e74c3c",   # red
}

QUICK_PORTS = ["3000", "3001", "5173", "8080", "11434"]


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class PortProcessManager:
    """The main GUI application class."""

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Port Process Manager")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_DARK)

        # Internal state
        self.current_pid: int | None = None
        self.current_port: str | None = None
        self.auto_refresh_var = IntVar(value=0)
        self.status_var = StringVar(value="READY")
        self._auto_refresh_job = None

        # Build UI
        self._build_top_section()
        self._build_quick_ports()
        self._build_action_buttons()
        self._build_output_area()
        self._build_status_bar()

        # First log line
        self.log("Application started.", level="INFO")
        if not PSUTIL_AVAILABLE:
            self.log("psutil not detected. Falling back to 'tasklist'. "
                     "Run 'pip install psutil' for richer details.",
                     level="WARN")
        else:
            self.log("psutil detected. Using rich process inspection.",
                     level="INFO")

    # ---------------------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------------------
    def _build_top_section(self):
        """Port entry + main action buttons row."""
        top = Frame(self.root, bg=BG_PANEL, padx=12, pady=10)
        top.pack(fill="x", padx=10, pady=(10, 4))

        Label(
            top, text="Port:", bg=BG_PANEL, fg=FG_TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 8))

        self.port_entry = Entry(
            top, width=10, font=("Consolas", 12),
            bg=BG_OUTPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=ACCENT
        )
        self.port_entry.insert(0, "3000")
        self.port_entry.pack(side="left", padx=(0, 12), ipady=4)
        self.port_entry.bind("<Return>", lambda e: self.find_pid())

        # Auto-refresh checkbox
        self.auto_chk = Checkbutton(
            top, text="Auto Refresh (3s)", variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
            bg=BG_PANEL, fg=FG_TEXT, selectcolor=BG_DARK,
            activebackground=BG_PANEL, activeforeground=FG_TEXT,
            font=("Segoe UI", 10)
        )
        self.auto_chk.pack(side="right")

        # Open in Browser button
        self._make_button(
            top, "Open in Browser", self.open_in_browser,
            bg=BTN_QUICK, hover=BTN_QUICK_HV
        ).pack(side="right", padx=(0, 10))

    def _build_quick_ports(self):
        """A horizontal row of quick-pick port buttons."""
        bar = Frame(self.root, bg=BG_DARK, padx=12, pady=4)
        bar.pack(fill="x", padx=10)

        Label(
            bar, text="Quick Ports:", bg=BG_DARK, fg=FG_DIM,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 8))

        for p in QUICK_PORTS:
            self._make_button(
                bar, p, lambda port=p: self._set_quick_port(port),
                bg=BTN_QUICK, hover=BTN_QUICK_HV, width=8
            ).pack(side="left", padx=2)

        # Kill all node processes shortcut on the right
        self._make_button(
            bar, "Kill All Node Processes", self.kill_all_node,
            bg=BTN_KILL, hover=BTN_KILL_HVR
        ).pack(side="right")

    def _build_action_buttons(self):
        """The three main step buttons: Find PID / Verify / Kill."""
        actions = Frame(self.root, bg=BG_DARK, padx=12, pady=8)
        actions.pack(fill="x", padx=10)

        self._make_button(
            actions, "1) Find PID", self.find_pid,
            bg=ACCENT, hover=ACCENT_HOVER, width=18
        ).pack(side="left", padx=4)

        self._make_button(
            actions, "2) Verify Process", self.verify_process,
            bg=BTN_VERIFY, hover=BTN_VERIFY_HV, width=18
        ).pack(side="left", padx=4)

        self._make_button(
            actions, "3) Kill Process", self.kill_process,
            bg=BTN_KILL, hover=BTN_KILL_HVR, width=18
        ).pack(side="left", padx=4)

        self._make_button(
            actions, "Clear Output", self.clear_output,
            bg=BTN_QUICK, hover=BTN_QUICK_HV, width=14
        ).pack(side="right", padx=4)

    def _build_output_area(self):
        """The big scrollable console output."""
        wrapper = Frame(self.root, bg=BG_DARK, padx=12, pady=6)
        wrapper.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self.output = Text(
            wrapper, wrap="word", bg=BG_OUTPUT, fg=FG_TEXT,
            insertbackground=FG_TEXT, font=("Consolas", 10),
            relief="flat", padx=10, pady=10, state=DISABLED
        )
        self.output.pack(side="left", fill="both", expand=True)

        sb = Scrollbar(wrapper, command=self.output.yview)
        sb.pack(side="right", fill="y")
        self.output.config(yscrollcommand=sb.set)

        # Configure text tags for coloring
        self.output.tag_configure("INFO",  foreground="#cfcfcf")
        self.output.tag_configure("WARN",  foreground="#f1c40f")
        self.output.tag_configure("ERROR", foreground="#e74c3c")
        self.output.tag_configure("OK",    foreground="#2ecc71")
        self.output.tag_configure("TIME",  foreground="#7f8c8d")
        self.output.tag_configure("HEADER",
                                  foreground=ACCENT,
                                  font=("Consolas", 10, "bold"))
        for name, color in PROCESS_COLORS.items():
            self.output.tag_configure(f"proc_{name}",
                                      foreground=color,
                                      font=("Consolas", 10, "bold"))

    def _build_status_bar(self):
        """Bottom status bar showing READY / PROCESS FOUND / KILLED / ERROR."""
        bar = Frame(self.root, bg=BG_PANEL, padx=12, pady=6)
        bar.pack(fill="x", side="bottom")

        Label(
            bar, text="Status:", bg=BG_PANEL, fg=FG_DIM,
            font=("Segoe UI", 9)
        ).pack(side="left")

        self.status_label = Label(
            bar, textvariable=self.status_var,
            bg=BG_PANEL, fg="#2ecc71",
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(side="left", padx=8)

        engine = "psutil" if PSUTIL_AVAILABLE else "tasklist (fallback)"
        Label(
            bar, text=f"Inspection engine: {engine}",
            bg=BG_PANEL, fg=FG_DIM, font=("Segoe UI", 9)
        ).pack(side="right")

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _make_button(self, parent, text, cmd,
                     bg=ACCENT, hover=ACCENT_HOVER, width=None):
        """Build a flat-styled button with hover effect."""
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

    def _set_quick_port(self, port: str):
        """Populate the port entry from a quick-pick button."""
        self.port_entry.delete(0, END)
        self.port_entry.insert(0, port)
        self.find_pid()

    def _set_status(self, text: str, color: str = "#2ecc71"):
        self.status_var.set(text)
        self.status_label.config(fg=color)

    def log(self, message: str, level: str = "INFO"):
        """Append a timestamped, color-tagged message to the output area."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.output.config(state=NORMAL)
        self.output.insert(END, f"[{ts}] ", "TIME")
        self.output.insert(END, f"{level:<5} ", level if level in
                           ("INFO", "WARN", "ERROR", "OK") else "INFO")
        self.output.insert(END, f"{message}\n")
        self.output.see(END)
        self.output.config(state=DISABLED)

    def log_header(self, title: str):
        """Bold accent-colored section header in the output."""
        self.output.config(state=NORMAL)
        self.output.insert(END, f"\n{'=' * 60}\n", "HEADER")
        self.output.insert(END, f"  {title}\n", "HEADER")
        self.output.insert(END, f"{'=' * 60}\n", "HEADER")
        self.output.see(END)
        self.output.config(state=DISABLED)

    def log_process_name(self, name: str):
        """Color the process name based on what it is."""
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

    def _validate_port(self) -> str | None:
        """Return a validated port string or None if invalid."""
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
            self.log(f"Port {port} is out of range (1-65535).", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return None
        return str(port)

    # ---------------------------------------------------------------------
    # STEP 1 - Find PID via netstat
    # ---------------------------------------------------------------------
    def find_pid(self):
        """Run `netstat -ano | findstr :PORT` and extract the LISTENING PID."""
        port = self._validate_port()
        if port is None:
            return
        self.current_port = port
        self.log_header(f"STEP 1: Finding PID for port {port}")

        try:
            # Use netstat -ano (numeric, no DNS) and filter by port.
            # We do the filtering in Python so we can keep raw output.
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except FileNotFoundError:
            self.log("`netstat` not found. Are you sure this is Windows?",
                     level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return
        except Exception as exc:
            self.log(f"Failed to run netstat: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        if result.returncode != 0 and not result.stdout:
            self.log(f"netstat returned non-zero: {result.stderr.strip()}",
                     level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        # Filter lines containing :PORT (mirrors `findstr :PORT`)
        needle = f":{port}"
        matching = [ln for ln in result.stdout.splitlines() if needle in ln]

        if not matching:
            self.log(f"No netstat entries found for port {port}.",
                     level="WARN")
            self.current_pid = None
            self._set_status("READY", "#f1c40f")
            return

        self.log("Raw netstat output (filtered):", level="INFO")
        self.output.config(state=NORMAL)
        for ln in matching:
            self.output.insert(END, f"    {ln}\n")
        self.output.config(state=DISABLED)
        self.output.see(END)

        listening_pid = self._parse_listening_pid(matching, port)
        if listening_pid is None:
            self.log(
                f"No LISTENING entry on port {port}. "
                "Entries shown are likely ESTABLISHED browser connections "
                "(e.g. Chrome talking to a server) and are NOT the server "
                "itself. Start your server or pick another port.",
                level="WARN"
            )
            self.current_pid = None
            self._set_status("READY", "#f1c40f")
            return

        self.current_pid = listening_pid
        self.log(f"Detected LISTENING PID: {listening_pid}", level="OK")
        self._set_status("PROCESS FOUND", "#2ecc71")

    def _parse_listening_pid(self, lines, port: str) -> int | None:
        """
        Parse netstat output and return the PID of the LISTENING entry, if any.

        Sample netstat -ano line:
            TCP    0.0.0.0:3000     0.0.0.0:0     LISTENING       12345
            TCP    127.0.0.1:51234  127.0.0.1:3000 ESTABLISHED     67890

        We deliberately ignore ESTABLISHED rows - those are clients
        (e.g. Chrome) talking to a server, not the server itself.
        """
        for ln in lines:
            if "LISTENING" not in ln.upper():
                continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            local_addr = parts[1]
            # Match the port at the END of the local address: ...:PORT
            if not local_addr.endswith(f":{port}"):
                continue
            pid_str = parts[-1]
            if pid_str.isdigit():
                return int(pid_str)
        return None

    # ---------------------------------------------------------------------
    # STEP 2 - Verify process details
    # ---------------------------------------------------------------------
    def verify_process(self):
        """Show name, exe path, command line and status for the current PID."""
        if self.current_pid is None:
            self.log("No PID stored. Click 'Find PID' first.", level="WARN")
            return

        self.log_header(f"STEP 2: Verifying PID {self.current_pid}")

        if PSUTIL_AVAILABLE:
            self._verify_with_psutil(self.current_pid)
        else:
            self._verify_with_tasklist(self.current_pid)

    def _verify_with_psutil(self, pid: int):
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                name = p.name()
                try:
                    exe = p.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    exe = "<access denied>"
                try:
                    cmdline = " ".join(p.cmdline()) or "<n/a>"
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = "<access denied>"
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
            self.log(f"Access denied inspecting PID {pid}. "
                     "Try running as Administrator.", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
        except Exception as exc:
            self.log(f"Unexpected error inspecting PID {pid}: {exc}",
                     level="ERROR")
            self._set_status("ERROR", "#e74c3c")

    def _verify_with_tasklist(self, pid: int):
        """Fallback when psutil is not installed."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/V", "/FO", "LIST"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except Exception as exc:
            self.log(f"Failed to run tasklist: {exc}", level="ERROR")
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
        """Identify well-known process types and warn if it's a browser."""
        low = (name or "").lower()
        if "node" in low:
            self.log("Identified: Node.js process.", level="OK")
        elif "python" in low:
            self.log("Identified: Python process.", level="OK")
        elif "docker" in low:
            self.log("Identified: Docker process.", level="OK")
        elif "bun" in low:
            self.log("Identified: Bun runtime.", level="OK")
        elif "npm" in low:
            self.log("Identified: npm process.", level="OK")
        elif "electron" in low:
            self.log("Identified: Electron app.", level="OK")
        elif any(b in low for b in ("chrome", "msedge", "firefox", "brave")):
            self.log(
                "WARNING: This looks like a browser. Browsers usually only "
                "CONNECT to a port (ESTABLISHED), they do not OWN it. "
                "Step 1 should already have ignored these. Double-check "
                "before killing.", level="WARN"
            )
        else:
            self.log("Identified: Unknown / generic process.", level="WARN")

    # ---------------------------------------------------------------------
    # STEP 3 - Kill the process
    # ---------------------------------------------------------------------
    def kill_process(self):
        """Confirm and then run `taskkill /PID <pid> /F`."""
        if self.current_pid is None:
            self.log("No PID stored. Click 'Find PID' first.", level="WARN")
            return

        if not messagebox.askyesno(
            "Confirm kill",
            f"Forcefully terminate PID {self.current_pid}"
            f" on port {self.current_port}?\n\nThis cannot be undone."
        ):
            self.log("Kill cancelled by user.", level="INFO")
            return

        self.log_header(f"STEP 3: Killing PID {self.current_pid}")

        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(self.current_pid), "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except Exception as exc:
            self.log(f"Failed to run taskkill: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            if stdout:
                self.log(stdout, level="OK")
            self.log(
                f"PID {self.current_pid} terminated. "
                f"Port {self.current_port} should now be free.",
                level="OK"
            )
            self._set_status("PROCESS KILLED", "#2ecc71")
            self.current_pid = None
        else:
            msg = stderr or stdout or "taskkill failed."
            if "Access is denied" in msg or "denied" in msg.lower():
                self.log(
                    f"Access denied killing PID {self.current_pid}. "
                    "Try running this app as Administrator.",
                    level="ERROR"
                )
            else:
                self.log(f"taskkill error: {msg}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")

    def kill_all_node(self):
        """Optional: kill every node.exe process on the machine."""
        if not messagebox.askyesno(
            "Kill ALL Node processes",
            "This will forcefully terminate EVERY node.exe process "
            "on this machine.\n\nProceed?"
        ):
            self.log("Kill-all-node cancelled.", level="INFO")
            return

        self.log_header("Killing ALL node.exe processes")
        try:
            result = subprocess.run(
                ["taskkill", "/IM", "node.exe", "/F"],
                capture_output=True, text=True, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except Exception as exc:
            self.log(f"Failed to run taskkill: {exc}", level="ERROR")
            self._set_status("ERROR", "#e74c3c")
            return

        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            self.log(output or "All node.exe processes terminated.",
                     level="OK")
            self._set_status("PROCESS KILLED", "#2ecc71")
        else:
            if "not found" in output.lower():
                self.log("No node.exe processes were running.", level="INFO")
                self._set_status("READY", "#2ecc71")
            else:
                self.log(output or "taskkill failed.", level="ERROR")
                self._set_status("ERROR", "#e74c3c")

    # ---------------------------------------------------------------------
    # Extras
    # ---------------------------------------------------------------------
    def open_in_browser(self):
        """Open http://localhost:<port> in the default browser."""
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
        """Turn the 3-second auto refresh loop on/off."""
        if self.auto_refresh_var.get():
            self.log("Auto-refresh enabled (every 3 seconds).", level="INFO")
            self._auto_refresh_tick()
        else:
            self.log("Auto-refresh disabled.", level="INFO")
            if self._auto_refresh_job is not None:
                try:
                    self.root.after_cancel(self._auto_refresh_job)
                except Exception:
                    pass
                self._auto_refresh_job = None

    def _auto_refresh_tick(self):
        """Run Find PID, then schedule the next tick."""
        if not self.auto_refresh_var.get():
            return
        # Run in a thread so a slow netstat doesn't freeze the UI
        threading.Thread(target=self._safe_find_pid, daemon=True).start()
        self._auto_refresh_job = self.root.after(3000, self._auto_refresh_tick)

    def _safe_find_pid(self):
        try:
            self.find_pid()
        except Exception as exc:
            self.log(f"Auto-refresh error: {exc}", level="ERROR")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    root = Tk()
    try:
        # Use a nicer default font on Windows
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
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
