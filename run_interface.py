#!/usr/bin/env python3
"""
Script para iniciar la interfaz web completa (API + Frontend).
Inicia el backend FastAPI y el frontend React/Vite en paralelo.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent
API_DIR = PROJECT_ROOT / "interface" / "api"
WEB_DIR = PROJECT_ROOT / "interface" / "web"
VENV_ACTIVATE = PROJECT_ROOT / ".venv" / "bin" / "activate"

# Procesos
processes = []


def signal_handler(sig, frame):
    """Maneja Ctrl+C para terminar ambos procesos."""
    print("\n\n🛑 Deteniendo servicios...")
    for proc in processes:
        if proc.poll() is None:  # Si aún está ejecutándose
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("✅ Servicios detenidos.")
    sys.exit(0)


def start_api():
    """Inicia el servidor FastAPI."""
    print("\n" + "="*70)
    print("🚀 Iniciando API (FastAPI)")
    print("="*70)
    
    # Comando para activar .venv e iniciar servidor
    cmd = [
        "bash",
        "-c",
        f"cd {API_DIR} && source {VENV_ACTIVATE} && python server.py"
    ]
    
    proc = subprocess.Popen(
        cmd,
        cwd=str(API_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    processes.append(proc)
    return proc


def start_web():
    """Inicia el servidor de desarrollo Vite."""
    # Esperar a que el API esté listo
    time.sleep(3)
    
    print("\n" + "="*70)
    print("🌐 Iniciando Frontend (Vite + React)")
    print("="*70)
    
    # Comando para instalar dependencias e iniciar dev server
    cmd = [
        "bash",
        "-c",
        f"cd {WEB_DIR} && npm run dev"
    ]
    
    proc = subprocess.Popen(
        cmd,
        cwd=str(WEB_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    processes.append(proc)
    return proc


def main():
    """Función principal."""
    print("\n" + "="*70)
    print("CHEF DIGITAL CBR - INTERFAZ WEB")
    print("="*70)
    
    # Verificar que existen los directorios
    if not API_DIR.exists():
        print(f"❌ ERROR: Carpeta API no encontrada: {API_DIR}")
        sys.exit(1)
    
    if not WEB_DIR.exists():
        print(f"❌ ERROR: Carpeta WEB no encontrada: {WEB_DIR}")
        sys.exit(1)
    
    if not VENV_ACTIVATE.exists():
        print(f"❌ ERROR: .venv no encontrado en {VENV_ACTIVATE}")
        print("Crea el entorno virtual:")
        print("  python -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar servicios
    api_proc = start_api()
    web_proc = start_web()
    
    print("\n" + "="*70)
    print("✅ SERVICIOS INICIADOS")
    print("="*70)
    print("📍 API:      http://localhost:8000")
    print("📍 Frontend: http://localhost:5173")
    print("\nPresiona Ctrl+C para detener...")
    print("="*70 + "\n")
    
    # Esperar a que los procesos terminen
    try:
        api_proc.wait()
    except KeyboardInterrupt:
        pass
    
    try:
        web_proc.wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
