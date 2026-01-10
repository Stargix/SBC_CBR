"""
Test del factor de confianza por número de ingredientes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from develop.core.similarity import SimilarityCalculator
from develop.core.models import CulturalTradition

def main():
    print("="*70)
    print("🎯 TEST: Factor de confianza por número de ingredientes")
    print("="*70)
    
    calc = SimilarityCalculator()
    
    # Test casos con diferente número de ingredientes
    casos = [
        {
            "nombre": "1 ingrediente italiano",
            "ingredientes": ["butter"],
            "esperado_sin_penalizacion": 1.0,
            "factor_confianza": 0.6,
            "esperado_final": 0.60
        },
        {
            "nombre": "2 ingredientes italianos",
            "ingredientes": ["butter", "arugula"],
            "esperado_sin_penalizacion": 1.0,
            "factor_confianza": 0.8,
            "esperado_final": 0.80
        },
        {
            "nombre": "3 ingredientes italianos",
            "ingredientes": ["butter", "arugula", "lemon"],
            "esperado_sin_penalizacion": 1.0,
            "factor_confianza": 0.9,
            "esperado_final": 0.90
        },
        {
            "nombre": "4 ingredientes italianos",
            "ingredientes": ["butter", "arugula", "lemon", "red pepper flakes"],
            "esperado_sin_penalizacion": 1.0,
            "factor_confianza": 1.0,
            "esperado_final": 1.0
        },
        {
            "nombre": "1 ingrediente universal",
            "ingredientes": ["sugar"],
            "esperado_sin_penalizacion": 0.7,
            "factor_confianza": 0.6,
            "esperado_final": 0.42
        },
        {
            "nombre": "2 ingredientes universales",
            "ingredientes": ["sugar", "raspberries"],
            "esperado_sin_penalizacion": 0.7,
            "factor_confianza": 0.8,
            "esperado_final": 0.56
        },
        {
            "nombre": "3 ingredientes universales",
            "ingredientes": ["sugar", "raspberries", "eggs"],
            "esperado_sin_penalizacion": 0.7,
            "factor_confianza": 0.9,
            "esperado_final": 0.63
        },
        {
            "nombre": "4 ingredientes universales",
            "ingredientes": ["sugar", "raspberries", "eggs", "all-purpose flour"],
            "esperado_sin_penalizacion": 0.7,
            "factor_confianza": 1.0,
            "esperado_final": 0.70
        },
        {
            "nombre": "Raspberry Bars (6 ingredientes)",
            "ingredientes": ["sugar", "sugar", "all-purpose flour", "butter", "eggs", "walnuts"],
            "esperado_sin_penalizacion": 0.75,
            "factor_confianza": 1.0,
            "esperado_final": 0.75
        }
    ]
    
    print("\n📊 RESULTADOS:")
    todos_correctos = True
    
    for caso in casos:
        score = calc.get_cultural_score(caso["ingredientes"], CulturalTradition.ITALIAN)
        esperado = caso["esperado_final"]
        
        print(f"\n📋 {caso['nombre']}")
        print(f"   Ingredientes ({len(caso['ingredientes'])}): {caso['ingredientes'][:3]}{'...' if len(caso['ingredientes']) > 3 else ''}")
        print(f"   Score base: {caso['esperado_sin_penalizacion']:.2f}")
        print(f"   Factor confianza: {caso['factor_confianza']:.2f}")
        print(f"   Score final esperado: {esperado:.2f}")
        print(f"   Score final obtenido: {score:.2f}")
        
        if abs(score - esperado) < 0.01:
            print(f"   ✅ CORRECTO")
        else:
            print(f"   ❌ ERROR: diferencia {abs(score - esperado):.2f}")
            todos_correctos = False
    
    print("\n" + "="*70)
    print("🎯 IMPACTO DE LA PENALIZACIÓN")
    print("="*70)
    
    print("\n❌ ANTES (sin penalización):")
    print("   Cherry Cream Pie (1 ing): 100% cultural")
    print("   → Daba impresión falsa de alta autenticidad")
    
    print("\n✅ AHORA (con penalización suavizada):")
    print("   Cherry Cream Pie (1 ing): 60% cultural")
    print("   → Refleja menor confiabilidad sin ser excesivo")
    
    print("\n📈 Escalado de confianza (suavizado):")
    print("   1 ingrediente: factor 0.6 (moderadamente poco confiable)")
    print("   2 ingredientes: factor 0.8 (poco confiable)")
    print("   3 ingredientes: factor 0.9 (casi confiable)")
    print("   4+ ingredientes: factor 1.0 (totalmente confiable)")
    
    print("\n" + "="*70)
    if todos_correctos:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")

if __name__ == "__main__":
    main()
