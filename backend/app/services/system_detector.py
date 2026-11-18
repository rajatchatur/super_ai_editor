import platform
import os
import sys

def get_system_ram_gb() -> float:
    """Safely get total physical RAM in GB across macOS, Windows, and Linux without requiring external packages."""
    # 1. Try psutil if available
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        pass

    # 2. macOS fallback via sysctl
    if sys.platform == "darwin":
        try:
            import subprocess
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
            return round(int(out) / (1024 ** 3), 2)
        except Exception:
            pass

    # 3. Windows fallback via ctypes / wmic
    if sys.platform == "win32":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullTotalPhys / (1024 ** 3), 2)
        except Exception:
            pass

    # 4. Linux fallback via /proc/meminfo
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / (1024 ** 2), 2)
        except Exception:
            pass

    # Default heuristic
    return 8.0

def get_hardware_profile():
    """Detect operating system, architecture, and recommend the best Ollama model."""
    os_name = sys.platform
    os_display = "macOS" if os_name == "darwin" else ("Windows" if os_name == "win32" else "Linux")
    arch = platform.machine()
    total_ram = get_system_ram_gb()

    # Determine recommended profile
    if os_name == "darwin":
        if total_ram <= 10.0:
            recommended_model = "llama3.2:1b"
            profile_name = "macOS 8GB Optimized (Ultra-Fast & Responsive)"
            notes = "Optimized for Apple Silicon 8GB Unified Memory. Zero swap memory pressure, instantaneous response."
            candidate_models = ["llama3.2:1b", "qwen2.5:1.5b", "phi3:mini"]
        else:
            recommended_model = "llama3.2:3b"
            profile_name = "macOS 16GB+ Studio Profile"
            notes = "Full Apple Silicon Metal acceleration with high contextual reasoning."
            candidate_models = ["llama3.2:3b", "qwen2.5:7b", "mistral:7b"]
    elif os_name == "win32":
        if total_ram <= 10.0:
            recommended_model = "llama3.2:1b"
            profile_name = "Windows 8GB Economy Profile"
            notes = "Lightweight memory footprint to avoid pagefile thrashing."
            candidate_models = ["llama3.2:1b", "qwen2.5:1.5b"]
        elif total_ram <= 20.0:
            recommended_model = "llama3.2:3b"
            profile_name = "Windows 16GB High-Performance Profile"
            notes = "Sweet spot for 16GB Windows PCs. Superb video script reasoning and timeline action synthesis."
            candidate_models = ["llama3.2:3b", "mistral:7b", "qwen2.5:7b"]
        else:
            recommended_model = "llama3.1:8b"
            profile_name = "Windows 32GB+ Pro Workstation Profile"
            notes = "Maximum reasoning fidelity, deep video analysis."
            candidate_models = ["llama3.1:8b", "mistral:7b", "qwen2.5:14b"]
    else:  # Linux / Docker container default
        if total_ram <= 10.0:
            recommended_model = "llama3.2:1b"
            profile_name = "Linux/Container 8GB Profile"
            notes = "Lightweight memory configuration."
            candidate_models = ["llama3.2:1b", "phi3:mini"]
        else:
            recommended_model = "llama3.2:3b"
            profile_name = "Linux/Container 16GB Profile"
            notes = "Balanced performance and high accuracy."
            candidate_models = ["llama3.2:3b", "mistral:7b"]

    return {
        "os": os_display,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "arch": arch,
        "total_ram_gb": total_ram,
        "profile_name": profile_name,
        "recommended_model": recommended_model,
        "candidate_models": candidate_models,
        "notes": notes,
        "docker_compatible": True
    }
