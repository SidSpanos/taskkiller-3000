Port Process Manager

Windows Python GUI utility for identifying, verifying, and killing processes occupying localhost ports.

Features
Find LISTENING process by port
Verify process executable and command line
Kill process safely
Ignore ESTABLISHED browser sessions
Manual port input
Tkinter GUI
Windows focused workflow
Supported Ports

Common development ports include:

3000
3001
5173
8080
11434
Requirements
Python 3
Windows
Optional:
psutil

Install psutil:

pip install psutil
Run
python port_manager.py

Or:

py port_manager.py
Purpose

This utility helps developers quickly identify which application owns a localhost port and safely terminate the correct LISTENING process without confusing browser ESTABLISHED sessions with the actual hosted application.

Useful when working with:

Node.js
React
Vite
Next.js
Ollama
Docker
Electron
Python web servers
Local AI tooling
Notes
LISTENING processes are the actual applications hosting the port.
ESTABLISHED connections are typically browser/client sessions connected to the application.
Killing the LISTENING process frees the port.
Killing ESTABLISHED sessions only disconnects clients temporarily.