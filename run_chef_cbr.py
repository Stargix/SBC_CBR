#!/usr/bin/env python
"""
Script wrapper para ejecutar Chef Digital CBR como módulo.

Uso: python run_chef_cbr.py
"""

import sys
from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season

def main():
    """Función principal de ejemplo"""
    # Crear sistema CBR
    config = CBRConfig(enable_learning=True, verbose=True)
    cbr = ChefDigitalCBR(config)
    
    # Crear una solicitud de ejemplo
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=45.0,
        price_max=55.0,
        season=Season.SUMMER,
        wants_wine=True
    )
    
    # Procesar solicitud
    print("Procesando solicitud...")
    result = cbr.process_request(request)
    
    # Mostrar resultados
    print(f"\n✅ Solicitud procesada exitosamente")
    print(f"   Propuestas: {len(result.proposed_menus)}")
    print(f"   Tiempo: {result.processing_time:.2f}s")
    print(f"\n{result.explanations}")

if __name__ == "__main__":
    main()
