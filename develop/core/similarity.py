"""
Funciones de similitud para el sistema CBR.

Este módulo implementa las métricas de similitud entre casos,
que son fundamentales para la fase de recuperación (Retrieve) del CBR.

La similitud se calcula considerando múltiples dimensiones:
- Tipo de evento
- Temporada
- Rango de precios
- Estilo culinario
- Restricciones dietéticas
- Preferencias culturales
- Número de comensales

Se implementan tanto métricas simples como extensiones con
posibilidad de integrar embeddings o LLMs para similitud semántica.
"""

from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
import math

from .models import (
    Case, Request, Menu, Dish,
    EventType, Season, CulinaryStyle, CulturalTradition,
    DishCategory, Flavor, Complexity
)
from .knowledge import (
    get_preferred_styles_for_event,
    is_style_appropriate_for_event,
    FLAVOR_COMPATIBILITY
)


@dataclass
class SimilarityWeights:
    """
    Pesos para los diferentes componentes de la similitud.
    
    Estos pesos determinan la importancia relativa de cada
    dimensión en el cálculo de similitud total.
    """
    event_type: float = 0.20      # Tipo de evento es muy importante
    season: float = 0.12          # Temporada afecta disponibilidad
    price_range: float = 0.18    # Presupuesto es crítico
    style: float = 0.12           # Estilo culinario
    cultural: float = 0.08        # Tradición cultural
    dietary: float = 0.15         # Restricciones dietéticas críticas
    guests: float = 0.05          # Número de comensales
    wine_preference: float = 0.05 # Preferencia de vino
    success_bonus: float = 0.05   # Bonus por casos exitosos
    
    def normalize(self):
        """Normaliza los pesos para que sumen 1"""
        total = (self.event_type + self.season + self.price_range + 
                self.style + self.cultural + self.dietary + 
                self.guests + self.wine_preference + self.success_bonus)
        if total > 0:
            self.event_type /= total
            self.season /= total
            self.price_range /= total
            self.style /= total
            self.cultural /= total
            self.dietary /= total
            self.guests /= total
            self.wine_preference /= total
            self.success_bonus /= total


class SimilarityCalculator:
    """
    Calculadora de similitud entre casos CBR.
    
    Implementa múltiples métricas de similitud y permite
    configurar los pesos de cada componente.
    """
    
    def __init__(self, weights: Optional[SimilarityWeights] = None):
        """
        Inicializa el calculador de similitud.
        
        Args:
            weights: Pesos para las diferentes dimensiones
        """
        self.weights = weights or SimilarityWeights()
        self.weights.normalize()
    
    def calculate_similarity(self, request: Request, case: Case) -> float:
        """
        Calcula la similitud entre una solicitud y un caso existente.
        
        La similitud es un valor entre 0 (completamente diferente) y 1 (idéntico).
        
        Args:
            request: Solicitud del cliente actual
            case: Caso de la base de conocimiento
            
        Returns:
            Valor de similitud entre 0 y 1
        """
        try:
            similarities = {}
            
            # 1. Similitud por tipo de evento
            similarities['event'] = self._event_similarity(
                request.event_type, case.request.event_type
            )
            
            # 2. Similitud por temporada
            similarities['season'] = self._season_similarity(
                request.season, case.request.season
            )
            
            # 3. Similitud por rango de precios
            similarities['price'] = self._price_similarity(
                request.price_min, request.price_max,
                case.menu.total_price
            )
            
            # 4. Similitud por estilo culinario
            similarities['style'] = self._style_similarity(
                request.preferred_style, request.event_type,
                case.menu.dominant_style
            )
            
            # 5. Similitud cultural
            similarities['cultural'] = self._cultural_similarity(
                request.cultural_preference,
                case.menu.cultural_theme
            )
            
            # 6. Similitud dietética (muy importante - puede ser eliminatoria)
            similarities['dietary'] = self._dietary_similarity(
                request.required_diets,
                case.menu
            )
            
            # 7. Similitud por número de comensales
            similarities['guests'] = self._guests_similarity(
                request.num_guests,
                case.request.num_guests,
                case.menu
            )
            
            # 8. Similitud por preferencia de vino
            similarities['wine'] = self._wine_similarity(
                request.wants_wine,
                case.request.wants_wine
            )
            
            # 9. Bonus por éxito del caso
            similarities['success'] = case.feedback_score / 5.0 if case.success else 0.0
            
            # Calcular similitud ponderada
            total_similarity = (
                self.weights.event_type * similarities['event'] +
                self.weights.season * similarities['season'] +
                self.weights.price_range * similarities['price'] +
                self.weights.style * similarities['style'] +
                self.weights.cultural * similarities['cultural'] +
                self.weights.dietary * similarities['dietary'] +
                self.weights.guests * similarities['guests'] +
                self.weights.wine_preference * similarities['wine'] +
                self.weights.success_bonus * similarities['success']
            )
            
            return total_similarity
        except Exception as e:
            # Manejo de errores: devolver similitud neutra en vez de crashear
            print(f"⚠️  Error calculando similitud: {e}")
            return 0.5  # Similitud neutra por defecto
    
    def _event_similarity(self, req_event: EventType, case_event: EventType) -> float:
        """
        Calcula similitud entre tipos de evento.
        
        Los eventos similares tienen mayor puntuación.
        """
        if req_event == case_event:
            return 1.0
        
        # Matriz de similitud entre eventos
        event_similarity_matrix = {
            (EventType.WEDDING, EventType.COMMUNION): 0.6,
            (EventType.WEDDING, EventType.CHRISTENING): 0.5,
            (EventType.COMMUNION, EventType.CHRISTENING): 0.8,
            (EventType.FAMILIAR, EventType.CHRISTENING): 0.7,
            (EventType.FAMILIAR, EventType.COMMUNION): 0.7,
            (EventType.CONGRESS, EventType.CORPORATE): 0.9,
            (EventType.CORPORATE, EventType.CONGRESS): 0.9,
        }
        
        # Buscar en ambas direcciones
        sim = event_similarity_matrix.get((req_event, case_event), 
              event_similarity_matrix.get((case_event, req_event), 0.3))
        
        return sim
    
    def _season_similarity(self, req_season: Season, case_season: Season) -> float:
        """
        Calcula similitud entre temporadas.
        """
        if req_season == case_season:
            return 1.0
        
        if case_season == Season.ALL or req_season == Season.ALL:
            return 0.9  # ALL es muy flexible
        
        # Temporadas adyacentes tienen cierta similitud
        season_order = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]
        try:
            req_idx = season_order.index(req_season)
            case_idx = season_order.index(case_season)
            distance = min(abs(req_idx - case_idx), 4 - abs(req_idx - case_idx))
            
            if distance == 1:
                return 0.7  # Temporadas adyacentes
            elif distance == 2:
                return 0.3  # Temporadas opuestas
            else:
                return 0.5
        except ValueError:
            return 0.5
    
    def _price_similarity(self, req_min: float, req_max: float, 
                          case_price: float) -> float:
        """
        Calcula similitud por rango de precios.
        
        Un caso dentro del rango tiene similitud 1.
        Fuera del rango, decrece gradualmente.
        """
        if req_min <= case_price <= req_max:
            # Dentro del rango - similitud perfecta
            return 1.0
        
        # Calcular qué tan lejos está del rango
        if case_price < req_min:
            distance = req_min - case_price
            reference = req_min
        else:
            distance = case_price - req_max
            reference = req_max
        
        # Penalización proporcional a la distancia
        # Tolerancia del 20% del rango
        if req_max > req_min:
            tolerance = (req_max - req_min) * 0.2
        else:
            tolerance = 10  # Tolerancia por defecto si min=max
        
        if tolerance == 0:
            tolerance = 10  # Evitar division por zero
        
        similarity = max(0, 1 - (distance / tolerance))
        
        return similarity
    
    def _style_similarity(self, req_style: Optional[CulinaryStyle],
                          req_event: EventType,
                          case_style: Optional[CulinaryStyle]) -> float:
        """
        Calcula similitud por estilo culinario.
        
        Considera tanto el estilo preferido como la adecuación al evento.
        """
        if req_style is None and case_style is None:
            return 0.8  # Ambos flexibles
        
        if req_style is not None and req_style == case_style:
            return 1.0  # Coincidencia exacta
        
        # Si no hay preferencia, evaluar si el estilo del caso es apropiado para el evento
        if req_style is None and case_style is not None:
            if is_style_appropriate_for_event(case_style, req_event):
                return 0.9
            return 0.5
        
        # Si hay preferencia pero no coincide
        if req_style is not None and case_style is not None:
            # Verificar si ambos son apropiados para el evento
            preferred_styles = get_preferred_styles_for_event(req_event)
            req_in_preferred = req_style in preferred_styles
            case_in_preferred = case_style in preferred_styles
            
            if req_in_preferred and case_in_preferred:
                return 0.7  # Ambos son apropiados
            elif case_in_preferred:
                return 0.5
            else:
                return 0.3
        
        return 0.5
    
    def _cultural_similarity(self, req_culture: Optional[CulturalTradition],
                            case_culture: Optional[CulturalTradition]) -> float:
        """
        Calcula similitud cultural/gastronómica.
        
        Considera relaciones entre tradiciones culinarias similares.
        """
        if req_culture is None:
            return 0.8  # Sin preferencia cultural = flexible
        
        if req_culture == case_culture:
            return 1.0  # Match exacto
        
        if case_culture is None:
            return 0.6  # El caso no tiene tema cultural definido
        
        # Culturas relacionadas (basado en ingredientes y técnicas similares)
        cultural_relations = {
            # Mediterráneas - comparten aceite de oliva, hierbas
            (CulturalTradition.ITALIAN, CulturalTradition.SPANISH): 0.8,
            (CulturalTradition.ITALIAN, CulturalTradition.FRENCH): 0.7,
            (CulturalTradition.SPANISH, CulturalTradition.FRENCH): 0.6,
            (CulturalTradition.LEBANESE, CulturalTradition.ITALIAN): 0.5,
            
            # Asiáticas orientales - soja, arroz, wok
            (CulturalTradition.CHINESE, CulturalTradition.JAPANESE): 0.7,
            (CulturalTradition.CHINESE, CulturalTradition.KOREAN): 0.8,
            (CulturalTradition.JAPANESE, CulturalTradition.KOREAN): 0.7,
            
            # Asiáticas del sureste - coco, citricos, fish sauce
            (CulturalTradition.THAI, CulturalTradition.VIETNAMESE): 0.9,
            
            # Latinas - chili, maíz, frijoles
            (CulturalTradition.MEXICAN, CulturalTradition.SPANISH): 0.5,
            
            # Influencia francesa
            (CulturalTradition.FRENCH, CulturalTradition.VIETNAMESE): 0.4,  # Influencia colonial
            (CulturalTradition.FRENCH, CulturalTradition.LEBANESE): 0.4,
            
            # India y Oriente Medio
            (CulturalTradition.INDIAN, CulturalTradition.LEBANESE): 0.5,
            
            # América
            (CulturalTradition.AMERICAN, CulturalTradition.MEXICAN): 0.6,
        }
        
        # Buscar relación bidireccional
        sim = cultural_relations.get((req_culture, case_culture),
              cultural_relations.get((case_culture, req_culture), 0.3))
        
        return sim
    
    def _dietary_similarity(self, required_diets: List[str], menu: Menu) -> float:
        """
        Calcula similitud dietética.
        
        IMPORTANTE: Si las dietas requeridas no se cumplen,
        la similitud es muy baja (puede ser eliminatoria).
        """
        if not required_diets:
            return 1.0  # Sin restricciones = todo vale
        
        menu_diets = menu.get_all_diets()
        
        # Verificar cuántas dietas requeridas cumple el menú
        fulfilled = sum(1 for diet in required_diets if diet in menu_diets)
        
        if fulfilled == len(required_diets):
            return 1.0  # Cumple todas
        
        # Penalización proporcional a dietas no cumplidas
        ratio = fulfilled / len(required_diets)
        
        # Si no cumple ninguna, penalización severa
        if ratio == 0:
            return 0.1
        
        return ratio * 0.8  # Máximo 0.8 si no cumple todas
    
    def _guests_similarity(self, req_guests: int, case_guests: int, 
                           menu: Menu) -> float:
        """
        Calcula similitud por número de comensales.
        
        Verifica que el menú pueda servir a la cantidad de invitados.
        """
        # Verificar capacidad máxima del menú
        max_capacity = min(
            menu.starter.max_guests,
            menu.main_course.max_guests,
            menu.dessert.max_guests
        )
        
        if req_guests > max_capacity:
            # El menú no puede servir a tantos invitados
            return 0.2
        
        # Similitud basada en escala del evento
        ratio = min(req_guests, case_guests) / max(req_guests, case_guests)
        
        return ratio
    
    def _wine_similarity(self, req_wine: bool, case_wine: bool) -> float:
        """
        Calcula similitud por preferencia de vino/alcohol.
        """
        if req_wine == case_wine:
            return 1.0
        return 0.5  # Diferente preferencia pero no es crítico
    
    def calculate_detailed_similarity(self, request: Request, 
                                       case: Case) -> Dict[str, float]:
        """
        Calcula similitud detallada con desglose por componente.
        
        Útil para explicabilidad del sistema.
        
        Args:
            request: Solicitud del cliente
            case: Caso de la base
            
        Returns:
            Diccionario con similitud por cada dimensión
        """
        details = {
            'event_type': self._event_similarity(request.event_type, case.request.event_type),
            'season': self._season_similarity(request.season, case.request.season),
            'price_range': self._price_similarity(request.price_min, request.price_max, case.menu.total_price),
            'style': self._style_similarity(request.preferred_style, request.event_type, case.menu.dominant_style),
            'cultural': self._cultural_similarity(request.cultural_preference, case.menu.cultural_theme),
            'dietary': self._dietary_similarity(request.required_diets, case.menu),
            'guests': self._guests_similarity(request.num_guests, case.request.num_guests, case.menu),
            'wine': self._wine_similarity(request.wants_wine, case.request.wants_wine),
            'success_bonus': case.feedback_score / 5.0 if case.success else 0.0
        }
        
        # Calcular total ponderado
        details['total'] = (
            self.weights.event_type * details['event_type'] +
            self.weights.season * details['season'] +
            self.weights.price_range * details['price_range'] +
            self.weights.style * details['style'] +
            self.weights.cultural * details['cultural'] +
            self.weights.dietary * details['dietary'] +
            self.weights.guests * details['guests'] +
            self.weights.wine_preference * details['wine'] +
            self.weights.success_bonus * details['success_bonus']
        )
        
        return details


def calculate_dish_similarity(dish1: Dish, dish2: Dish) -> float:
    """
    Calcula la similitud entre dos platos.
    
    Útil para la fase de adaptación cuando se buscan
    platos alternativos similares.
    
    Args:
        dish1: Primer plato
        dish2: Segundo plato
        
    Returns:
        Similitud entre 0 y 1
    """
    similarities = []
    
    # Mismo tipo de plato (starter, main, dessert)
    if dish1.dish_type != dish2.dish_type:
        return 0.0  # No tiene sentido comparar platos de diferente tipo
    
    # Similitud de categoría
    if dish1.category == dish2.category:
        similarities.append(1.0)
    else:
        similarities.append(0.3)
    
    # Similitud de precio (dentro del 30%)
    max_price = max(dish1.price, dish2.price)
    if max_price == 0:
        price_ratio = 1.0  # Ambos gratis
    else:
        price_ratio = min(dish1.price, dish2.price) / max_price
    similarities.append(price_ratio)
    
    # Similitud de complejidad
    complexity_order = [Complexity.LOW, Complexity.MEDIUM, Complexity.HIGH]
    try:
        c1_idx = complexity_order.index(dish1.complexity)
        c2_idx = complexity_order.index(dish2.complexity)
        complexity_sim = 1.0 - abs(c1_idx - c2_idx) / 2.0
        similarities.append(complexity_sim)
    except ValueError:
        similarities.append(0.5)
    
    # Similitud de sabores
    common_flavors = set(dish1.flavors) & set(dish2.flavors)
    all_flavors = set(dish1.flavors) | set(dish2.flavors)
    if all_flavors:
        flavor_sim = len(common_flavors) / len(all_flavors)
    else:
        flavor_sim = 0.5
    similarities.append(flavor_sim)
    
    # Similitud de estilos
    common_styles = set(dish1.styles) & set(dish2.styles)
    all_styles = set(dish1.styles) | set(dish2.styles)
    if all_styles:
        style_sim = len(common_styles) / len(all_styles)
    else:
        style_sim = 0.5
    similarities.append(style_sim)
    
    # Similitud de calorías (tolerancia del 20%)
    max_cal = max(dish1.calories, dish2.calories)
    if max_cal == 0:
        cal_ratio = 1.0  # Ambos sin calorías
    else:
        cal_ratio = min(dish1.calories, dish2.calories) / max_cal
    similarities.append(cal_ratio)
    
    # Promediar todas las similitudes
    return sum(similarities) / len(similarities)


def calculate_menu_similarity(menu1: Menu, menu2: Menu) -> float:
    """
    Calcula la similitud entre dos menús completos.
    
    Args:
        menu1: Primer menú
        menu2: Segundo menú
        
    Returns:
        Similitud entre 0 y 1
    """
    # Similitud de cada componente
    starter_sim = calculate_dish_similarity(menu1.starter, menu2.starter)
    main_sim = calculate_dish_similarity(menu1.main_course, menu2.main_course)
    dessert_sim = calculate_dish_similarity(menu1.dessert, menu2.dessert)
    
    # Similitud de precio total
    max_price = max(menu1.total_price, menu2.total_price)
    if max_price == 0:
        price_sim = 1.0  # Ambos son gratis
    else:
        price_sim = min(menu1.total_price, menu2.total_price) / max_price
    
    # Similitud de estilo dominante
    style_sim = 1.0 if menu1.dominant_style == menu2.dominant_style else 0.5
    
    # Ponderación: principal tiene más peso
    return (
        0.20 * starter_sim +
        0.35 * main_sim +
        0.20 * dessert_sim +
        0.15 * price_sim +
        0.10 * style_sim
    )


class SemanticSimilarityCalculator:
    """
    Calculadora de similitud semántica usando embeddings.
    
    Esta clase está preparada para integrar modelos de embeddings
    (como sentence-transformers) o LLMs para calcular similitudes
    más sofisticadas basadas en descripciones textuales.
    
    NOTA: Requiere instalación adicional de bibliotecas de ML.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el calculador semántico.
        
        Args:
            model_name: Nombre del modelo de embeddings a usar
        """
        self.model = None
        self.model_name = model_name
        self._try_load_model()
    
    def _try_load_model(self):
        """Intenta cargar el modelo de embeddings si está disponible"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        except ImportError:
            self.model = None
    
    def is_available(self) -> bool:
        """Verifica si la similitud semántica está disponible"""
        return self.model is not None
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud semántica entre dos textos.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            Similitud entre 0 y 1
        """
        if not self.is_available():
            return 0.5  # Valor neutro si no está disponible
        
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        embeddings = self.model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # Normalizar a [0, 1]
        return (similarity + 1) / 2
    
    def get_dish_description(self, dish: Dish) -> str:
        """
        Genera una descripción textual de un plato para embeddings.
        
        Args:
            dish: Plato a describir
            
        Returns:
            Descripción textual
        """
        parts = [
            dish.name,
            f"Category: {dish.category.value}",
            f"Style: {', '.join(s.value for s in dish.styles)}",
            f"Flavors: {', '.join(f.value for f in dish.flavors)}",
            f"Temperature: {dish.temperature.value}",
            f"Complexity: {dish.complexity.value}",
        ]
        
        if dish.cultural_traditions:
            parts.append(f"Traditions: {', '.join(t.value for t in dish.cultural_traditions)}")
        
        if dish.chef_style:
            parts.append(f"Chef style: {dish.chef_style}")
        
        return ". ".join(parts)
    
    def calculate_semantic_dish_similarity(self, dish1: Dish, dish2: Dish) -> float:
        """
        Calcula similitud semántica entre dos platos.
        
        Args:
            dish1: Primer plato
            dish2: Segundo plato
            
        Returns:
            Similitud entre 0 y 1
        """
        if not self.is_available():
            return calculate_dish_similarity(dish1, dish2)
        
        desc1 = self.get_dish_description(dish1)
        desc2 = self.get_dish_description(dish2)
        
        return self.calculate_text_similarity(desc1, desc2)
