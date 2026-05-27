# Installation Guide

This document provides step-by-step terminal instructions to install and configure the prerequisites for running **YieldLens** across different operating systems.

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
1. **Python (3.10 or 3.11)**
2. **Node.js (v18 or v20)**
3. **MongoDB Community Server** (running locally on port 27017)
4. **Redis Cache Server** (running locally on port 6379)

---

## 🏁 Automated Single-Command Startup (Recommended)

YieldLens comes with an automated startup orchestrator that handles virtual environment configuration, dependencies, and launch sequences in one command:

```bash
# Clone and enter the repository
git clone https://github.com/shubhwade/yieldtest.git
cd yieldlens

# Run the single startup utility
python run.py

# OR run via npm script wrapper
npm start
```
*Note: Make sure your local MongoDB and Redis servers are started before running this command (see instructions below).*

---

## 🪟 Windows Setup Guide

### 1. Install Runtimes
- **Python**: Download and run the [Python 3.10 Installer](https://www.python.org/downloads/). Ensure **"Add Python to PATH"** is checked.
- **Node.js**: Download and run the [Node.js MSI Installer](https://nodejs.org/).

### 2. Start MongoDB
- Download and run the [MongoDB Community Server MSI](https://www.mongodb.com/try/download/community).
- By default, MongoDB is installed and registered as a Windows Service, meaning it will boot automatically in the background.
- If it is not running, start it from an Administrator command prompt:
  ```cmd
  net start MongoDB
  ```

### 3. Start Redis
- Redis is natively built for Linux, but can be run on Windows via **WSL (Windows Subsystem for Linux)** or via Memurai.
- If running Redis in WSL, start it in your Linux terminal:
  ```bash
  sudo service redis-server start
  ```

---

## 🍎 macOS Setup Guide

### 1. Install Homebrew
If you do not have Homebrew installed, open your Terminal and run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Runtimes & Services
Use Homebrew to install everything in one go:
```bash
# Install runtimes
brew install python@3.10 node

# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community@7.0

# Install Redis
brew install redis
```

### 3. Start Services
Start MongoDB and Redis in the background:
```bash
# Start MongoDB Service
brew services start mongodb-community@7.0

# Start Redis Service
brew services start redis
```

---

## 🐧 Linux (Ubuntu/Debian) Setup Guide

### 1. Install Runtimes & Redis
Open your terminal and run:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm redis-server
```

### 2. Install MongoDB
Import the public key and add the repository:
```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg --ooc /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y mongodb-org
```

### 3. Start Services
```bash
# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```
