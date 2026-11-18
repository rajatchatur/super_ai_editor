# 📦 Installation & Setup Guide — super_ai_editor

This guide provides step-by-step instructions to get **`super_ai_editor`** up and running on **macOS** and **Windows 10 / 11** with zero errors.

---

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Method A: Docker Installation (Recommended)](#2-method-a-docker-installation-recommended)
3. [Method B: Native macOS Installation](#3-method-b-native-macos-installation)
4. [Method C: Native Windows 10 / 11 Installation](#4-method-c-native-windows-10--11-installation)
5. [Ollama Local AI Setup & RAM Optimization](#5-ollama-local-ai-setup--ram-optimization)
6. [Troubleshooting & FAQs](#6-troubleshooting--faqs)

---

## 1. Prerequisites

### For Docker Deployment (Simplest & Most Reliable):
- **Docker Desktop** installed and running:
  - macOS: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (Supports both Apple Silicon M1/M2/M3/M4 & Intel)
  - Windows: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) (Enable WSL 2 Backend)

### For Native Deployment (Without Docker):
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14
- **FFmpeg**: Installed on your system path
  - On macOS: `brew install ffmpeg`
  - On Windows: `winget install Gyan.FFmpeg` or via [ffmpeg.org](https://ffmpeg.org/download.html)
- *(Optional)* **Ollama**: [Download from ollama.com](https://ollama.com/download)

---

## 2. Method A: Docker Installation (Recommended)

Docker provides an isolated, multi-platform environment where all audio libraries, FFmpeg binaries, and server dependencies are pre-configured.

### Step 1: Open Terminal / PowerShell
Navigate to the project folder:
```bash
cd super-ai_editor
```

### Step 2: Build and Start Container
```bash
docker compose up --build
```

### Step 3: Open the Web Studio
Open your browser and navigate to:
```
http://localhost:8000
```

> **Note for Windows 10/11 Users**: Make sure Docker Desktop is running and WSL 2 integration is enabled under `Settings > Resources > WSL Integration`.

---

## 3. Method B: Native macOS Installation

### Step 1: Verify System Dependencies
```bash
# Check Python and FFmpeg
python3 --version
ffmpeg -version
```
If FFmpeg is not installed, install it using Homebrew:
```bash
brew install ffmpeg
```

### Step 2: Launch super_ai_editor
Simply execute the launcher script:
```bash
./start.sh
```
The script will automatically:
1. Detect your Apple Silicon / Intel architecture.
2. Read your physical RAM (e.g. 8GB Unified Memory).
3. Check Ollama connectivity.
4. Launch the studio server at `http://localhost:8000`.
5. Open your default browser.

---

## 4. Method C: Native Windows 10 / 11 Installation

### Step 1: Verify Python & FFmpeg
Open PowerShell or Command Prompt:
```powershell
python --version
ffmpeg -version
```
If FFmpeg is not installed, run:
```powershell
winget install Gyan.FFmpeg
```

### Step 2: Launch via Batch Script
Double-click **`start.bat`** or run in Command Prompt:
```cmd
start.bat
```
Your browser will open automatically at `http://localhost:8000`.

---

## 5. Ollama Local AI Setup & RAM Optimization

`super_ai_editor` connects to a local Ollama instance to provide private, latency-free video editing intelligence.

### Step 1: Install Ollama
Download and install Ollama from [ollama.com](https://ollama.com/download).

### Step 2: Choose the Model for Your RAM

#### 🍏 For macOS with 8GB RAM:
We recommend **`llama3.2:1b`**:
- **Why?** It consumes only ~1.3 GB of unified memory, leaving over 6 GB free for video decoding, WebGL Three.js rendering, and audio processing.
- Run:
  ```bash
  ollama run llama3.2:1b
  ```

#### 🪟 For Windows with 16GB RAM:
We recommend **`llama3.2:3b`** or **`mistral:7b`**:
- **Why?** It provides exceptional contextual reasoning for complex multi-clip edits, transitions, and subtitle styling while easily fitting in 16 GB of host RAM or 6–8 GB VRAM.
- Run:
  ```cmd
  ollama run llama3.2:3b
  ```

### Step 3: Verifying Ollama Connection in the Editor
When `super_ai_editor` starts, check the top navigation bar:
- 🟢 **Green Dot (`Ollama: llama3.2:1b` or `llama3.2:3b`)**: Ollama is connected and ready.
- 🟡 **Yellow Dot (`Offline Rule Engine Active`)**: Ollama is not running. The editor continues to work smoothly using its built-in offline NLP rules!

---

## 6. Troubleshooting & FAQs

### Q1: The editor says "Ollama offline". Can I still edit videos?
**Yes!** The application is designed to be resilient. When Ollama is offline, a built-in offline AI rule engine parses instructions like *"add whoosh"*, *"generate subtitles"*, or *"add 3d title"* and executes them on the timeline without errors.

### Q2: What video formats can I export?
You can export:
- **MP4 (H.264 + AAC)**: Standard broadcast quality with embedded subtitles.
- **WebM (VP9 + Opus)**: Instant client-side recording without server round-trip.
- **.SRT**: SubRip subtitle track export.

### Q3: How do I test that everything is working properly?
Run the built-in test suite:
```bash
python3 verify_system.py
```
If all 8 tests output `✔ PASS`, your installation is complete and verified.
