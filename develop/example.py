#!/usr/bin/env python3
"""
Ejemplo de uso del sistema CBR desde CBR/develop.
"""

import sys
from pathlib import Path

# Añadir el directorio padre al path para importar develop como módulo
sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle
)


def main():
    """Demo rápida del sistema."""
    print("=" * 60)
    print("🍽️  SISTEMA DE CATERING CBR - DEVELOP")
    print("=" * 60)
    
    # Configurar sistema
    config = CBRConfig(verbose=False, max_proposals=3)
    cbr = ChefDigitalCBR(config)
    
    # Crear solicitud de boda
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_max=80.0,
        season=Season.SPRING,
        preferred_style=CulinaryStyle.GOURMET,
        wants_wine=True
    )
    
    print(f"\n📋 Solicitud:")
    print(f"   Evento: Boda")
    print(f"   Comensales: {request.num_guests}")
    print(f"   Presupuesto: {request.price_max}€/persona")
    print(f"   Temporada: Primavera")
    print(f"   Estilo: Gourmet\n")
    
    # Procesar
    result = cbr.process_request(request)
    print(result.explanations)
    
    # Estadísticas
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("=" * 60)
    stats = cbr.get_statistics()
    print(f"\n📚 Base de Casos:")
    print(f"   Total casos: {stats['case_base']['total_cases']}")
    
    # Obtener stats de la case_base directamente
    cb_stats = cbr.case_base.get_statistics()
    print(f"   Platos disponibles: {cb_stats['total_dishes']}")
    print(f"   Bebidas disponibles: {cb_stats['total_beverages']}")
    if cb_stats['total_cases'] > 0:
        print(f"   Casos exitosos: {cb_stats['successful_cases']}")
        print(f"   Feedback promedio: {cb_stats['average_feedback']:.1f}/5")
    print()


if __name__ == "__main__":
    main()
