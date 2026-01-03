#!/usr/bin/env python
"""
Script para ejecutar las demos del sistema CBR de Chef Digital.

Uso: python run_demos.py [nombre_demo]
     python run_demos.py  # Lista todas las demos disponibles
"""

import sys
import subprocess
from pathlib import Path

DEMOS = {
    "simulacion": "Simulación de usuarios sintéticos con aprendizaje",
    "retain": "Demostración del ciclo completo CBR con RETAIN",
    "menu_completo": "Adaptación completa de menú",
    "recalculo_similitud": "Recalcío de similitud después de ADAPT",
    "filtrado_critico": "Filtrado de restricciones críticas en RETRIEVE",
    "adaptacion_dietetica": "Adaptación de ingredientes dietéticos",
    "negative_cases": "Manejo de casos negativos"
}

def run_demo(demo_name: str):
    """Ejecuta una demo específica"""
    if demo_name not in DEMOS:
        print(f"❌ Demo '{demo_name}' no encontrada")
        print("\nDemos disponibles:")
        list_demos()
        sys.exit(1)
    
    print(f"\n▶️  Ejecutando: {DEMOS[demo_name]}\n")
    
    try:
        cmd = [sys.executable, "-m", f"demos.demo_{demo_name}"]
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Error ejecutando demo: {e}")
        sys.exit(1)

def list_demos():
    """Lista todas las demos disponibles"""
    print("\n" + "="*70)
    print("📺 DEMOS DISPONIBLES - Chef Digital CBR")
    print("="*70 + "\n")
    
    for i, (name, desc) in enumerate(DEMOS.items(), 1):
        print(f"{i}. {name}")
        print(f"   → {desc}\n")
    
    print("="*70)
    print(f"\nUso: python run_demos.py <nombre>")
    print("Ejemplo: python run_demos.py simulacion\n")

    inp = input("Selecciona una demo para ejecutar (número o nombre), o presiona Enter para salir: ").strip()

    return inp

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        inp = list_demos()
        if not inp:
            return
        if inp.isdigit():
            demo_name = list(DEMOS.keys())[int(inp) - 1]
        else:
            demo_name = inp
        run_demo(demo_name)
        return
    
    demo_name = sys.argv[1]
    run_demo(demo_name)

if __name__ == "__main__":

    main()
