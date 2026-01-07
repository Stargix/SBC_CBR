"""
Test de debugging: ¿Por qué con restricción vegan no se recuperan menús válidos?
"""
from develop.main import ChefDigitalCBR
from develop.core.models import Request

# Crear CBR
cbr = ChefDigitalCBR()

# Request con vegan
request = Request(
    num_guests=4,
    required_diets=['vegan'],
    price_min=10.0,
    price_max=20.0
)

print("=" * 80)
print("DEBUG: ¿Por qué con vegan no hay menús válidos?")
print("=" * 80)
print(f"\nRequest: vegan, budget {request.price_min}-{request.price_max}€\n")

# Ejecutar proceso
result = cbr.process_request(request)

print(f"Resultado:")
print(f"  - Menús propuestos: {len(result.proposed_menus)}")
print(f"  - Menús rechazados: {len(result.rejected_cases)}")
print()

# Analizar casos rechazados
if result.rejected_cases:
    print("ANÁLISIS DE CASOS RECHAZADOS:")
    print("-" * 80)
    for i, reject in enumerate(result.rejected_cases[:5], 1):
        print(f"\n{i}. {reject['menu_name']}")
        print(f"   Similitud: {reject.get('similarity', 0):.1%}")
        
        reasons = reject.get('reasons', [])
        if reasons:
            for reason in reasons:
                if hasattr(reason, 'message'):
                    print(f"   - {reason.message}")
                else:
                    print(f"   - {reason}")

print("\n" + "=" * 80)
print("DIAGNÓSTICO DEL PROBLEMA")
print("=" * 80)
print("""
El sistema tiene 3 fases:

1. RETRIEVE: Recupera casos similares de la base de datos
   - Pregunta: ¿Filtra por dietas o solo por similitud?
   
2. ADAPT: Adapta los casos recuperados
   - _adapt_for_diets() intenta sustituir ingredientes que violan dietas
   - Si falla, retorna None (descarta el caso)
   - Pregunta: ¿Está funcionando la sustitución?
   
3. REVISE: Valida menús adaptados
   - Verifica que cumplan restricciones
   - Pregunta: ¿Llegan menús a esta fase?

POSIBLES PROBLEMAS:
A) RETRIEVE recupera casos sin ingredientes veganos → ADAPT falla al sustituir
B) ADAPT no encuentra sustituciones en el mismo grupo de ingredientes
C) Los platos no veganos tienen muchos ingredientes problemáticos
""")

print("\nVAMOS A INVESTIGAR RETRIEVE...")
print("-" * 80)

# Forzar RETRIEVE para ver qué recupera
retrieval_results = cbr._retrieve_phase_detailed(request)
print(f"\nRetrieve encontró: {len(retrieval_results)} casos")

if retrieval_results:
    print("\nPrimeros 3 casos recuperados:")
    for i, result in enumerate(retrieval_results[:3], 1):
        case = result.case
        menu = case.menu
        print(f"\n{i}. Caso {case.id} (Similitud: {result.similarity:.1%})")
        print(f"   Starter: {menu.starter.name}")
        print(f"     Diets: {menu.starter.diets}")
        print(f"     Ingredients: {menu.starter.ingredients[:5]}...")
        print(f"   Main: {menu.main_course.name}")
        print(f"     Diets: {menu.main_course.diets}")
        print(f"     Ingredients: {menu.main_course.ingredients[:5]}...")

print("\n" + "=" * 80)
print("AHORA VEAMOS QUÉ PASA EN ADAPT...")
print("=" * 80)

# Intentar adaptar el primer caso
if retrieval_results:
    first_case = retrieval_results[0].case
    print(f"\nIntentando adaptar caso: {first_case.id}")
    
    # Llamar directamente a _adapt_case para ver el resultado
    adaptation = cbr.adapter._adapt_case(
        first_case, 
        request, 
        original_similarity=retrieval_results[0].similarity
    )
    
    if adaptation is None:
        print("❌ ADAPT retornó None - El caso NO se pudo adaptar")
        print("\nEsto significa que _adapt_for_diets() falló.")
        print("Razón probable:")
        print("  - No se encontraron sustituciones para ingredientes no-veganos")
        print("  - Las sustituciones deben ser del MISMO GRUPO de ingredientes")
        print("  - Si no hay alternativa vegan en el grupo, el plato se descarta")
    else:
        print("✓ ADAPT tuvo éxito")
        print(f"  Adaptaciones: {len(adaptation.adaptations_made)}")
        for adapt in adaptation.adaptations_made[:5]:
            print(f"    - {adapt}")
        print(f"  Similitud final: {adaptation.final_similarity:.1%}")
