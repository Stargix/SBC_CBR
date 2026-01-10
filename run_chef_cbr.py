#!/usr/bin/env python
"""
Script wrapper para ejecutar Chef Digital CBR como módulo.

Uso: python run_chef_cbr.py
"""

import sys
from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import Request, EventType, Season


def get_event_type():
    """Solicita el tipo de evento al usuario."""
    print("\n📅 TIPO DE EVENTO:")
    events = {
        '1': EventType.WEDDING,
        '2': EventType.CHRISTENING,
        '3': EventType.COMMUNION,
        '4': EventType.CONGRESS,
        '5': EventType.FAMILIAR,
        '6': EventType.CORPORATE
    }
    print("  1. Boda (Wedding)")
    print("  2. Bautizo (Christening)")
    print("  3. Comunión (Communion)")
    print("  4. Congreso (Congress)")
    print("  5. Evento Familiar (Familiar)")
    print("  6. Evento Corporativo (Corporate)")
    
    while True:
        choice = input("\nSelecciona el tipo de evento (1-6): ").strip()
        if choice in events:
            return events[choice]
        print("❌ Opción inválida. Intenta de nuevo.")


def get_season():
    """Solicita la estación al usuario."""
    print("\n🌤️ ESTACIÓN DEL AÑO:")
    seasons = {
        '1': Season.SPRING,
        '2': Season.SUMMER,
        '3': Season.AUTUMN,
        '4': Season.WINTER
    }
    print("  1. Primavera (Spring)")
    print("  2. Verano (Summer)")
    print("  3. Otoño (Autumn)")
    print("  4. Invierno (Winter)")
    
    while True:
        choice = input("\nSelecciona la estación (1-4): ").strip()
        if choice in seasons:
            return seasons[choice]
        print("❌ Opción inválida. Intenta de nuevo.")


def get_culinary_style():
    """Solicita el estilo culinario preferido (opcional)."""
    print("\n🍴 ESTILO CULINARIO (opcional):")
    from develop.core.models import CulinaryStyle
    styles = {
        '1': CulinaryStyle.CLASSIC,
        '2': CulinaryStyle.MODERN,
        '3': CulinaryStyle.FUSION,
        '4': CulinaryStyle.REGIONAL,
        '5': CulinaryStyle.SIBARITA,
        '6': CulinaryStyle.GOURMET,
        '0': None
    }
    print("  0. Sin preferencia")
    print("  1. Clásico (Classic)")
    print("  2. Moderno (Modern)")
    print("  3. Fusión (Fusion)")
    print("  4. Regional (Regional)")
    print("  5. Sibarita (Sibarita)")
    print("  6. Gourmet (Gourmet)")
    
    while True:
        choice = input("\nSelecciona el estilo (0-6): ").strip()
        if choice in styles:
            return styles[choice]
        print("❌ Opción inválida. Intenta de nuevo.")


def get_cultural_preference():
    """Solicita la preferencia cultural (opcional)."""
    print("\n🌍 PREFERENCIA CULTURAL (opcional):")
    from develop.core.models import CulturalTradition
    cultures = {
        '1': CulturalTradition.AMERICAN,
        '2': CulturalTradition.CHINESE,
        '3': CulturalTradition.FRENCH,
        '4': CulturalTradition.INDIAN,
        '5': CulturalTradition.ITALIAN,
        '6': CulturalTradition.JAPANESE,
        '7': CulturalTradition.MEXICAN,
        '8': CulturalTradition.SPANISH,
        '9': CulturalTradition.KOREAN,
        '10': CulturalTradition.VIETNAMESE,
        '11': CulturalTradition.LEBANESE,
        '0': None
    }
    print("  0. Sin preferencia")
    print("  1. Americana (American)")
    print("  2. China (Chinese)")
    print("  3. Francesa (French)")
    print("  4. India (Indian)")
    print("  5. Italiana (Italian)")
    print("  6. Japonesa (Japanese)")
    print("  7. Mexicana (Mexican)")
    print("  8. Española (Spanish)")
    print("  9. Coreana (Korean)")
    print("  10. Vietnamita (Vietnamese)")
    print("  11. Libanesa (Lebanese)")

    
    while True:
        choice = input("\nSelecciona la cultura (0-11): ").strip()
        if choice in cultures:
            return cultures[choice]
        print("❌ Opción inválida. Intenta de nuevo.")


def get_dietary_restrictions():
    """Solicita restricciones dietéticas (opcional, múltiple)."""
    print("\n🥗 RESTRICCIONES DIETÉTICAS (opcional, separadas por comas):")
    print()
    print("  alcohol-free, celery-free, crustacean-free, dairy-free,")
    print("  egg-free, fish-free, gluten-free, keto-friendly, kosher,")
    print("  paleo, peanut-free, pescatarian, vegan, vegetarian, etc.")
    print("\n  Deja vacío si no hay restricciones")
    
    response = input("\nIngresa restricciones (separadas por comas): ").strip()
    if not response:
        return []
    
    # Limpiar y separar
    restrictions = [r.strip().lower() for r in response.split(',') if r.strip()]
    return restrictions


def get_restricted_ingredients():
    """Solicita ingredientes a evitar (opcional, múltiple)."""
    print("\n🚫 INGREDIENTES A EVITAR (opcional, separados por comas):")
    print("  Ejemplos: shrimp, peanuts, shellfish, mushrooms")
    print("  Deja vacío si no hay restricciones")
    
    response = input("\nIngresa ingredientes a evitar: ").strip()
    if not response:
        return []
    
    # Limpiar y separar
    ingredients = [i.strip().lower() for i in response.split(',') if i.strip()]
    return ingredients


def get_season():
    """Solicita la estación al usuario."""
    print("\n🌤️ ESTACIÓN DEL AÑO:")
    seasons = {
        '1': Season.SPRING,
        '2': Season.SUMMER,
        '3': Season.AUTUMN,
        '4': Season.WINTER
    }
    print("  1. Primavera (Spring)")
    print("  2. Verano (Summer)")
    print("  3. Otoño (Autumn)")
    print("  4. Invierno (Winter)")
    
    while True:
        choice = input("\nSelecciona la estación (1-4): ").strip()
        if choice in seasons:
            return seasons[choice]
        print("❌ Opción inválida. Intenta de nuevo.")


def get_positive_int(prompt, min_val=1):
    """Solicita un número entero positivo al usuario."""
    while True:
        try:
            value = int(input(prompt).strip())
            if value >= min_val:
                return value
            print(f"❌ El valor debe ser al menos {min_val}.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")


def get_positive_float(prompt, min_val=0.0):
    """Solicita un número decimal positivo al usuario."""
    while True:
        try:
            value = float(input(prompt).strip())
            if value >= min_val:
                return value
            print(f"❌ El valor debe ser al menos {min_val}.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")


def get_yes_no(prompt):
    """Solicita una respuesta Sí/No al usuario."""
    while True:
        response = input(prompt).strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("❌ Por favor responde 's' (sí) o 'n' (no).")


def main():
    """Función principal interactiva"""
    print("=" * 60)
    print("🍽️  CHEF DIGITAL CBR - Sistema de Recomendación de Menús")
    print("=" * 60)
    
    # Recopilar información del usuario
    event_type = get_event_type()
    num_guests = get_positive_int("\n👥 Número de invitados: ", min_val=1)
    
    print("\n💰 PRESUPUESTO POR PERSONA:")
    price_min = get_positive_float("  Precio mínimo (€): ", min_val=0.0)
    price_max = get_positive_float("  Precio máximo (€): ", min_val=price_min)
    
    if price_max < price_min:
        print(f"⚠️  Ajustando: precio máximo debe ser >= precio mínimo")
        price_max = price_min
    
    season = get_season()
    wants_wine = get_yes_no("\n🍷 ¿Desea incluir vino? (s/n): ")
    
    # Campos adicionales opcionales
    print("\n" + "=" * 60)
    print("PREFERENCIAS ADICIONALES (opcional)")
    print("=" * 60)
    
    preferred_style = get_culinary_style()
    cultural_preference = get_cultural_preference()
    dietary_restrictions = get_dietary_restrictions()
    restricted_ingredients = get_restricted_ingredients()
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE LA SOLICITUD:")
    print("=" * 60)
    print(f"  Evento: {event_type.value}")
    print(f"  Invitados: {num_guests}")
    print(f"  Presupuesto: €{price_min:.2f} - €{price_max:.2f} por persona")
    print(f"  Estación: {season.value}")
    print(f"  Con vino: {'Sí' if wants_wine else 'No'}")
    if preferred_style:
        print(f"  Estilo culinario: {preferred_style.value}")
    if cultural_preference:
        print(f"  Preferencia cultural: {cultural_preference.value}")
    if dietary_restrictions:
        print(f"  Restricciones dietéticas: {', '.join(dietary_restrictions)}")
    if restricted_ingredients:
        print(f"  Ingredientes a evitar: {', '.join(restricted_ingredients)}")
    print("=" * 60)
    
    proceed = get_yes_no("\n¿Proceder con esta solicitud? (s/n): ")
    if not proceed:
        print("\n❌ Solicitud cancelada.")
        return
    
    # Crear sistema CBR
    print("\n🚀 Inicializando Chef Digital CBR...")
    config = CBRConfig(enable_learning=True, verbose=True)
    cbr = ChefDigitalCBR(config)
    
    # Crear solicitud
    request = Request(
        event_type=event_type,
        num_guests=num_guests,
        price_min=price_min,
        price_max=price_max,
        season=season,
        wants_wine=wants_wine,
        preferred_style=preferred_style,
        cultural_preference=cultural_preference,
        required_diets=dietary_restrictions,
        restricted_ingredients=restricted_ingredients
    )
    
    # Procesar solicitud
    print("\n⚙️  Procesando solicitud...\n")
    result = cbr.process_request(request)
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print(" SOLICITUD PROCESADA EXITOSAMENTE")
    print("=" * 60)
    print(f"  Propuestas generadas: {len(result.proposed_menus)}")
    print(f"  Tiempo de procesamiento: {result.processing_time:.2f}s")
    print("=" * 60)
    print(f"\n{result.explanations}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
