"""
Demo de aprendizaje adaptativo dual: Casos + Platos

Este demo muestra cómo usar simultáneamente:
1. AdaptiveWeightLearner - Para similitud de casos completos
2. AdaptiveDishWeightLearner - Para similitud de platos individuales

El sistema aprende de forma coordinada:
- Los pesos de casos mejoran la recuperación inicial
- Los pesos de platos mejoran la adaptación cuando se reemplazan platos
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from develop.core.adaptive_weights import AdaptiveWeightLearner, AdaptiveDishWeightLearner
from develop.core.similarity import SimilarityWeights, DishSimilarityWeights, calculate_dish_similarity
from develop.core.models import (
    Feedback, Request, EventType, Season, CulturalTradition,
    Dish, DishType, DishCategory, Complexity, Flavor, Temperature
)


def print_section(title: str):
    """Imprime una sección con formato"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_weights(weights_dict: dict, title: str):
    """Imprime pesos de forma ordenada"""
    print(f"\n{title}:")
    for name, value in sorted(weights_dict.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(value * 50)
        print(f"  {name:20s}: {value:.3f}  {bar}")


def demo_case_weight_learning():
    """Demo del aprendizaje de pesos de casos"""
    print_section("DEMO 1: Aprendizaje de Pesos de Casos")
    
    # Inicializar learner
    case_learner = AdaptiveWeightLearner(learning_rate=0.08)
    
    print("\n📊 Pesos iniciales de similitud de casos:")
    initial_weights = case_learner._weights_to_dict()
    print_weights(initial_weights, "Pesos Iniciales")
    
    # Simulación 1: Cliente insatisfecho con precio
    print("\n\n--- Escenario 1: Cliente insatisfecho con precio ---")
    print("Cliente quería presupuesto bajo, pero recibió menú caro")
    
    feedback1 = Feedback(
        overall_satisfaction=2,
        price_satisfaction=1,  # Muy insatisfecho con precio
        flavor_satisfaction=4,
        dietary_satisfaction=5,
        cultural_satisfaction=4,
        comments="Muy caro, excedió el presupuesto"
    )
    
    request1 = Request(
        event_type=EventType.FAMILIAR,
        season=Season.SUMMER,
        num_guests=20,
        price_min=20.0,
        price_max=30.0,
        required_diets=[]
    )
    
    adjustments1 = case_learner.update_from_feedback(feedback1, request1)
    print(f"\n✏️ Ajustes realizados: {adjustments1}")
    
    # Simulación 2: Cliente insatisfecho con cultura
    print("\n\n--- Escenario 2: Cliente insatisfecho con cultura ---")
    print("Cliente quería menú español pero recibió asiático")
    
    feedback2 = Feedback(
        overall_satisfaction=2,
        price_satisfaction=4,
        flavor_satisfaction=3,
        dietary_satisfaction=4,
        cultural_satisfaction=1,  # Muy insatisfecho con cultura
        comments="No respetó mis preferencias culturales"
    )
    
    request2 = Request(
        event_type=EventType.WEDDING,
        season=Season.AUTUMN,
        num_guests=80,
        price_min=50.0,
        price_max=60.0,
        required_diets=[],
        cultural_preference=CulturalTradition.SPANISH
    )
    
    adjustments2 = case_learner.update_from_feedback(feedback2, request2)
    print(f"\n✏️ Ajustes realizados: {adjustments2}")
    
    # Simulación 3: Cliente muy satisfecho
    print("\n\n--- Escenario 3: Cliente muy satisfecho ---")
    print("Todo perfecto, especialmente precio y cultura")
    
    feedback3 = Feedback(
        overall_satisfaction=5,
        price_satisfaction=5,
        flavor_satisfaction=5,
        dietary_satisfaction=5,
        cultural_satisfaction=5,
        comments="¡Perfecto! Exactamente lo que queríamos"
    )
    
    request3 = Request(
        event_type=EventType.CORPORATE,
        season=Season.WINTER,
        num_guests=50,
        price_min=40.0,
        price_max=45.0,
        required_diets=[],
        cultural_preference=CulturalTradition.FRENCH
    )
    
    adjustments3 = case_learner.update_from_feedback(feedback3, request3)
    print(f"\n✏️ Ajustes realizados: {adjustments3}")
    
    # Mostrar pesos finales
    print("\n\n📊 Evolución de pesos:")
    final_weights = case_learner._weights_to_dict()
    print_weights(final_weights, "Pesos Finales")
    
    print("\n📈 Cambios más significativos:")
    for weight_name, initial_value in initial_weights.items():
        final_value = final_weights[weight_name]
        change = final_value - initial_value
        change_pct = (change / initial_value * 100) if initial_value > 0 else 0
        if abs(change_pct) > 5:
            arrow = "↑" if change > 0 else "↓"
            print(f"  {arrow} {weight_name:20s}: {change:+.3f} ({change_pct:+.1f}%)")
    
    # Guardar historial
    case_learner.save_learning_history("data/case_learning_demo.json")
    print("\n💾 Historial guardado en: data/case_learning_demo.json")
    
    return case_learner


def demo_dish_weight_learning():
    """Demo del aprendizaje de pesos de platos"""
    print_section("DEMO 2: Aprendizaje de Pesos de Platos")
    
    # Inicializar learner
    dish_learner = AdaptiveDishWeightLearner(learning_rate=0.08)
    
    print("\n📊 Pesos iniciales de similitud de platos:")
    initial_weights = dish_learner._weights_to_dict()
    print_weights(initial_weights, "Pesos Iniciales")
    
    # Crear platos de ejemplo
    original_pasta = Dish(
        id="pasta1",
        name="Pasta Carbonara",
        dish_type=DishType.MAIN_COURSE,
        category=DishCategory.PASTA,
        ingredients=["pasta", "egg", "bacon", "parmesan", "black_pepper"],
        price=18.0,
        complexity=Complexity.MEDIUM,
        flavors=[Flavor.SALTY, Flavor.UMAMI],
        styles=[],
        temperature=Temperature.HOT,
        seasons=[Season.ALL],
        diets=[]
    )
    
    # Reemplazo 1: Misma categoría, similar (EXITOSO)
    replacement_pasta_1 = Dish(
        id="pasta2",
        name="Pasta Amatriciana",
        dish_type=DishType.MAIN_COURSE,
        category=DishCategory.PASTA,
        ingredients=["pasta", "tomato", "bacon", "pecorino", "onion"],
        price=19.0,
        complexity=Complexity.MEDIUM,
        flavors=[Flavor.SALTY, Flavor.UMAMI],
        styles=[],
        temperature=Temperature.HOT,
        seasons=[Season.ALL],
        diets=[]
    )
    
    print("\n\n--- Escenario 1: Adaptación exitosa (pasta similar) ---")
    print(f"Original: {original_pasta.name}")
    print(f"Reemplazo: {replacement_pasta_1.name}")
    
    dish_learner.update_from_feedback(
        original_dish=original_pasta,
        replacement_dish=replacement_pasta_1,
        feedback_score=4.5,
        adaptation_reason="general"
    )
    print("✅ Feedback positivo - Cliente satisfecho con el reemplazo")
    
    # Reemplazo 2: Categoría diferente (FALLIDO)
    replacement_rice = Dish(
        id="rice1",
        name="Risotto ai Funghi",
        dish_type=DishType.MAIN_COURSE,
        category=DishCategory.RICE,  # ¡Diferente categoría!
        ingredients=["rice", "mushroom", "parmesan", "white_wine", "onion"],
        price=22.0,
        complexity=Complexity.HIGH,
        flavors=[Flavor.UMAMI],
        styles=[],
        temperature=Temperature.HOT,
        seasons=[Season.ALL],
        diets=[]
    )
    
    print("\n\n--- Escenario 2: Adaptación problemática (cambió categoría) ---")
    print(f"Original: {original_pasta.name} (PASTA)")
    print(f"Reemplazo: {replacement_rice.name} (RICE)")
    
    dish_learner.update_from_feedback(
        original_dish=original_pasta,
        replacement_dish=replacement_rice,
        feedback_score=2.0,
        adaptation_reason="general"
    )
    print("❌ Feedback negativo - Cliente esperaba pasta, no arroz")
    
    # Reemplazo 3: Adaptación dietética exitosa
    replacement_vegan = Dish(
        id="pasta3",
        name="Pasta Aglio e Olio (Vegan)",
        dish_type=DishType.MAIN_COURSE,
        category=DishCategory.PASTA,
        ingredients=["pasta", "garlic", "olive_oil", "chili", "parsley"],
        price=16.0,
        complexity=Complexity.LOW,
        flavors=[Flavor.SALTY, Flavor.SPICY],
        styles=[],
        temperature=Temperature.HOT,
        seasons=[Season.ALL],
        diets=["vegan"]
    )
    
    print("\n\n--- Escenario 3: Adaptación dietética exitosa ---")
    print(f"Original: {original_pasta.name} (con huevo y bacon)")
    print(f"Reemplazo: {replacement_vegan.name} (VEGAN)")
    
    dish_learner.update_from_feedback(
        original_dish=original_pasta,
        replacement_dish=replacement_vegan,
        feedback_score=4.2,
        adaptation_reason="dietary"
    )
    print("✅ Adaptación dietética bien recibida")
    
    # Mostrar pesos finales
    print("\n\n📊 Evolución de pesos:")
    final_weights = dish_learner._weights_to_dict()
    print_weights(final_weights, "Pesos Finales")
    
    print("\n📈 Cambios más significativos:")
    for weight_name, initial_value in initial_weights.items():
        final_value = final_weights[weight_name]
        change = final_value - initial_value
        change_pct = (change / initial_value * 100) if initial_value > 0 else 0
        if abs(change_pct) > 5:
            arrow = "↑" if change > 0 else "↓"
            print(f"  {arrow} {weight_name:20s}: {change:+.3f} ({change_pct:+.1f}%)")
    
    # Guardar historial
    dish_learner.save_learning_history("data/dish_learning_demo.json")
    print("\n💾 Historial guardado en: data/dish_learning_demo.json")
    
    return dish_learner


def demo_integrated_learning():
    """Demo de aprendizaje integrado (casos + platos)"""
    print_section("DEMO 3: Aprendizaje Integrado (Casos + Platos)")
    
    print("\n🎯 Sistema con aprendizaje dual:")
    print("  1. Aprende qué CASOS recuperar (similitud a nivel de menú/evento)")
    print("  2. Aprende qué PLATOS usar al adaptar (similitud a nivel de plato)")
    
    case_learner = AdaptiveWeightLearner(learning_rate=0.06)
    dish_learner = AdaptiveDishWeightLearner(learning_rate=0.06)
    
    print("\n✅ Ambos learners inicializados")
    print(f"  - Case learner: {case_learner.iteration} iteraciones")
    print(f"  - Dish learner: {dish_learner.iteration} iteraciones")
    
    print("\n💡 Uso típico en el ciclo CBR:")
    print("  RETRIEVE: Usa case_learner.get_current_weights()")
    print("  ADAPT: Usa dish_learner.get_current_weights() al buscar reemplazos")
    print("  RETAIN: Actualiza AMBOS learners con el feedback")
    
    # Ejemplo de cómo usar ambos pesos
    print("\n\n--- Ejemplo de uso coordinado ---")
    
    # Obtener pesos actuales
    case_weights = case_learner.get_current_weights()
    dish_weights = dish_learner.get_current_weights()
    
    print(f"\n1️⃣ RETRIEVE: Buscar casos similares")
    print(f"   Usando pesos aprendidos para casos:")
    print(f"   - event_type: {case_weights.event_type:.3f}")
    print(f"   - price_range: {case_weights.price_range:.3f}")
    print(f"   - cultural: {case_weights.cultural:.3f}")
    
    print(f"\n2️⃣ ADAPT: Si necesitamos reemplazar un plato...")
    print(f"   Usando pesos aprendidos para platos:")
    print(f"   - category: {dish_weights.category:.3f}")
    print(f"   - flavors: {dish_weights.flavors:.3f}")
    print(f"   - diets: {dish_weights.diets:.3f}")
    
    # Crear platos de ejemplo
    dish1 = Dish(
        id="dish1",
        name="Gazpacho",
        dish_type=DishType.STARTER,
        category=DishCategory.SOUP,
        ingredients=["tomato", "cucumber", "pepper", "onion", "garlic", "olive_oil"],
        price=8.0,
        complexity=Complexity.LOW,
        flavors=[Flavor.SOUR],
        styles=[],
        temperature=Temperature.COLD,
        seasons=[Season.SUMMER],
        diets=["vegan"]
    )
    
    dish2 = Dish(
        id="dish2",
        name="Salmorejo",
        dish_type=DishType.STARTER,
        category=DishCategory.CREAM,
        ingredients=["tomato", "bread", "olive_oil", "garlic", "ham", "egg"],
        price=9.0,
        complexity=Complexity.LOW,
        flavors=[Flavor.SOUR],
        styles=[],
        temperature=Temperature.COLD,
        seasons=[Season.SUMMER],
        diets=[]
    )
    
    print(f"\n3️⃣ Ejemplo: Calcular similitud entre platos")
    similarity = calculate_dish_similarity(dish1, dish2, weights=dish_weights)
    print(f"   Similitud {dish1.name} ↔ {dish2.name}: {similarity:.3f}")
    print(f"   (Usa los pesos aprendidos de platos)")
    
    print("\n\n4️⃣ RETAIN: Tras recibir feedback...")
    print("   → Actualizar case_learner.update_from_feedback()")
    print("   → Actualizar dish_learner.update_from_feedback() por cada adaptación")
    
    print("\n\n📊 Ventajas del sistema dual:")
    print("  ✓ Aprendizaje especializado para cada fase del CBR")
    print("  ✓ Mayor precisión en retrieve Y en adapt")
    print("  ✓ Aprende de forma independiente pero complementaria")
    print("  ✓ Historiales separados para análisis detallado")
    
    return case_learner, dish_learner


def main():
    """Función principal del demo"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  DEMO: APRENDIZAJE ADAPTATIVO DUAL (Casos + Platos)".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    try:
        # Demo 1: Aprendizaje de pesos de casos
        case_learner = demo_case_weight_learning()
        
        input("\n\n[Presiona ENTER para continuar al Demo 2...]")
        
        # Demo 2: Aprendizaje de pesos de platos
        dish_learner = demo_dish_weight_learning()
        
        input("\n\n[Presiona ENTER para continuar al Demo 3...]")
        
        # Demo 3: Integración
        demo_integrated_learning()
        
        print_section("RESUMEN FINAL")
        
        print("\n✅ Implementación completada:")
        print("  1. ✓ DishSimilarityWeights - Pesos configurables para platos")
        print("  2. ✓ calculate_dish_similarity() - Acepta pesos personalizados")
        print("  3. ✓ AdaptiveDishWeightLearner - Aprende de adaptaciones")
        print("  4. ✓ Integración con AdaptiveWeightLearner existente")
        
        print("\n📚 Archivos creados/modificados:")
        print("  - develop/core/similarity.py (DishSimilarityWeights)")
        print("  - develop/core/adaptive_weights.py (AdaptiveDishWeightLearner)")
        print("  - data/case_learning_demo.json (historial de casos)")
        print("  - data/dish_learning_demo.json (historial de platos)")
        
        print("\n🎓 Próximos pasos:")
        print("  1. Integrar los learners en el ciclo CBR completo")
        print("  2. Usar case_learner en retrieve.py")
        print("  3. Usar dish_learner en adapt.py/ingredient_adapter.py")
        print("  4. Actualizar ambos en retain.py con feedback real")
        
        print("\n" + "█"*70)
        print("Demo completado exitosamente! 🎉")
        print("█"*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
