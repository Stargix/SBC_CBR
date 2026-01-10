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

from typing import List, Dict, Tuple, Optional, Callable, Set
from dataclasses import dataclass
import math
import json
import os

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
    dietary: float = 0.10         # Restricciones dietéticas (se pueden adaptar)
    guests: float = 0.05          # Número de comensales
    wine_preference: float = 0.05 # Preferencia de vino
    success_bonus: float = 0.10   # Bonus por casos exitosos (incrementado)
    
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


@dataclass
class DishSimilarityWeights:
    """
    Pesos para los diferentes componentes de la similitud de platos.
    
    Estos pesos determinan la importancia relativa de cada característica
    del plato al buscar alternativas similares durante la adaptación.
    """
    category: float = 0.15        # Categoría del plato (soup, pasta, etc.)
    price: float = 0.15           # Precio del plato
    complexity: float = 0.10      # Complejidad de preparación
    flavors: float = 0.15         # Perfiles de sabor
    styles: float = 0.15          # Estilos culinarios
    temperature: float = 0.05     # Temperatura (hot/cold)
    diets: float = 0.10           # Restricciones dietéticas
    cultural: float = 0.15        # Adecuación cultural
    
    def normalize(self):
        """Normaliza los pesos para que sumen 1"""
        total = (self.category + self.price + self.complexity + 
                self.flavors + self.styles + self.temperature + 
                self.diets + self.cultural)
        if total > 0:
            self.category /= total
            self.price /= total
            self.complexity /= total
            self.flavors /= total
            self.styles /= total
            self.temperature /= total
            self.diets /= total
            self.cultural /= total


class SimilarityCalculator:
    """
    Calculadora de similitud entre casos CBR.
    
    Implementa múltiples métricas de similitud y permite
    configurar los pesos de cada componente.
    """
    
    def __init__(self, weights: Optional[SimilarityWeights] = None,
                 allow_dietary_adaptation: bool = True,
                 use_embeddings_for_culture: bool = True,
                 semantic_calculator: Optional['SemanticSimilarityCalculator'] = None):
        """
        Inicializa el calculador de similitud.
        
        Args:
            weights: Pesos para las diferentes dimensiones
            allow_dietary_adaptation: Si True, permite recuperar casos con 
                                     restricciones no cumplidas para adaptarlos
            use_embeddings_for_culture: Si True, usa embeddings para similaridad cultural
            semantic_calculator: Calculador semántico (se crea automáticamente si es None)
        """
        self.weights = weights or SimilarityWeights()
        self.weights.normalize()
        self.allow_dietary_adaptation = allow_dietary_adaptation
        self.use_embeddings_for_culture = use_embeddings_for_culture
        
        # Inicializar semantic calculator si se requiere
        if use_embeddings_for_culture and semantic_calculator is None:
            try:
                self.semantic_calculator = SemanticSimilarityCalculator()
            except Exception as e:
                print(f"Warning: Could not initialize semantic calculator: {e}")
                self.semantic_calculator = None
                self.use_embeddings_for_culture = False
        else:
            self.semantic_calculator = semantic_calculator
        
        # Cargar conocimiento de ingredientes para análisis cultural
        self._load_ingredients_knowledge()
    
    def _load_ingredients_knowledge(self):
        """Carga el conocimiento de ingredientes desde JSON para análisis cultural"""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'ingredients.json'
        )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.ingredient_to_cultures = data['ingredient_to_cultures']
        self.cultures = data['cultures']
        
        # Construir índice cultura -> ingredientes
        self.culture_to_ingredients = {}
        for ingredient, data in self.ingredient_to_cultures.items():
            cultures = data.get('cultures', []) if isinstance(data, dict) else data
            for culture in cultures:
                if culture not in self.culture_to_ingredients:
                    self.culture_to_ingredients[culture] = set()
                self.culture_to_ingredients[culture].add(ingredient)
    
    def _adjust_weights_for_request(self, request: Request) -> SimilarityWeights:
        """
        Ajusta dinámicamente los pesos según los campos especificados en el request.
        
        Si un campo tiene un valor especial que indica "no especificado", 
        su peso se reduce a 0 para esta petición y se redistribuye proporcionalmente
        entre los demás campos activos.
        
        Valores especiales:
        - event_type=ANY, season=ALL, num_guests=-1, price=-1, 
        - preferred_style=None, cultural_preference=None, required_diets=[]
        
        Args:
            request: Solicitud del cliente
            
        Returns:
            SimilarityWeights ajustado para esta petición (NO modifica self.weights)
        """
        # Crear copia de los pesos originales
        import copy
        from .models import EventType, Season
        adjusted = copy.deepcopy(self.weights)
        
        # Determinar qué campos NO están especificados (valores especiales)
        fields_to_zero = []
        
        # 1. event_type: EventType.ANY = no especificado
        if request.event_type == EventType.ANY:
            fields_to_zero.append('event_type')
            adjusted.event_type = 0.0
        
        # 2. season: Season.ALL = no especificado
        if request.season == Season.ALL:
            fields_to_zero.append('season')
            adjusted.season = 0.0
        
        # 3. num_guests: -1 = no especificado
        if request.num_guests == -1:
            fields_to_zero.append('guests')
            adjusted.guests = 0.0
        
        # 4. price_range: -1 en ambos = no especificado
        # Si solo uno está especificado, el otro toma un valor sensato
        if request.price_min == -1.0 and request.price_max == -1.0:
            fields_to_zero.append('price_range')
            adjusted.price_range = 0.0
        
        # 5. preferred_style: None = no especificado
        if request.preferred_style is None:
            fields_to_zero.append('style')
            adjusted.style = 0.0
        
        # 6. cultural_preference: None = no especificado
        if request.cultural_preference is None:
            fields_to_zero.append('cultural')
            adjusted.cultural = 0.0
        
        # 7. required_diets: lista vacía = no especificado
        if not request.required_diets:
            fields_to_zero.append('dietary')
            adjusted.dietary = 0.0
        
        # 8. wants_wine: False = no le importa el vino
        if not request.wants_wine and not request.wine_per_dish:
            fields_to_zero.append('wine_preference')
            adjusted.wine_preference = 0.0
        
        # NOTA: success_bonus NUNCA se pone a 0 porque no depende del request,
        # sino del historial de éxito del caso
        
        # Si se redujo algún peso, normalizar para redistribuir
        if fields_to_zero:
            adjusted.normalize()
        
        return adjusted
    
    def calculate_similarity(self, request: Request, case: Case) -> float:
        """
        Calcula la similitud entre una solicitud y un caso existente.
        
        La similitud es un valor entre 0 (completamente diferente) y 1 (idéntico).
        
        IMPORTANTE: Ajusta dinámicamente los pesos según los campos especificados
        en el request. Si un campo es None o vacío, su peso se reduce a 0 para
        esta petición específica, sin modificar los pesos base.
        
        Args:
            request: Solicitud del cliente actual
            case: Caso de la base de conocimiento
            
        Returns:
            Valor de similitud entre 0 y 1
        """
        try:
            # Crear copia de pesos para ajustar dinámicamente (NO modifica self.weights)
            active_weights = self._adjust_weights_for_request(request)
            
            similarities = {}
            
            # 1. Similitud por tipo de evento
            similarities['event'] = self._event_similarity(
                request.event_type, case.request.event_type,
                case.menu.dominant_style
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
                case.request.wants_wine,
                case.menu.beverage
            )
            
            # 9. Bonus por éxito del caso
            similarities['success'] = case.feedback_score / 5.0 if case.success else 0.0
            
            # Calcular similitud ponderada con pesos ajustados
            total_similarity = (
                active_weights.event_type * similarities['event'] +
                active_weights.season * similarities['season'] +
                active_weights.price_range * similarities['price'] +
                active_weights.style * similarities['style'] +
                active_weights.cultural * similarities['cultural'] +
                active_weights.dietary * similarities['dietary'] +
                active_weights.guests * similarities['guests'] +
                active_weights.wine_preference * similarities['wine'] +
                active_weights.success_bonus * similarities['success']
            )
            
            return total_similarity
        except Exception as e:
            # Manejo de errores: devolver similitud neutra en vez de crashear
            print(f"⚠️  Error calculando similitud: {e}")
            return 0.5  # Similitud neutra por defecto
    
    def _event_similarity(self, req_event: EventType, case_event: EventType, 
                          case_menu_style: Optional[CulinaryStyle] = None) -> float:
        """
        Calcula similitud entre tipos de evento.
        
        Si req_event=EventType.ANY, significa que no se especificó tipo
        (este caso se maneja en _adjust_weights_for_request poniendo peso=0).
        
        MEJORADO: Cuando los eventos coinciden, verifica que el estilo del menú
        del caso sea apropiado para ese tipo de evento.
        
        Los eventos similares tienen mayor puntuación.
        """
        # Si no especificó tipo de evento (ANY), devolver neutral (aunque el peso debería ser 0)
        if req_event == EventType.ANY:
            return 0.8  # Neutral - acepta cualquier evento
        
        if req_event == case_event:
            # Mismo evento - verificar si el estilo es apropiado
            if case_menu_style and not is_style_appropriate_for_event(case_menu_style, req_event):
                return 0.8  # Mismo evento pero estilo no apropiado (penalización leve)
            return 1.0  # Mismo evento con estilo apropiado o sin estilo definido
        
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
        
        Si price_min=-1 y price_max=-1, significa que no se especificó rango
        (este caso se maneja en _adjust_weights_for_request poniendo peso=0).
        
        Si solo uno está especificado (-1 en el otro), se infiere el rango:
        - Si req_min=-1 pero req_max=X: rango [0, X]
        - Si req_max=-1 pero req_min=X: rango [X, infinito] (tolerante)
        
        Un caso dentro del rango tiene similitud 1.
        Fuera del rango, decrece gradualmente.
        """
        # Si no especificó rango (-1 en ambos), devolver neutral (aunque el peso debería ser 0)
        if req_min == -1.0 and req_max == -1.0:
            return 0.8  # Neutral
        
        # Si solo especificó max, asumir min=0
        if req_min == -1.0:
            req_min = 0.0
        
        # Si solo especificó min, ser muy tolerante con el máximo
        if req_max == -1.0:
            req_max = req_min * 5  # Rango muy amplio hacia arriba
        
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
        
        MEJORADO: Se enfoca en preferencias EXPLÍCITAS de estilo del usuario.
        La validación de estilos apropiados para eventos ya se hace en _event_similarity.
        """
        # Si el usuario NO especificó estilo, es neutral
        # (la validación de estilo apropiado ya se hizo en event_similarity)
        if req_style is None:
            return 0.9  # Neutral - sin preferencia explícita
        
        # Si el usuario SÍ especificó estilo
        if req_style == case_style:
            return 1.0  # Match exacto con la preferencia del usuario
        
        # El usuario pidió un estilo específico pero el caso tiene otro
        if case_style is not None:
            # Verificar si ambos estilos son apropiados para el evento
            preferred_styles = get_preferred_styles_for_event(req_event)
            req_in_preferred = req_style in preferred_styles
            case_in_preferred = case_style in preferred_styles
            
            if req_in_preferred and case_in_preferred:
                return 0.7  # Ambos apropiados para el evento, aunque no coinciden
            elif case_in_preferred:
                return 0.5  # Al menos el caso es apropiado
            else:
                return 0.3  # El caso no es apropiado para el evento
        
        # El caso no tiene estilo definido pero el usuario sí pidió uno
        return 0.6
    
    def _cultural_similarity(self, req_culture: Optional[CulturalTradition],
                            case_culture: Optional[CulturalTradition]) -> float:
        """
        Calcula similitud cultural/gastronómica.
        
        Si use_embeddings_for_culture=True y hay un semantic_calculator disponible,
        usa embeddings semánticos. De lo contrario, usa las relaciones hardcodeadas.
        
        Considera relaciones entre tradiciones culinarias similares.
        """
        if req_culture is None:
            return 0.8  # Sin preferencia cultural = flexible
        
        if req_culture == case_culture:
            return 1.0  # Match exacto
        
        if case_culture is None:
            return 0.6  # El caso no tiene tema cultural definido
        
        # Intentar usar embeddings si está habilitado y disponible
        if (self.use_embeddings_for_culture and 
            self.semantic_calculator and 
            self.semantic_calculator.is_available()):
            return self.semantic_calculator.calculate_cultural_similarity(
                req_culture, case_culture
            )
        
        # Fallback: Culturas relacionadas (basado en ingredientes y técnicas similares)
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
    
    def is_ingredient_cultural(self, ingredient: str, 
                              culture: CulturalTradition,
                              include_universal: bool = True) -> bool:
        """
        Verifica si un ingrediente es apropiado para una cultura.
        
        Args:
            ingredient: Ingrediente a verificar
            culture: Tradición cultural
            include_universal: Si True, considera universales como apropiados.
                             Si False, solo ingredientes específicos de la cultura.
            
        Returns:
            True si el ingrediente es apropiado para esa cultura
        """
        ing_data = self.ingredient_to_cultures.get(ingredient, {})
        cultures = ing_data.get('cultures', []) if isinstance(ing_data, dict) else ing_data
        
        cultures_lower = [c.lower() for c in cultures] if isinstance(cultures, list) else []
        
        # Manejar cultura como string o enum
        if isinstance(culture, str):
            culture_name = culture.lower()
        else:
            culture_name = culture.value.lower()
        
        # Verificar si pertenece específicamente a la cultura
        if culture_name in cultures_lower:
            return True
        
        # Si include_universal, considerar universales como apropiados
        if include_universal and 'universal' in cultures_lower:
            return True
        
        return False
    
    def get_cultural_score(self, ingredients: List[str], 
                          culture: CulturalTradition) -> float:
        """
        Calcula qué tan culturalmente apropiados son los ingredientes.
        
        Este método analiza la proporción de ingredientes de un plato que son
        característicos o apropiados para una cultura gastronómica específica.
        
        MEJORADO: Considera distancia semántica entre culturas.
        
        Orden de evaluación (importante para evitar que universales den 100%):
        1. Ingredientes desconocidos (no en base): peso 0.5 (neutro)
        2. Ingredientes universales: peso 0.7
        3. Ingredientes de la cultura exacta: peso 1.0
        4. Ingredientes de culturas similares: peso proporcional a similaridad (>0.7)
        5. Ingredientes conocidos sin culturas: peso 0.5 (neutro)
        6. Ingredientes de culturas no relacionadas: peso 0.0
        
        PENALIZACIÓN POR POCOS INGREDIENTES:
        Platos con pocos ingredientes son menos representativos de la cultura.
        Factor de confianza suavizado:
        - 1 ingrediente: score * 0.6 (moderadamente poco confiable)
        - 2 ingredientes: score * 0.8 (poco confiable)
        - 3 ingredientes: score * 0.9 (casi confiable)
        - 4+ ingredientes: score * 1.0 (totalmente confiable)
        
        NOTA: Los ingredientes desconocidos reciben score neutro (0.5) para no
        penalizar platos que usan ingredientes válidos pero filtrados de la
        base de conocimiento por ser menos comunes.
        
        Args:
            ingredients: Lista de ingredientes
            culture: Cultura a evaluar
            
        Returns:
            Score 0.0-1.0, donde 1.0 significa que todos los ingredientes
            son apropiados para la cultura
        """
        if not ingredients:
            return 0.5
        
        total_score = 0.0
        
        for ingredient in ingredients:
            # Caso 1: Verificar si el ingrediente existe en la base de conocimiento
            ing_data = self.ingredient_to_cultures.get(ingredient, None)
            
            if ing_data is None:
                # Ingrediente NO encontrado en ingredients.json (fue filtrado o es desconocido)
                # Darle score neutro para no penalizar platos con ingredientes válidos
                total_score += 0.5
                continue
            
            # Caso 2: Ingrediente universal (verificar ANTES que cultura específica)
            if isinstance(ing_data, dict):
                cultures = ing_data.get('cultures', [])
            else:
                cultures = ing_data if isinstance(ing_data, list) else []
            
            cultures_lower = [c.lower() for c in cultures]
            if 'universal' in cultures_lower:
                total_score += 0.7
                continue
            
            # Caso 3: Ingrediente pertenece específicamente a la cultura objetivo
            if self.is_ingredient_cultural(ingredient, culture, include_universal=False):
                total_score += 1.0
                continue
            
            # Caso 4: Ingrediente de cultura semánticamente similar
            if self.use_embeddings_for_culture and self.semantic_calculator:
                max_similarity = 0.0
                
                # Verificar a qué culturas pertenece el ingrediente
                for ing_culture_name in cultures:
                    try:
                        # Convertir nombre de cultura a enum
                        ing_culture = CulturalTradition(ing_culture_name.lower())
                        
                        # Calcular similaridad semántica
                        similarity = self.semantic_calculator.calculate_cultural_similarity(
                            culture, ing_culture
                        )
                        
                        max_similarity = max(max_similarity, similarity)
                    except (ValueError, AttributeError):
                        # Cultura no válida o error, continuar
                        continue
                
                # Usar la similaridad más alta encontrada (con threshold mínimo)
                if max_similarity > 0.7:  # Solo si hay similaridad significativa
                    total_score += max_similarity
                    continue
            
            # Caso 5: Ingrediente conocido pero no relacionado con ninguna cultura
            # (ingrediente existe en base pero no tiene culturas asignadas)
            if not cultures:
                total_score += 0.5  # Score neutro
            # Si tiene culturas pero ninguna es similar, no suma (0.0 implícito)
        
        # Calcular score base
        base_score = total_score / len(ingredients) if ingredients else 0.5
        
        # Aplicar factor de confianza basado en número de ingredientes
        # Platos con pocos ingredientes son menos representativos
        # Factor más suave para no penalizar demasiado
        num_ingredients = len(ingredients)
        if num_ingredients == 1:
            confidence_factor = 0.6  # Penalización moderada
        elif num_ingredients == 2:
            confidence_factor = 0.8  # Penalización leve
        elif num_ingredients == 3:
            confidence_factor = 0.9  # Penalización muy leve
        else:
            confidence_factor = 1.0  # Sin penalización (4+ ingredientes)
        
        # Score final penalizado por falta de ingredientes
        final_score = base_score * confidence_factor
        
        return final_score
    
    def _dietary_similarity(self, required_diets: List[str], menu: Menu) -> float:
        """
        Calcula similitud dietética.
        
        Si allow_dietary_adaptation=True, la penalización es gradual para permitir
        recuperar casos que puedan ser adaptados en la fase de Adapt.
        Si False, la penalización es más severa (comportamiento más estricto).
        
        La estrategia CBR completa es:
        1. Retrieve: Recuperar casos con penalización suave
        2. Reuse: Adaptar ingredientes para cumplir restricciones
        3. Revise: Validar que se cumplen tras adaptación
        4. Retain: Guardar caso adaptado exitoso
        """
        if not required_diets:
            return 1.0  # Sin restricciones = todo vale
        
        menu_diets = menu.get_all_diets()
        
        # Verificar cuántas dietas requeridas cumple el menú
        fulfilled = sum(1 for diet in required_diets if diet in menu_diets)
        
        if fulfilled == len(required_diets):
            return 1.0  # Cumple todas - caso ideal
        
        # Calcular ratio de cumplimiento
        ratio = fulfilled / len(required_diets)
        
        if self.allow_dietary_adaptation:
            # Modo adaptativo: penalización gradual más suave
            # Permite recuperar casos para adaptar posteriormente
            if ratio == 0:
                # No cumple ninguna restricción: aún recuperable si es muy similar en otros aspectos
                return 0.3  # Penalización moderada, no eliminatoria
            elif ratio < 0.5:
                # Cumple menos de la mitad
                return 0.4 + (ratio * 0.3)  # Entre 0.4 y 0.55
            else:
                # Cumple más de la mitad
                return 0.6 + (ratio * 0.3)  # Entre 0.6 y 0.9
        else:
            # Modo estricto: penalización severa (comportamiento original)
            if ratio == 0:
                return 0.1  # Casi eliminatorio
            else:
                return ratio * 0.8  # Máximo 0.8 si no cumple todas
    
    def _guests_similarity(self, req_guests: int, case_guests: int, 
                           menu: Menu) -> float:
        """
        Calcula similitud por número de comensales.
        
        Si req_guests=-1, significa que no se especificó cantidad
        (este caso se maneja en _adjust_weights_for_request poniendo peso=0).
        
        Verifica que el menú pueda servir a la cantidad de invitados.
        """
        # Si no especificó cantidad (-1), devolver neutral (aunque el peso debería ser 0)
        if req_guests == -1:
            return 0.8  # Neutral
        
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
    
    def _wine_similarity(self, req_wine: bool, case_wine: bool, case_beverage) -> float:
        """
        Calcula similitud por preferencia de vino/alcohol.
        
        MEJORADO: Si ambos quieren vino, compara también el subtype
        para preferir casos con tipos de vino compatibles.
        
        Args:
            req_wine: Si la solicitud quiere vino
            case_wine: Si el caso tiene vino
            case_beverage: Bebida del caso (para comparar subtype)
        
        Returns:
            Similitud 0.0-1.0
        """
        # Si ninguno quiere vino
        if not req_wine and not case_wine:
            return 1.0  # Match perfecto
        
        # Si uno quiere y otro no
        if req_wine != case_wine:
            return 0.5  # No ideal pero no crítico
        
        # Ambos quieren vino - evaluar si la bebida del caso es vino
        if req_wine and case_wine:
            # Si el caso tiene bebida alcohólica con subtype, es un buen match
            if case_beverage and case_beverage.alcoholic:
                if case_beverage.subtype:
                    return 1.0  # Tiene vino con tipo definido
                return 0.8  # Tiene vino pero sin subtype específico
            return 0.6  # Quiere vino pero el caso no tiene vino adecuado
        
        return 1.0
    
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
            'event_type': self._event_similarity(request.event_type, case.request.event_type, case.menu.dominant_style),
            'season': self._season_similarity(request.season, case.request.season),
            'price_range': self._price_similarity(request.price_min, request.price_max, case.menu.total_price),
            'style': self._style_similarity(request.preferred_style, request.event_type, case.menu.dominant_style),
            'cultural': self._cultural_similarity(request.cultural_preference, case.menu.cultural_theme),
            'dietary': self._dietary_similarity(request.required_diets, case.menu),
            'guests': self._guests_similarity(request.num_guests, case.request.num_guests, case.menu),
            'wine': self._wine_similarity(request.wants_wine, case.request.wants_wine, case.menu.beverage),
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


def calculate_dish_similarity(dish1: Dish, dish2: Dish, 
                            target_culture: Optional[CulturalTradition] = None,
                            similarity_calc: Optional[SimilarityCalculator] = None,
                            weights: Optional[DishSimilarityWeights] = None) -> float:
    """
    Calcula la similitud entre dos platos considerando múltiples dimensiones.
    
    MEJORADO: 
    - Incluye cultura como dimensión cuando se proporciona target_culture
    - Acepta pesos configurables (DishSimilarityWeights)
    - Compatible con aprendizaje adaptativo de pesos
    
    Útil para la fase de adaptación cuando se buscan platos alternativos similares.
    
    Args:
        dish1: Primer plato (plato original)
        dish2: Segundo plato (candidato de reemplazo)
        target_culture: Cultura objetivo (opcional, para evaluar adecuación cultural)
        similarity_calc: Calculador de similitud (opcional, para evaluar cultura)
        weights: Pesos configurables (si None, usa pesos por defecto)
        
    Returns:
        Similitud entre 0 y 1
    """
    # Mismo tipo de plato (starter, main, dessert)
    if dish1.dish_type != dish2.dish_type:
        return 0.0  # No tiene sentido comparar platos de diferente tipo
    
    # Usar pesos por defecto si no se proporcionan
    if weights is None:
        weights = DishSimilarityWeights()
        weights.normalize()
    
    # Diccionario de similitudes parciales
    similarities = {}
    
    # 1. Similitud de categoría
    if dish1.category == dish2.category:
        similarities['category'] = 1.0
    else:
        similarities['category'] = 0.3
    
    # 2. Similitud de precio
    max_price = max(dish1.price, dish2.price)
    if max_price == 0:
        similarities['price'] = 1.0
    else:
        similarities['price'] = min(dish1.price, dish2.price) / max_price
    
    # 3. Similitud de complejidad
    complexity_order = [Complexity.LOW, Complexity.MEDIUM, Complexity.HIGH]
    try:
        c1_idx = complexity_order.index(dish1.complexity)
        c2_idx = complexity_order.index(dish2.complexity)
        similarities['complexity'] = 1.0 - abs(c1_idx - c2_idx) / 2.0
    except ValueError:
        similarities['complexity'] = 0.5
    
    # 4. Similitud de sabores
    common_flavors = set(dish1.flavors) & set(dish2.flavors)
    all_flavors = set(dish1.flavors) | set(dish2.flavors)
    if all_flavors:
        similarities['flavors'] = len(common_flavors) / len(all_flavors)
    else:
        similarities['flavors'] = 0.5
    
    # 5. Similitud de estilos
    common_styles = set(dish1.styles) & set(dish2.styles)
    all_styles = set(dish1.styles) | set(dish2.styles)
    if all_styles:
        similarities['styles'] = len(common_styles) / len(all_styles)
    else:
        similarities['styles'] = 0.5
    
    # 6. Similitud de temperatura
    if dish1.temperature == dish2.temperature:
        similarities['temperature'] = 1.0
    else:
        similarities['temperature'] = 0.5
    
    # 7. Similitud de dietas
    common_diets = set(dish1.diets or []) & set(dish2.diets or [])
    all_diets = set(dish1.diets or []) | set(dish2.diets or [])
    if all_diets:
        similarities['diets'] = len(common_diets) / len(all_diets)
    else:
        similarities['diets'] = 0.8  # Ambos sin restricciones específicas
    
    # 8. Similitud cultural - SOLO si se proporciona target_culture
    if target_culture and similarity_calc and dish2.ingredients:
        similarities['cultural'] = similarity_calc.get_cultural_score(dish2.ingredients, target_culture)
    else:
        # Si no se evalúa cultura, usar peso 0 para cultural
        similarities['cultural'] = 0.0
        weights_temp = DishSimilarityWeights(
            category=weights.category,
            price=weights.price,
            complexity=weights.complexity,
            flavors=weights.flavors,
            styles=weights.styles,
            temperature=weights.temperature,
            diets=weights.diets,
            cultural=0.0
        )
        weights_temp.normalize()
        weights = weights_temp
    
    # Calcular similitud total ponderada
    total_sim = (
        similarities['category'] * weights.category +
        similarities['price'] * weights.price +
        similarities['complexity'] * weights.complexity +
        similarities['flavors'] * weights.flavors +
        similarities['styles'] * weights.styles +
        similarities['temperature'] * weights.temperature +
        similarities['diets'] * weights.diets +
        similarities['cultural'] * weights.cultural
    )
    
    return total_sim


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
    
    Se utiliza para calcular similitudes culturales/gastronómicas
    basadas en descripciones textuales y embeddings semánticos.
    
    NOTA: Requiere instalación adicional de sentence-transformers.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el calculador semántico.
        
        Args:
            model_name: Nombre del modelo de embeddings a usar
        """
        self.model = None
        self.model_name = model_name
        self._cultural_embeddings_cache = {}  # Cache de embeddings culturales
        self._try_load_model()
        
        # Pre-computar embeddings de culturas si el modelo está disponible
        if self.is_available():
            self._precompute_cultural_embeddings()
    
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
    
    def _precompute_cultural_embeddings(self):
        """
        Pre-calcula y cachea los embeddings de todas las tradiciones culturales.
        Esto se ejecuta una sola vez al inicializar el calculador.
        """
        if not self.is_available():
            return
        
        # Calcular embeddings para todas las culturas
        for culture in CulturalTradition:
            description = self.get_cultural_description(culture)
            embedding = self.model.encode(description)
            self._cultural_embeddings_cache[culture] = embedding
    
    def get_cultural_description(self, culture: CulturalTradition) -> str:
        """
        Genera una descripción textual de una tradición cultural para embeddings.
        
        Args:
            culture: Tradición cultural
            
        Returns:
            Descripción textual enriquecida
        """
        # Descripciones detalladas de cada cultura gastronómica
        descriptions = {
    CulturalTradition.AMERICAN: "American cuisine is a melting pot of immigrant influences, featuring iconic dishes like juicy cheeseburgers, smoky barbecued ribs and brisket, crispy fried chicken with Southern sauces, and homemade apple pies. It includes comfort foods like creamy mac and cheese, and varied regional styles: Southern soul food with collard greens and cornbread, Tex-Mex with Mexican influences, New England clam chowder, and California fusion emphasizing fresh, organic, and healthy ingredients, reflecting the country's cultural diversity and gastronomic innovation.",
    CulturalTradition.CHINESE: "Chinese cuisine is vast and regional, with techniques like high-heat wok stir-frying to preserve textures and flavors, abundant use of soy sauce, steamed rice, hand-pulled noodles, dumplings filled with pork or vegetables steamed or fried, and seasonings like five-spice powder and numbing Sichuan pepper. It includes Cantonese dim sum, Peking duck, spicy Sichuan hot pot, and an emphasis on yin-yang balance, with influences from eight regional culinary traditions that celebrate freshness, harmony, and food as medicine.",
    CulturalTradition.FRENCH: "French cuisine, the cradle of haute cuisine, employs rich butter, heavy creams, and wine-based sauces like beurre blanc or bordelaise, refined techniques such as sous-vide and flambé, delicate pastries like croissants and éclairs, varied cheeses from creamy camembert to pungent roquefort, and regional specialties like Burgundy escargots, coq au vin, Marseille bouillabaisse, and foie gras. It emphasizes artistic presentation, terroir (the influence of soil and climate on ingredients), and dining as a refined social and cultural experience.",
    CulturalTradition.INDIAN: "Indian cuisine is a tapestry of vibrant spices like anti-inflammatory turmeric, toasted cumin, cardamom, and garam masala, with aromatic curries in tomato or coconut sauces, naan breads baked in tandoor ovens with garlic or cheese, perfumed basmati rice, nutritious lentil dals, and predominant vegetarian dishes like paneer tikka or aloo gobi. It includes regional influences: Southern thalis with crispy dosas and chutneys, Northern Mughal biryanis, and street food like spicy chaat, reflecting Ayurvedic principles of balance, religious diversity, and communal celebration through food.",
    CulturalTradition.ITALIAN: "Italian cuisine celebrates Mediterranean simplicity with fresh pasta like creamy spaghetti carbonara or tagliatelle al ragù, Neapolitan pizzas with thin crusts and fresh toppings, extra virgin olive oil, juicy San Marzano tomatoes, aromatic basil, grated parmesan cheese, and flavors like Milanese saffron risotto. It highlights regional diversity: Genovese pesto with pine nuts, Lombard ossobuco, Sicilian arancini, and antipasti like prosciutto and mozzarella, emphasizing seasonal ingredients, prolonged family meals, and the 'la dolce vita' concept at the table.",
    CulturalTradition.JAPANESE: "Japanese cuisine prioritizes freshness and minimalism, with sushi and sashimi of raw fish on vinegared rice, gohan rice as a base, fermented soy sauce, comforting miso soups, sake for pairing, and umami flavors from dashi and shiitake. It includes light fried tempura, rich broth ramen, seasonal multi-course kaiseki, and techniques like precise cutting with hocho knives. It reflects the wabi-sabi philosophy of beautiful imperfection, respect for nature, and rituals like matcha tea, making food an art form and mindfulness practice.",
    CulturalTradition.KOREAN: "Korean cuisine is bold and fermented, with spicy cabbage kimchi as a staple, red hot gochujang paste in mixed bibimbap, marinated bulgogi barbecue grilled meats, sticky rice, fermented foods like doenjang and ganjang for umami depth, spicy flavors balanced with sesame and garlic, and varied banchan side dishes like seasoned spinach or pickled radish. It includes jjigae hot pots, chewy tteokbokki street food, and communal meals emphasizing health through fermentation, Joseon dynasty history, and Buddhist influences in vegetarian dishes.",
    CulturalTradition.LEBANESE: "Lebanese cuisine is fresh and shared, with creamy tahini chickpea hummus, crispy spiced fava bean falafel, lemony parsley bulgur tabbouleh, fruity olive oil, warm pita bread for wrapping, mezze platters with smoky baba ghanoush and ground meat kibbeh, herbal za'atar roasted lamb, and Mediterranean-Arab fusion. It features sweets like pistachio and honey baklava, Bekaa Valley wines, and prolonged social meals reflecting hospitality, Ottoman and Phoenician influences, and emphasis on local, healthy ingredients.",
    CulturalTradition.MEXICAN: "Mexican cuisine is vibrant and pre-Hispanic, with corn tacos filled with carnitas or al pastor, varied chiles like jalapeño and habanero for heat, corn in tamales and pozole, refried beans, creamy avocado guacamole, fresh cilantro and acidic lime, complex mole sauces with chocolate and spices. It includes coastal ceviches, Swiss enchiladas, and street food like grilled elotes with mayo and cheese. It celebrates indigenous-Spanish fusion, festivals like Day of the Dead with pan de muerto, and UNESCO-recognized cultural heritage emphasizing community and bold flavors.",
    CulturalTradition.SPANISH: "Spanish cuisine is diverse and tapas-oriented, with small bites like spicy patatas bravas or garlic shrimp gambas al ajillo, Valencian paella with bomba rice, saffron, and seafood, Andalusian olive oil, cured ibérico ham, cold tomato gazpacho, and Mediterranean ingredients like olives and peppers. It includes churros with chocolate for breakfast, Madrid cocido stew, and regionals like Galician octopus or potato tortilla. It reflects Moorish and Roman influences, post-meal siesta, and bar-sharing culture, promoting socialization and denomination of origin products.",
    CulturalTradition.THAI: "Thai cuisine balances sweet, sour, salty, and spicy flavors, with pad thai stir-fried noodles with shrimp and peanuts, green or red curries in creamy coconut milk, aromatic lemongrass, umami nam pla fish sauce, fresh kaffir lime, fiery bird's eye chiles. It includes sour tom yum soup, sticky mango rice dessert, and grilled satay street food. Influenced by Asian neighbors and Portuguese, it emphasizes fresh herbs, family meals, and Buddhist harmony philosophy, making each dish a sensory explosion and therapeutic experience.",
    CulturalTradition.VIETNAMESE: "Vietnamese cuisine is light and herbal, with bone broth pho perfumed with star anise and cinnamon, fresh spring rolls wrapped in rice paper with herbs like mint and basil, salty nuoc mam fish sauce, rice noodles in bun cha with grilled pork, fresh ingredients like bean sprouts and lemongrass. It includes colonial French-influenced banh mi sandwiches, Hoi An cao lau, and condensed milk coffees. It reflects yin-yang balance, floating markets, and Chinese-French heritage, prioritizing freshness, contrasting textures, and meals as expressions of hospitality and health."
}
        
        return descriptions.get(culture, f"{culture.value} cuisine")
    
    def calculate_cultural_similarity(self, culture1: CulturalTradition, 
                                     culture2: CulturalTradition) -> float:
        """
        Calcula similitud semántica entre dos tradiciones culturales usando embeddings pre-calculados.
        
        Args:
            culture1: Primera tradición cultural
            culture2: Segunda tradición cultural
            
        Returns:
            Similitud entre 0 y 1
        """
        if not self.is_available():
            return 0.5  # Fallback neutro
        
        # Usar embeddings cacheados
        if culture1 not in self._cultural_embeddings_cache or culture2 not in self._cultural_embeddings_cache:
            # Fallback: calcular on-demand si no está en cache (no debería ocurrir si se pre-calcularon)
            return 0.5
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        emb1 = self._cultural_embeddings_cache[culture1]
        emb2 = self._cultural_embeddings_cache[culture2]
        
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        
        # Normalizar a [0, 1] (cosine similarity ya está en [-1, 1])
        return (similarity + 1) / 2
