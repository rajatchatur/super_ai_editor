#!/usr/bin/env bash
# ========================================================
# super_ai_editor - One-Click Launcher (macOS & Linux)
# ========================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "🎬  Starting super_ai_editor — AI-Powered Pro Video Studio"
echo "=========================================================="

# Check if Docker mode requested
if [ "$1" == "--docker" ]; then
    echo "🐳 Launching via Docker Compose..."
    docker compose up --build
    exit 0
fi

# Detect Hardware & Recommend Ollama Model
echo "🔍 Checking System & Memory Profile..."
python3 -c "
import sys; sys.path.insert(0, '$DIR')
from backend.app.services.system_detector import get_hardware_profile
hw = get_hardware_profile()
print(f'   • Detected OS: {hw[\"os\"]} ({hw[\"arch\"]})')
print(f'   • System RAM: {hw[\"total_ram_gb\"]} GB')
print(f'   • Recommended Ollama Model: {hw[\"recommended_model\"]} ({hw[\"profile_name\"]})')
"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🤖 Ollama is ONLINE at http://localhost:11434"
else
    echo "ℹ️  Ollama is not running. (Offline AI Rule Engine is ACTIVE)"
    echo "   Tip: To enable live LLM Copilot, run in another terminal:"
    echo "        ollama run llama3.2:1b  (for 8GB Mac)"
    echo "        ollama run llama3.2:3b  (for 16GB Windows)"
fi

echo ""
echo "🚀 Launching Studio Server at http://localhost:8000 ..."
echo "   Press Ctrl+C to stop."
echo "=========================================================="

# Open browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 1 && open "http://localhost:8000") &
fi

python3 backend/run.py
