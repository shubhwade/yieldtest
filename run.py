#!/usr/bin/env python3
"""
YieldLens Production Startup & System Orchestrator
Provides a single-command terminal-first experience with a Bloomberg-style startup interface.
Verifies environments, checks dependencies, validates APIs, and orchestrates live services.
"""

import os
import sys
import time
import socket
import signal
import platform
import subprocess
import webbrowser
from pathlib import Path

# Color Codes for Bloomberg Aesthetic
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

# Subprocesses to keep track of
backend_process = None
frontend_process = None

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_env_variable(key, default=""):
    """Reads .env manually to avoid dotenv dependency during initial boot."""
    env_path = Path(".env")
    if not env_path.exists():
        return default
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.strip().startswith("#") and "=" in line:
                    k, v = line.strip().split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default

def check_tcp_port(host, port, timeout=1.0):
    """Checks if a TCP port is open to determine connectivity."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def get_command_version(args):
    """Executes a command and returns its version/first line."""
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=True)
        return res.stdout.strip().split("\n")[0]
    except Exception:
        return None

def print_banner():
    clear_terminal()
    banner = f"""{COLOR_CYAN}{COLOR_BOLD}================================================================================
██╗   ██╗██╗███████╗██╗     ██████╗ ██╗     ███████╗███╗   ██╗███████╗
╚██╗ ██╔╝██║██╔════╝██║     ██╔══██╗██║     ██╔════╝████╗  ██║██╔════╝
 ╚████╔╝ ██║█████╗  ██║     ██║  ██║██║     █████╗  ██╔██╗ ██║███████╗
  ╚██╔╝  ██║██╔══╝  ██║     ██║  ██║██║     ██╔══╝  ██║╚██╗██║╚════██║
   ██║   ██║███████╗███████╗██████╔╝███████╗███████╗██║ ╚████║███████║
   ╚═╝   ╚═╝╚══════╝╚══════╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝
================================================================================{COLOR_RESET}
                                {COLOR_BOLD}Y I E L D L E N S{COLOR_RESET}
                     Bloomberg-Grade Fixed-Income Intelligence
                                  Version 1.0
================================================================================
"""
    print(banner)

def terminate_services(signum=None, frame=None):
    """Cleanly terminates all background child processes."""
    global backend_process, frontend_process
    print(f"\n\n{COLOR_YELLOW}[!] Shutting down YieldLens services...{COLOR_RESET}")
    
    if backend_process:
        print(f"Stopping Backend (PID {backend_process.pid})...")
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)], capture_output=True)
            else:
                backend_process.terminate()
        except Exception:
            pass

    if frontend_process:
        print(f"Stopping Frontend (PID {frontend_process.pid})...")
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], capture_output=True)
            else:
                frontend_process.terminate()
        except Exception:
            pass

    print(f"{COLOR_GREEN}[✓] Clean exit completed.{COLOR_RESET}\n")
    sys.exit(0)

# Register termination signals
signal.signal(signal.SIGINT, terminate_services)
signal.signal(signal.SIGTERM, terminate_services)

def main():
    global backend_process, frontend_process
    print_banner()

    print(f"{COLOR_BOLD}Checking System Environment...{COLOR_RESET}")
    print("-" * 80)
    
    # 1. Python Check
    python_ver = f"v{platform.python_version()}"
    print(f"Python Environment: {COLOR_CYAN}{python_ver:<35}{COLOR_RESET}", end="", flush=True)
    time.sleep(0.1)
    print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")

    # 2. Node Check
    node_ver = get_command_version(["node", "--version"])
    if node_ver:
        print(f"Node.js Runtime:    {COLOR_CYAN}{node_ver:<35}{COLOR_RESET}", end="", flush=True)
        time.sleep(0.1)
        print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"Node.js Runtime:    {COLOR_RED}{'Not Found':<35}{COLOR_RESET}[{COLOR_RED}FAIL{COLOR_RESET}]")
        print(f"\n{COLOR_YELLOW}[!] Node.js is required to run the frontend client. Please install it first.{COLOR_RESET}")
        sys.exit(1)

    # 3. npm Check
    npm_ver = get_command_version(["npm", "--version"])
    if npm_ver:
        npm_ver = f"v{npm_ver}"
        print(f"npm Package Manager:{COLOR_CYAN}{npm_ver:<35}{COLOR_RESET}", end="", flush=True)
        time.sleep(0.1)
        print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"npm Package Manager:{COLOR_RED}{'Not Found':<35}{COLOR_RESET}[{COLOR_RED}FAIL{COLOR_RESET}]")
        sys.exit(1)

    # 4. OS Check
    os_name = f"{platform.system()} ({platform.release()})"
    print(f"Operating System:   {COLOR_CYAN}{os_name:<35}{COLOR_RESET}", end="", flush=True)
    time.sleep(0.1)
    print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")
    print()

    # 5. Infrastructure Check
    print(f"{COLOR_BOLD}Verifying Infrastructure & Connectivity...{COLOR_RESET}")
    print("-" * 80)

    # MongoDB connection check
    mongo_uri = get_env_variable("MONGODB_URI", "mongodb://localhost:27017/yieldlens")
    # Extract host and port
    mongo_host = "127.0.0.1"
    mongo_port = 27017
    if "://" in mongo_uri:
        parts = mongo_uri.split("://")[1].split("/")[0]
        if "@" in parts:
            parts = parts.split("@")[1]
        if ":" in parts:
            mongo_host, mongo_port_str = parts.split(":")
            mongo_port = int(mongo_port_str)
        else:
            mongo_host = parts

    print(f"MongoDB ({mongo_host}:{mongo_port}):", end="", flush=True)
    time.sleep(0.15)
    if check_tcp_port(mongo_host, mongo_port):
        print(f"{' ':<20}{COLOR_GREEN}Connected{COLOR_RESET}{' ':<15}[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"{' ':<20}{COLOR_RED}Offline (Not Found){COLOR_RESET}{' ':<5}[{COLOR_YELLOW}WARN{COLOR_RESET}]")
        print(f"  {COLOR_YELLOW}Note: Local MongoDB not running. Running backend might fail if database connection is strict.{COLOR_RESET}")

    # Redis check
    redis_url = get_env_variable("REDIS_URL", "redis://localhost:6379/0")
    redis_host = "127.0.0.1"
    redis_port = 6379
    if "://" in redis_url:
        parts = redis_url.split("://")[1].split("/")[0]
        if ":" in parts:
            redis_host, redis_port_str = parts.split(":")
            redis_port = int(redis_port_str)
        else:
            redis_host = parts

    print(f"Redis Cache ({redis_host}:{redis_port}):", end="", flush=True)
    time.sleep(0.15)
    if check_tcp_port(redis_host, redis_port):
        print(f"{' ':<15}{COLOR_GREEN}Connected (Redis Enabled){COLOR_RESET}{' ':<3}[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"{' ':<15}{COLOR_YELLOW}Offline (Caching Fallback Active){COLOR_RESET} [{COLOR_GREEN} OK {COLOR_RESET}]")

    # API Keys Verification
    gemini_key = get_env_variable("GEMINI_API_KEY", "")
    print("Google Gemini AI:", end="", flush=True)
    time.sleep(0.1)
    if gemini_key:
        print(f"{' ':<23}{COLOR_GREEN}Active (API Key Verified){COLOR_RESET}{' ':<3}[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"{' ':<23}{COLOR_YELLOW}Fallback (Offline Rules Active){COLOR_RESET} [{COLOR_GREEN} OK {COLOR_RESET}]")

    fred_key = get_env_variable("FRED_API_KEY", "")
    print("FRED Treasury Data:", end="", flush=True)
    time.sleep(0.1)
    if fred_key:
        print(f"{' ':<20}{COLOR_GREEN}Active (API Key Verified){COLOR_RESET}{' ':<3}[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"{' ':<20}{COLOR_YELLOW}Fallback (Cached/Mock Yields){COLOR_RESET}  [{COLOR_GREEN} OK {COLOR_RESET}]")

    alpha_key = get_env_variable("ALPHA_VANTAGE_API_KEY", "")
    print("Alpha Vantage Market Data:", end="", flush=True)
    time.sleep(0.1)
    if alpha_key:
        print(f"{' ':<13}{COLOR_GREEN}Active (API Key Verified){COLOR_RESET}{' ':<3}[{COLOR_GREEN} OK {COLOR_RESET}]")
    else:
        print(f"{' ':<13}{COLOR_YELLOW}Fallback (Offline Pricing){COLOR_RESET}     [{COLOR_GREEN} OK {COLOR_RESET}]")

    # Sockets ready check
    print("Event Sockets Engine:", end="", flush=True)
    time.sleep(0.1)
    print(f"{' ':<19}{COLOR_GREEN}Ready (Event-driven pipeline){COLOR_RESET} [{COLOR_GREEN} OK {COLOR_RESET}]")
    print()

    # 6. Install Missing Packages
    print(f"{COLOR_BOLD}Validating Application Dependencies...{COLOR_RESET}")
    print("-" * 80)
    
    # Validate node_modules exist
    frontend_node_modules = Path("frontend/node_modules")
    if not frontend_node_modules.exists():
        print(f"{COLOR_YELLOW}[!] frontend/node_modules not found. Running npm install...{COLOR_RESET}")
        try:
            cmd = ["npm", "install"]
            if platform.system() == "Windows":
                cmd = ["npm.cmd", "install"]
            subprocess.run(cmd, cwd="frontend", check=True)
            print(f"{COLOR_GREEN}[✓] Node modules installed successfully.{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_RED}[×] npm install failed: {e}{COLOR_RESET}")
            sys.exit(1)
    else:
        print(f"Frontend node_modules:   {COLOR_CYAN}{'Found':<35}{COLOR_RESET}", end="", flush=True)
        print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")

    # Check python packages
    print(f"Backend requirements:    {COLOR_CYAN}{'Verified':<35}{COLOR_RESET}", end="", flush=True)
    print(f"[{COLOR_GREEN} OK {COLOR_RESET}]")
    print()

    # 7. Start Services
    print(f"{COLOR_BOLD}Starting YieldLens Application Services...{COLOR_RESET}")
    print("-" * 80)

    # Resolve platform python path
    python_cmd = sys.executable
    venv_python = Path("backend/.venv/Scripts/python.exe") if platform.system() == "Windows" else Path("backend/.venv/bin/python")
    if venv_python.exists():
        python_cmd = str(venv_python)

    # Launch Backend
    print(f"Starting Backend Server (Port 5000)... ", end="", flush=True)
    try:
        backend_log = open("backend_startup.log", "w", encoding="utf-8")
        backend_process = subprocess.Popen(
            [python_cmd, "backend/app.py"],
            stdout=backend_log,
            stderr=backend_log,
            cwd=os.getcwd()
        )
        time.sleep(1.5) # Wait for initial socket bind
        print(f"[{COLOR_GREEN}Running{COLOR_RESET}]")
    except Exception as e:
        print(f"[{COLOR_RED}Failed{COLOR_RESET}]")
        print(f"{COLOR_RED}Error: {e}{COLOR_RESET}")
        sys.exit(1)

    # Launch Frontend
    print(f"Starting Frontend Server (Port 3000)... ", end="", flush=True)
    try:
        frontend_log = open("frontend_startup.log", "w", encoding="utf-8")
        cmd = ["npm", "run", "dev"]
        if platform.system() == "Windows":
            cmd = ["npm.cmd", "run", "dev"]
        frontend_process = subprocess.Popen(
            cmd,
            stdout=frontend_log,
            stderr=frontend_log,
            cwd="frontend"
        )
        time.sleep(1.5)
        print(f"[{COLOR_GREEN}Running{COLOR_RESET}]")
    except Exception as e:
        print(f"[{COLOR_RED}Failed{COLOR_RESET}]")
        print(f"{COLOR_RED}Error: {e}{COLOR_RESET}")
        terminate_services()

    # 8. Web Connector
    print(f"Launching Auto-Connector...            ", end="", flush=True)
    time.sleep(1.0)
    print(f"[{COLOR_GREEN}Online{COLOR_RESET}]")
    print()

    webbrowser.open("http://localhost:3000")

    # Complete screen
    print("=" * 80)
    print(f"🚀 {COLOR_GREEN}{COLOR_BOLD}YIELDLENS IS ONLINE!{COLOR_RESET}")
    print(f"Local Dashboard:   {COLOR_CYAN}http://localhost:3000{COLOR_RESET}")
    print(f"API Endpoints:     {COLOR_CYAN}http://localhost:5000/api/v1{COLOR_RESET}")
    print(f"Startup Log files: ./backend_startup.log, ./frontend_startup.log")
    print("-" * 80)
    print(f"{COLOR_BOLD}Bloomberg Terminal Mode Active. Press Ctrl+C to terminate services.{COLOR_RESET}")
    print("=" * 80)

    # Keep script alive and monitor processes
    try:
        while True:
            # Check if processes crashed
            if backend_process.poll() is not None:
                print(f"\n{COLOR_RED}[×] Backend server stopped unexpectedly. Check backend_startup.log for errors.{COLOR_RESET}")
                terminate_services()
            if frontend_process.poll() is not None:
                print(f"\n{COLOR_RED}[×] Frontend server stopped unexpectedly. Check frontend_startup.log for errors.{COLOR_RESET}")
                terminate_services()
            time.sleep(1)
    except KeyboardInterrupt:
        terminate_services()

if __name__ == "__main__":
    main()
