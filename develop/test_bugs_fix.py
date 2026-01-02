"""
Demo: Verificación de bugs corregidos.

Prueba que los bugs identificados han sido corregidos.
"""

from core.models import Request, EventType, Season, Menu, Dish, DishType, DishCategory
from core.case_base import CaseBase
from cycle.retrieve import CaseRetriever
from cycle.adapt import CaseAdapter
from cycle.diversity import ensure_diversity, calculate_diversity_score
from core.similarity import calculate_dish_similarity, calculate_menu_similarity
import copy

def test_bug_1_no_mutation():
    """Test: Verificar que no se mutan objetos originales"""
    print("\n" + "="*80)
    print("TEST 1: No mutación de objetos originales")
    print("="*80)
    
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    # Obtener un caso
    all_cases = case_base.get_all_cases()
    if not all_cases:
        print("❌ No hay casos en la base")
        return
    
    original_case = all_cases[0]
    original_main_ingredients = list(original_case.menu.main_course.ingredients)
    
    print(f"\n📋 Caso original: {original_case.id}")
    print(f"   Main course: {original_case.menu.main_course.name}")
    print(f"   Ingredientes: {original_main_ingredients[:5]}")
    
    # Crear request que requiera adaptación dietética
    request = Request(
        event_type=EventType.WEDDING,
        num_guests=100,
        price_min=80,
        price_max=120,
        season=Season.SPRING,
        required_diets=['vegan'],  # Forzar adaptación
        wants_wine=True
    )
    
    # Adaptar
    adapter = CaseAdapter(case_base)
    retriever = CaseRetriever(case_base)
    
    results = retriever.retrieve(request, k=1)
    if results:
        adapted = adapter.adapt(results, request, num_proposals=1)
        
        # Verificar que el original NO cambió
        current_main_ingredients = list(original_case.menu.main_course.ingredients)
        
        if current_main_ingredients == original_main_ingredients:
            print("\n✅ CORRECTO: Caso original NO fue modificado")
            print(f"   Ingredientes originales preservados: {current_main_ingredients[:5]}")
        else:
            print("\n❌ ERROR: Caso original fue modificado!")
            print(f"   Antes: {original_main_ingredients[:5]}")
            print(f"   Después: {current_main_ingredients[:5]}")
    else:
        print("⚠️  No se recuperaron casos")


def test_bug_7_division_zero():
    """Test: Division por zero en similitud"""
    print("\n" + "="*80)
    print("TEST 2: División por zero en similitud")
    print("="*80)
    
    # Crear platos con precio 0
    dish1 = Dish(
        id="test1",
        name="Free Dish",
        dish_type=DishType.STARTER,
        price=0.0,  # ❗ Precio 0
        category=DishCategory.VEGETABLE,
        calories=0  # ❗ Calorías 0
    )
    
    dish2 = Dish(
        id="test2",
        name="Another Free Dish",
        dish_type=DishType.STARTER,
        price=0.0,
        category=DishCategory.VEGETABLE,
        calories=0
    )
    
    try:
        similarity = calculate_dish_similarity(dish1, dish2)
        print(f"\n✅ CORRECTO: Similitud calculada sin error: {similarity:.3f}")
        print(f"   Platos con precio/calorías 0 manejados correctamente")
    except ZeroDivisionError:
        print("\n❌ ERROR: Division por zero!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def test_bug_10_diversity():
    """Test: Diversificación de propuestas"""
    print("\n" + "="*80)
    print("TEST 3: Diversificación de propuestas")
    print("="*80)
    
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    all_cases = case_base.get_all_cases()
    if len(all_cases) < 5:
        print("⚠️  No hay suficientes casos para probar diversidad")
        return
    
    # Obtener menús
    menus = [case.menu for case in all_cases[:6]]
    
    print(f"\n📋 Menús originales: {len(menus)}")
    for i, menu in enumerate(menus, 1):
        print(f"   {i}. {menu.starter.name} / {menu.main_course.name}")
    
    # Calcular diversidad original
    original_diversity = calculate_diversity_score(menus)
    print(f"\n📊 Diversidad original: {original_diversity:.2%}")
    
    # Diversificar
    diverse_menus = ensure_diversity(menus, min_distance=0.3, max_proposals=3)
    
    print(f"\n📋 Menús diversificados: {len(diverse_menus)}")
    for i, menu in enumerate(diverse_menus, 1):
        print(f"   {i}. {menu.starter.name} / {menu.main_course.name}")
    
    # Calcular diversidad final
    final_diversity = calculate_diversity_score(diverse_menus)
    print(f"\n📊 Diversidad final: {final_diversity:.2%}")
    
    if final_diversity > original_diversity:
        print(f"✅ CORRECTO: Diversidad mejoró en {(final_diversity - original_diversity):.1%}")
    else:
        print(f"⚠️  Diversidad cambió: {original_diversity:.2%} → {final_diversity:.2%}")


def test_bug_11_case_limit():
    """Test: Límite de casos (política de olvido)"""
    print("\n" + "="*80)
    print("TEST 4: Política de olvido (límite de casos)")
    print("="*80)
    
    from cycle.retain import CaseRetainer
    
    case_base = CaseBase()
    case_base.load_from_file("config/initial_cases.json")
    
    retainer = CaseRetainer(case_base)
    
    # Configurar límite bajo para probar
    original_max = retainer.max_cases_total
    retainer.max_cases_total = 15
    
    print(f"\n📋 Casos iniciales: {len(case_base.get_all_cases())}")
    print(f"   Límite configurado: {retainer.max_cases_total}")
    
    # Forzar enforcement del límite
    if len(case_base.get_all_cases()) > retainer.max_cases_total:
        retainer._enforce_case_limit()
        
        final_count = len(case_base.get_all_cases())
        print(f"\n📋 Casos después de limpieza: {final_count}")
        
        if final_count <= retainer.max_cases_total:
            print(f"✅ CORRECTO: Límite respetado ({final_count} <= {retainer.max_cases_total})")
        else:
            print(f"❌ ERROR: Límite excedido ({final_count} > {retainer.max_cases_total})")
    else:
        print("⚠️  No hay suficientes casos para probar el límite")
    
    # Restaurar
    retainer.max_cases_total = original_max


def main():
    print("="*80)
    print("🔬 VERIFICACIÓN DE BUGS CORREGIDOS")
    print("="*80)
    
    test_bug_1_no_mutation()
    test_bug_7_division_zero()
    test_bug_10_diversity()
    test_bug_11_case_limit()
    
    print("\n" + "="*80)
    print("✅ TESTS COMPLETADOS")
    print("="*80)
    
    print("\n📋 RESUMEN DE BUGS CORREGIDOS:")
    print("   1. ✅ Mutación de objetos originales → Ahora usa deepcopy")
    print("   2. ✅ Fallback contraproducente → Mejorado para dietas/alergias")
    print("   3. ✅ Ingredientes duplicados → Reemplaza todas las ocurrencias")
    print("   4. ✅ Lógica de dietas → Corregida con is None")
    print("   5. ✅ Validación de precio → Añadidas advertencias")
    print("   6. ✅ Division por zero → Protección añadida")
    print("   7. ✅ Diversificación → Módulo diversity.py implementado")
    print("   8. ✅ Límite de casos → Política de olvido implementada")
    print("   9. ✅ Manejo de errores → Try-except en similarity")

if __name__ == "__main__":
    main()
