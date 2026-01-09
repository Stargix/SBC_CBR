"""
Simulador CBR con Groq LLM para generar solicitudes aleatorias y evaluación con aprendizaje adaptativo.
"""

import os
import json
import random
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno desde .env
load_dotenv()

import sys
sys.path.append(str(Path(__file__).parent.parent))

from develop.main import ChefDigitalCBR, CBRConfig
from develop.core.models import (
    Request, EventType, Season, CulinaryStyle, Feedback, CulturalTradition
)
from develop.cycle.retain import FeedbackData


@dataclass
class GroqSimulationConfig:
    """Configuración de la simulación con Groq."""
    groq_api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    model_name: str = "llama-3.3-70b-versatile"
    num_interactions: int = 5
    enable_adaptive_weights: bool = True
    case_base_path: str = "cases.json"
    temperature: float = 0.9
    verbose: bool = True
    save_results: bool = True
    results_path: str = "data/groq_simulation_results.json"


@dataclass
class InteractionResult:
    """Resultado de una interacción individual."""
    request_num: int
    generated_request: Dict[str, Any]
    proposed_dishes: List[str]
    adaptations_made: List[str]
    user_feedback: Optional[Dict[str, Any]]
    llm_evaluation: str = ""
    llm_score: float = 0.0
    timestamp: str = ""


@dataclass
class GroqSimulationResult:
    """Resultado de una simulación completa."""
    config: GroqSimulationConfig
    interactions: List[InteractionResult]
    start_time: str
    end_time: str
    duration_seconds: float
    total_requests: int
    successful_proposals: int
    llm_evaluation: str
    llm_score: float  # Puntuación de 0.0 a 5.0
    summary: Dict[str, Any] = field(default_factory=dict)


class GroqCBRSimulator:
    """Simulador CBR que usa Groq para generar solicitudes aleatorias y evaluar resultados."""
    
    def __init__(self, config: Optional[GroqSimulationConfig] = None):
        self.config = config or GroqSimulationConfig()
        
        if not self.config.groq_api_key:
            raise ValueError("GROQ_API_KEY no encontrada. Configura la variable de entorno.")
        
        self.groq_client = Groq(api_key=self.config.groq_api_key)
        
        cbr_config = CBRConfig(
            case_base_path=self.config.case_base_path,
            verbose=self.config.verbose,
            enable_learning=self.config.enable_adaptive_weights
        )
        
        self.cbr_system = ChefDigitalCBR(cbr_config)
        self.interactions: List[InteractionResult] = []
    
    def _call_groq_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Realiza una llamada al LLM de Groq.
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            
        Returns:
            Respuesta del LLM
        """
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=2000
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"⚠️ Error en llamada a Groq: {e}")
            return ""
    
    def _generate_random_request(self) -> Dict[str, Any]:
        """
        Genera una solicitud aleatoria de forma programática (sin LLM).
        
        Más eficiente que usar LLM - evita llamadas innecesarias a la API.
        
        Returns:
            Diccionario con los datos de la solicitud
        """
        event_types = ["WEDDING", "FAMILIAR", "CONGRESS", "CORPORATE", "CHRISTENING", "COMMUNION"]
        dietary = ["vegan", "vegetarian", "gluten-free", "lactose-free", "kosher", "pork-free"]
        seasons = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]
        styles = ["CLASSIC", "MODERN", "FUSION", "REGIONAL", "SIBARITA", "GOURMET"]
        cultures = ["AMERICAN", "CHINESE", "FRENCH", "INDIAN", "ITALIAN", "JAPANESE", "MEXICAN", "SPANISH", "KOREAN", "VIETNAMESE", "LEBANESE"]
        ingredients = ["shellfish", "nuts", "dairy", "eggs", "fish"]
        
        price_min = random.randint(15, 40)
        price_max = price_min + random.randint(10, 40)
        
        return {
            "event_type": random.choice(event_types),
            "num_guests": random.randint(2, 50),
            "season": random.choice(seasons),
            "price_min": price_min,
            "price_max": price_max,
            "wants_wine": random.choice([True, False]),
            "required_diets": random.sample(dietary, k=random.randint(0, 2)),
            "restricted_ingredients": random.sample(ingredients, k=random.randint(0, 2)),
            "preferred_style": random.choice(styles) if random.random() > 0.5 else None,
            "cultural_preference": random.choice(cultures) if random.random() > 0.5 else None
        }
    

    
    def _create_request_object(self, request_data: Dict[str, Any]) -> Request:
        """Convierte los datos de solicitud en un objeto Request."""
        # Parse event_type
        try:
            event_type = EventType[request_data.get("event_type", "FAMILIAR").upper()]
        except KeyError:
            event_type = EventType.FAMILIAR
        
        # Parse season
        try:
            season = Season[request_data.get("season", "SPRING").upper()]
        except KeyError:
            season = Season.SPRING
        
        # Parse preferred_style (opcional)
        preferred_style = None
        if "preferred_style" in request_data and request_data["preferred_style"]:
            try:
                preferred_style = CulinaryStyle[request_data["preferred_style"].upper()]
            except KeyError:
                pass
        
        # Parse cultural_preference (opcional)
        cultural_preference = None
        if "cultural_preference" in request_data and request_data["cultural_preference"]:
            try:
                cultural_preference = CulturalTradition[request_data["cultural_preference"].upper()]
            except KeyError:
                pass
        
        # Parse dietary restrictions
        required_diets = request_data.get("required_diets", [])
        if isinstance(required_diets, str):
            required_diets = [required_diets]
        
        # Parse restricted ingredients
        restricted_ingredients = request_data.get("restricted_ingredients", [])
        if isinstance(restricted_ingredients, str):
            restricted_ingredients = [restricted_ingredients]
        
        return Request(
            event_type=event_type,
            season=season,
            num_guests=int(request_data.get("num_guests", 4)),
            price_min=float(request_data.get("price_min", 20.0)),
            price_max=float(request_data.get("price_max", 50.0)),
            wants_wine=bool(request_data.get("wants_wine", False)),
            preferred_style=preferred_style,
            cultural_preference=cultural_preference,
            required_diets=required_diets,
            restricted_ingredients=restricted_ingredients
        )
    
    def _process_request(self, request_num: int, request_data: Dict[str, Any]) -> InteractionResult:
        """
        Procesa una solicitud a través del sistema CBR.
        
        Args:
            request_num: Número de la solicitud
            request_data: Datos de la solicitud generada
            
        Returns:
            Resultado de la interacción
        """
        if self.config.verbose:
            print(f"\n{'='*70}")
            print(f"SOLICITUD #{request_num}")
            print('='*70)
            print(json.dumps(request_data, indent=2, ensure_ascii=False))
        
        request = self._create_request_object(request_data)
        
        # Ejecutar ciclo CBR
        result = self.cbr_system.process_request(request)
        
        proposed_dishes = []
        adaptations_made = []
        menus_details = []
        
        if result and hasattr(result, 'proposed_menus') and result.proposed_menus:
            for proposal in result.proposed_menus[:3]:  # Top 3 propuestas
                if hasattr(proposal, 'menu'):
                    menu = proposal.menu
                    proposed_dishes.extend([
                        menu.starter.name,
                        menu.main_course.name,
                        menu.dessert.name
                    ])
                    
                    # Recopilar detalles del menú
                    menu_detail = {
                        "starter": {
                            "name": menu.starter.name,
                            "ingredients": menu.starter.ingredients[:10],
                            "price": menu.starter.price,
                            "calories": menu.starter.calories
                        },
                        "main_course": {
                            "name": menu.main_course.name,
                            "ingredients": menu.main_course.ingredients[:10],
                            "price": menu.main_course.price,
                            "calories": menu.main_course.calories
                        },
                        "dessert": {
                            "name": menu.dessert.name,
                            "ingredients": menu.dessert.ingredients[:10],
                            "price": menu.dessert.price,
                            "calories": menu.dessert.calories
                        },
                        "beverage": {
                            "name": menu.beverage.name,
                            "price": menu.beverage.price,
                            "alcoholic": menu.beverage.alcoholic
                        },
                        "total_price": menu.total_price,
                        "total_calories": menu.total_calories,
                        "similarity_score": proposal.similarity_score if hasattr(proposal, 'similarity_score') else 0.0
                    }
                    
                    # Validación del chef
                    if hasattr(proposal, 'validation_result'):
                        validation = proposal.validation_result
                        menu_detail["validation"] = {
                            "passed": validation.is_valid() if hasattr(validation, 'is_valid') else True,
                            "issues": [str(issue) for issue in validation.issues] if hasattr(validation, 'issues') else [],
                            "warnings": [str(warn) for warn in validation.warnings] if hasattr(validation, 'warnings') else []
                        }
                    
                    menus_details.append(menu_detail)
                
                if hasattr(proposal, 'adaptations'):
                    adaptations_made.extend(proposal.adaptations)
        
        if self.config.verbose:
            print(f"\n✅ Platos propuestos: {', '.join(proposed_dishes[:3]) if proposed_dishes else 'Ninguno'}")
            if menus_details:
                print(f"💰 Precio total: ${menus_details[0]['total_price']:.2f}")
        
        # Evaluar con LLM
        llm_eval = {"evaluation_text": "", "score": 0.0, "price_score": 0.0, "cultural_score": 0.0, "flavor_score": 0.0}
        if menus_details:
            if self.config.verbose:
                print(f"\n🤖 Evaluando con LLM...")
            # Pasar también las adaptaciones al LLM para que sepa qué cambios se hicieron
            llm_eval = self._evaluate_single_request(request_data, menus_details, adaptations_made)
            if self.config.verbose:
                print(f"⭐ Puntuación: {llm_eval['score']:.1f}/5.0")
        
        # APRENDIZAJE: Usar las puntuaciones del LLM para actualizar pesos adaptativos
        if self.config.enable_adaptive_weights and menus_details:
            self._apply_learning_from_score(
                request, 
                llm_eval['score'],
                llm_eval.get('price_score', llm_eval['score']),
                llm_eval.get('cultural_score', llm_eval['score']),
                llm_eval.get('flavor_score', llm_eval['score'])
            )
        
        return InteractionResult(
            request_num=request_num,
            generated_request=request_data,
            proposed_dishes=proposed_dishes,
            adaptations_made=adaptations_made,
            user_feedback={"menus_details": menus_details},
            llm_evaluation=llm_eval["evaluation_text"],
            llm_score=llm_eval["score"],
            timestamp=datetime.now().isoformat()
        )
    
    def _evaluate_simulation_with_llm(self, interactions: List[InteractionResult]) -> Dict[str, Any]:
        """
        Resume las evaluaciones individuales de la simulación.
        
        Args:
            interactions: Lista de interacciones realizadas
            
        Returns:
            Diccionario con resumen y puntuación promedio
        """
        # Calcular puntuación promedio de las evaluaciones individuales
        scores = [i.llm_score for i in interactions if i.llm_score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Crear resumen de las evaluaciones
        summary_lines = ["RESUMEN DE EVALUACIONES INDIVIDUALES:", "="*50]
        
        for interaction in interactions:
            summary_lines.append(f"\nSolicitud #{interaction.request_num}:")
            summary_lines.append(f"  Evento: {interaction.generated_request.get('event_type')}")
            summary_lines.append(f"  Puntuación: {interaction.llm_score:.1f}/5.0")
            # Primera línea de la evaluación
            eval_preview = interaction.llm_evaluation.split('\n')[0][:100] if interaction.llm_evaluation else "Sin evaluación"
            summary_lines.append(f"  Comentario: {eval_preview}...")
        
        summary_lines.append(f"\n{'='*50}")
        summary_lines.append(f"PUNTUACIÓN PROMEDIO: {avg_score:.2f}/5.00")
        
        evaluation_text = "\n".join(summary_lines)
        
        return {
            "evaluation_text": evaluation_text,
            "score": avg_score
        }
    
    def _evaluate_single_request(self, request_data: Dict[str, Any], menus_details: List[Dict[str, Any]], adaptations: List[str] = None) -> Dict[str, Any]:
        """
        Usa Groq LLM para evaluar una única solicitud con dimensiones separadas.
        
        Args:
            request_data: Datos de la solicitud
            menus_details: Detalles de los menús propuestos
            adaptations: Lista de adaptaciones realizadas por el sistema CBR
            
        Returns:
            Diccionario con evaluación y puntuaciones (overall + dimensiones)
        """
        system_prompt = """Eres un chef experto y crítico gastronómico. Evalúa la calidad del menú propuesto 
basándote en la coherencia de ingredientes, el precio, la adecuación cultural y el sabor.

Debe evaluar SEPARADAMENTE cada una de estas dimensiones:
1. PRECIO: ¿El precio es apropiado y está dentro del presupuesto?
2. CULTURA: ¿El menú respeta las preferencias culturales solicitadas?
3. SABOR: ¿Los sabores y combinaciones de ingredientes son coherentes y apropiados?"""

        # Preparar información simplificada
        menu_info = []
        for i, menu in enumerate(menus_details, 1):
            info = {
                "menu_num": i,
                "entrante": {
                    "nombre": menu["starter"]["name"],
                    "ingredientes": menu["starter"]["ingredients"],
                    "precio": f"{menu['starter']['price']}€"
                },
                "principal": {
                    "nombre": menu["main_course"]["name"],
                    "ingredientes": menu["main_course"]["ingredients"],
                    "precio": f"{menu['main_course']['price']}€"
                },
                "postre": {
                    "nombre": menu["dessert"]["name"],
                    "ingredientes": menu["dessert"]["ingredients"],
                    "precio": f"{menu['dessert']['price']}€"
                },
                "bebida": {
                    "nombre": menu["beverage"]["name"],
                    "precio": f"{menu['beverage']['price']}€"
                },
                "precio_total": f"{menu['total_price']}€",
                "validacion_chef": menu.get("validation", {})
            }
            menu_info.append(info)

        # Determinar si hay preferencia cultural
        cultural_pref = request_data.get('cultural_preference', 'No especificado')
        has_cultural_pref = cultural_pref and cultural_pref != 'No especificado'
        
        # Preparar información de adaptaciones si está disponible
        adaptations_text = ""
        if adaptations and len(adaptations) > 0:
            adaptations_text = "\n\nADAPTACIONES REALIZADAS POR EL SISTEMA CBR:\n"
            for i, adaptation in enumerate(adaptations[:5], 1):  # Máximo 5 para no sobrecargar
                adaptations_text += f"{i}. {adaptation}\n"
            adaptations_text += "\nEstas adaptaciones se hicieron para ajustar el menú a los requisitos."
        
        user_prompt = f"""Evalúa el siguiente menú para este evento:

SOLICITUD:
- Evento: {request_data.get('event_type')}
- Invitados: {request_data.get('num_guests')}
- Temporada: {request_data.get('season')}
- Presupuesto: {request_data.get('price_min')}-{request_data.get('price_max')}€
- Dietas requeridas: {', '.join(request_data.get('required_diets', [])) or 'Ninguna'}
- Estilo: {request_data.get('preferred_style', 'No especificado')}
- Preferencia cultural: {cultural_pref}

MENÚ PROPUESTO:
{json.dumps(menu_info[0] if menu_info else {}, indent=2, ensure_ascii=False)}
{adaptations_text}

CONTEXTO IMPORTANTE:
El sistema CBR parte de una base de casos existente y hace adaptaciones automáticas 
(sustituciones de ingredientes) para acercarse a los requisitos culturales. Si la 
cultura solicitada no está bien representada en la base de datos, el sistema hace 
su mejor esfuerzo adaptando ingredientes de platos similares.

Evalúa CADA DIMENSIÓN POR SEPARADO (escala 0.0-5.0):

1. PRECIO: ¿Está dentro del presupuesto {request_data.get('price_min')}-{request_data.get('price_max')}€? ¿Es apropiado para el evento?

2. CULTURA: {f'¿El menú respeta o se aproxima a la tradición {cultural_pref}?' if has_cultural_pref else '¿Los ingredientes son apropiados culturalmente para el evento?'}
   - Si hay adaptaciones culturales listadas arriba, valora el esfuerzo de aproximación
   - 5.0 = Auténtico y fiel a la tradición
   - 3.0-4.0 = Intento razonable de aproximación con ingredientes adaptados
   - 1.0-2.0 = No hay esfuerzo o adaptaciones incorrectas
   
3. SABOR: ¿Los sabores y combinaciones de ingredientes son coherentes? ¿Los platos se complementan bien?

4. DIETAS: ¿Se cumplen las restricciones dietéticas requeridas?

Da una evaluación breve (2-3 líneas) y termina con:
PRECIO: X.X
CULTURA: X.X
SABOR: X.X
GENERAL: X.X

Donde X.X es un número entre 0.0 y 5.0 para cada dimensión."""

        evaluation_text = self._call_groq_llm(system_prompt, user_prompt)
        scores = self._extract_dimension_scores_from_evaluation(evaluation_text)
        
        return {
            "evaluation_text": evaluation_text,
            "score": scores.get('overall', scores.get('general', 2.5)),
            "price_score": scores.get('price', scores.get('precio', 2.5)),
            "cultural_score": scores.get('cultural', scores.get('cultura', 2.5)),
            "flavor_score": scores.get('flavor', scores.get('sabor', 2.5))
        }
    
    def _apply_learning_from_score(self, request: Request, overall_score: float, 
                                    price_score: float, cultural_score: float, flavor_score: float):
        """
        Aplica aprendizaje adaptativo basado en las puntuaciones del LLM por dimensión.
        
        Convierte las puntuaciones 0-5 en feedback estructurado y actualiza pesos.
        
        Args:
            request: Solicitud procesada
            overall_score: Puntuación general del LLM (0.0 - 5.0)
            price_score: Puntuación de satisfacción con el precio (0.0 - 5.0)
            cultural_score: Puntuación de satisfacción cultural (0.0 - 5.0)
            flavor_score: Puntuación de satisfacción con el sabor (0.0 - 5.0)
        """
        # Crear FeedbackData con dimensiones separadas para el aprendizaje
        feedback_data = FeedbackData(
            menu_id="simulation_" + str(datetime.now().timestamp()),
            success=overall_score >= 3.5,
            score=overall_score,
            comments=f"Evaluación automática LLM: {overall_score:.1f}/5.0 (Precio: {price_score:.1f}, Cultura: {cultural_score:.1f}, Sabor: {flavor_score:.1f})",
            would_recommend=overall_score >= 4.0,
            price_satisfaction=price_score,
            cultural_satisfaction=cultural_score,
            flavor_satisfaction=flavor_score
        )
        
        # Aplicar aprendizaje con FeedbackData
        self.cbr_system.learn_from_feedback(feedback_data, request)
        
        if self.config.verbose:
            print(f"📊 Pesos adaptativos actualizados (overall: {overall_score:.1f}, precio: {price_score:.1f}, cultura: {cultural_score:.1f}, sabor: {flavor_score:.1f})")
    
    def _extract_dimension_scores_from_evaluation(self, evaluation_text: str) -> Dict[str, float]:
        """
        Extrae las puntuaciones de cada dimensión de la evaluación del LLM.
        
        Args:
            evaluation_text: Texto de evaluación del LLM
            
        Returns:
            Diccionario con scores por dimensión: 'price', 'cultural', 'flavor', 'overall'
        """
        import re
        
        scores = {}
        
        # Patrones para cada dimensión (soporta español e inglés)
        patterns = {
            'price': r'(?:PRECIO|PRICE):\s*(\d+\.?\d*)',
            'cultural': r'(?:CULTURA|CULTURAL):\s*(\d+\.?\d*)',
            'flavor': r'(?:SABOR|FLAVOR):\s*(\d+\.?\d*)',
            'overall': r'(?:GENERAL|OVERALL|PUNTUACIÓN):\s*(\d+\.?\d*)'
        }
        
        # Extraer cada dimensión
        for dimension, pattern in patterns.items():
            match = re.search(pattern, evaluation_text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    scores[dimension] = max(0.0, min(5.0, score))
                except ValueError:
                    pass
        
        # Si no se encontró puntuación overall, calcular promedio
        if 'overall' not in scores and len(scores) > 0:
            scores['overall'] = sum(scores.values()) / len(scores)
        
        # Si no se extrajo ninguna puntuación, usar fallback del método antiguo
        if not scores:
            fallback_score = self._extract_score_from_evaluation(evaluation_text)
            scores = {
                'overall': fallback_score,
                'price': fallback_score,
                'cultural': fallback_score,
                'flavor': fallback_score
            }
        
        # Si falta alguna dimensión, usar el overall o 2.5
        default_score = scores.get('overall', 2.5)
        for dimension in ['price', 'cultural', 'flavor']:
            if dimension not in scores:
                scores[dimension] = default_score
        
        if self.config.verbose and len([k for k in scores if k != 'overall']) > 1:
            print(f"   📊 Scores por dimensión: Precio={scores['price']:.1f}, Cultura={scores['cultural']:.1f}, Sabor={scores['flavor']:.1f}")
        
        return scores
    
    def _extract_score_from_evaluation(self, evaluation_text: str) -> float:
        """
        Extrae la puntuación numérica de la evaluación del LLM.
        
        Args:
            evaluation_text: Texto de evaluación
            
        Returns:
            Puntuación de 0.0 a 5.0
        """
        import re
        
        # Buscar patrón "PUNTUACIÓN: X.X"
        pattern = r'PUNTUACIÓN:\s*(\d+\.?\d*)'
        match = re.search(pattern, evaluation_text, re.IGNORECASE)
        
        if match:
            try:
                score = float(match.group(1))
                # Asegurar que esté en rango 0-5
                return max(0.0, min(5.0, score))
            except ValueError:
                pass
        
        # Fallback: intentar encontrar cualquier número seguido de "/5"
        pattern2 = r'(\d+\.?\d*)\s*/\s*5'
        match2 = re.search(pattern2, evaluation_text)
        if match2:
            try:
                score = float(match2.group(1))
                return max(0.0, min(5.0, score))
            except ValueError:
                pass
        
        # Si no se encuentra puntuación, retornar 2.5 (neutral)
        if self.config.verbose:
            print("⚠️ No se pudo extraer puntuación del LLM, usando 2.5 por defecto")
        return 2.5
    
    def run_simulation(self) -> GroqSimulationResult:
        """
        Ejecuta la simulación completa.
        
        Returns:
            Resultado de la simulación
        """
        start_time = datetime.now()
        
        if self.config.verbose:
            print(f"\n{'='*70}")
            print("GROQ CBR SIMULATOR")
            print('='*70)
            print(f"Modelo: {self.config.model_name}")
            print(f"Interacciones: {self.config.num_interactions}")
            print(f"Adaptive Weights: {self.config.enable_adaptive_weights}")
            print('='*70)
        
        # Ejecutar interacciones
        for i in range(1, self.config.num_interactions + 1):
            try:
                # Generar solicitud aleatoria con LLM
                request_data = self._generate_random_request()
                
                # Procesar a través del CBR
                interaction_result = self._process_request(i, request_data)
                self.interactions.append(interaction_result)
                
                # Pausa breve entre interacciones
                time.sleep(0.5)
                
            except Exception as e:
                if self.config.verbose:
                    print(f"⚠️ Error en interacción {i}: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Evaluación final con LLM
        if self.config.verbose:
            print(f"\n{'='*70}")
            print("EVALUACIÓN FINAL CON LLM")
            print('='*70)
        
        llm_evaluation_result = self._evaluate_simulation_with_llm(self.interactions)
        llm_evaluation = llm_evaluation_result["evaluation_text"]
        llm_score = llm_evaluation_result["score"]
        
        if self.config.verbose:
            print(f"\n{llm_evaluation}")
            print(f"\n⭐ PUNTUACIÓN FINAL: {llm_score:.1f}/5.0")
        
        # Preparar resultado
        successful = sum(1 for i in self.interactions if i.proposed_dishes)
        
        result = GroqSimulationResult(
            config=self.config,
            interactions=self.interactions,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            total_requests=len(self.interactions),
            successful_proposals=successful,
            llm_evaluation=llm_evaluation,
            llm_score=llm_score,
            summary={
                "avg_dishes_per_request": sum(len(i.proposed_dishes) for i in self.interactions) / len(self.interactions) if self.interactions else 0,
                "avg_adaptations_per_request": sum(len(i.adaptations_made) for i in self.interactions) / len(self.interactions) if self.interactions else 0,
                "success_rate": (successful / len(self.interactions) * 100) if self.interactions else 0
            }
        )
        
        # Guardar resultados
        if self.config.save_results:
            self._save_results(result)
            
            # Guardar historial de aprendizaje si está habilitado
            if self.config.enable_adaptive_weights:
                learning_path = self.config.results_path.replace('.json', '_learning.json')
                self.cbr_system.save_learning_data(learning_path)
        
        if self.config.verbose:
            print(f"\n{'='*70}")
            print("RESUMEN DE SIMULACIÓN")
            print('='*70)
            print(f"Duración: {duration:.2f}s")
            print(f"Solicitudes procesadas: {result.total_requests}")
            print(f"Propuestas exitosas: {result.successful_proposals}")
            print(f"Tasa de éxito: {result.summary['success_rate']:.1f}%")
            print(f"⭐ Puntuación promedio LLM: {result.llm_score:.2f}/5.00")
            
            # Mostrar evolución de pesos si está habilitado
            if self.config.enable_adaptive_weights:
                print(f"\n📈 EVOLUCIÓN DE PESOS ADAPTATIVOS:")
                learning_summary = self.cbr_system.weight_learner.get_learning_summary()
                if learning_summary.get('most_changed'):
                    for item in learning_summary['most_changed'][:3]:
                        print(f"   {item['weight']}: {item['change_pct']}")
            print('='*70)
        
        return result
    
    def _save_results(self, result: GroqSimulationResult):
        """Guarda los resultados en un archivo JSON."""
        try:
            output_path = Path(self.config.results_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir a diccionario serializable
            result_dict = {
                "config": {
                    "model_name": result.config.model_name,
                    "num_interactions": result.config.num_interactions,
                    "enable_adaptive_weights": result.config.enable_adaptive_weights,
                    "temperature": result.config.temperature
                },
                "interactions": [
                    {
                        "request_num": i.request_num,
                        "generated_request": i.generated_request,
                        "proposed_dishes": i.proposed_dishes,
                        "adaptations_made": i.adaptations_made,
                        "menus_details": i.user_feedback.get("menus_details", []) if i.user_feedback else [],
                        "llm_evaluation": i.llm_evaluation,
                        "llm_score": i.llm_score,
                        "timestamp": i.timestamp
                    }
                    for i in result.interactions
                ],
                "start_time": result.start_time,
                "end_time": result.end_time,
                "duration_seconds": result.duration_seconds,
                "total_requests": result.total_requests,
                "successful_proposals": result.successful_proposals,
                "llm_evaluation": result.llm_evaluation,
                "llm_score": result.llm_score,
                "summary": result.summary
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            if self.config.verbose:
                print(f"\n💾 Resultados guardados en: {output_path}")
                
        except Exception as e:
            if self.config.verbose:
                print(f"⚠️ Error guardando resultados: {e}")


def main():
    """Función principal para ejecutar el simulador."""
    # Verificar que existe la API key
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠️ ERROR: GROQ_API_KEY no encontrada.")
        print("Configura la variable de entorno:")
        print("export GROQ_API_KEY='tu_api_key_aqui'")
        return
    
    # Crear y ejecutar simulador
    config = GroqSimulationConfig(
        num_interactions=5,
        enable_adaptive_weights=True,
        verbose=True,
        temperature=0.9
    )
    
    simulator = GroqCBRSimulator(config)
    result = simulator.run_simulation()
    
    print("\n✅ Simulación completada exitosamente!")


if __name__ == "__main__":
    main()
