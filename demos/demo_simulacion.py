#!/usr/bin/env python3
"""
Simulación de usuarios sintéticos usando el sistema CBR.

Este script simula múltiples usuarios haciendo peticiones diversas,
dando feedback, y muestra cómo el sistema aprende y mejora con el tiempo.

Usa los casos reales de initial_cases.json para generar solicitudes realistas.
"""

import sys
from pathlib import Path
import time
import random
import json
from typing import List, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from develop import (
    ChefDigitalCBR, CBRConfig,
    Request, EventType, Season, CulinaryStyle, CulturalTradition,
    FeedbackData
)


@dataclass
class UsuarioSintetico:
    """Representa un usuario sintético con preferencias basado en casos reales."""
    nombre: str
    caso_real: dict  # Datos del caso real de initial_cases.json
    exigente: float = 0.5  # 0.0 = permisivo, 1.0 = muy exigente
    
    def generar_solicitud(self) -> Request:
        """Genera una solicitud basada en los datos reales del caso."""
        # Usar los datos del caso real con pequeñas variaciones
        event = EventType(self.caso_real["event"])
        season = Season(self.caso_real["season"])
        
        # Aplicar pequeña variación al presupuesto (±5%)
        presupuesto_base = (self.caso_real["price_min"] + self.caso_real["price_max"]) / 2
        variacion = presupuesto_base * 0.05 * random.uniform(-1, 1)
        precio_solicitado = presupuesto_base + variacion
        
        # Pequeña variación en comensales (±10%)
        comensales_base = self.caso_real["num_guests"]
        variacion_comensales = int(comensales_base * 0.10 * random.uniform(-1, 1))
        comensales = max(5, comensales_base + variacion_comensales)
        
        return Request(
            event_type=event,
            num_guests=comensales,
            price_max=precio_solicitado,
            season=season,
            preferred_style=CulinaryStyle(self.caso_real["style"]) if self.caso_real.get("style") else None,
            cultural_preference=CulturalTradition(self.caso_real["culture"]) if self.caso_real.get("culture") else None,
            required_diets=self.caso_real.get("required_diets", []),
            restricted_ingredients=self.caso_real.get("restricted_ingredients", []),
            wants_wine=random.choice([True, False])
        )
    
    def evaluar_menu(self, menu, precio_solicitado: float, 
                    restricciones_dieteticas: List[str] = None,
                    ingredientes_restringidos: List[str] = None) -> FeedbackData:
        """Simula la evaluación del menú por parte del usuario de forma objetiva."""
        score = 5.0
        comentarios = []
        
        # Evaluar precio (crítico)
        diff_precio = abs(menu.total_price - precio_solicitado)
        porcentaje_diferencia = diff_precio / precio_solicitado if precio_solicitado > 0 else 0
        
        if porcentaje_diferencia > 0.25:  # Más de 25% de diferencia
            score -= 1.5
            comentarios.append(f"precio fuera de rango (+{porcentaje_diferencia*100:.0f}%)")
        elif porcentaje_diferencia > 0.15:  # 15-25%
            score -= 0.8
            comentarios.append(f"precio superior (+{porcentaje_diferencia*100:.0f}%)")
        elif porcentaje_diferencia > 0.05:  # 5-15%
            score -= 0.3
        
        # Evaluar estilo
        estilo_esperado = CulinaryStyle(self.caso_real["style"]) if self.caso_real.get("style") else None
        if estilo_esperado and menu.dominant_style != estilo_esperado:
            score -= 0.6
            comentarios.append(f"estilo {menu.dominant_style.value} en lugar de {estilo_esperado.value}")
        
        # Evaluar cultura
        cultura_esperada = CulturalTradition(self.caso_real["culture"]) if self.caso_real.get("culture") else None
        if cultura_esperada and menu.cultural_theme != cultura_esperada:
            score -= 0.5
            comentarios.append(f"cultura no coincide")
        
        # Evaluar restricciones dietéticas (muy importante)
        if restricciones_dieteticas:
            # Aquí se debería verificar si el menú respeta las restricciones
            # Por ahora, si hay restricciones y el menú no las respeta, bajamos puntuación
            score -= 0.3  # Pequeña penalización por incertidumbre
            comentarios.append(f"restricciones dietéticas: {', '.join(restricciones_dieteticas)}")
        
        # Evaluar ingredientes restringidos (muy importante)
        if ingredientes_restringidos:
            score -= 0.3  # Pequeña penalización por incertidumbre
            comentarios.append(f"ingredientes restringidos: {', '.join(ingredientes_restringidos)}")
        
        # Variabilidad aleatoria según exigencia del usuario (menor en usuarios exigentes)
        variacion = random.gauss(0, max(0.1, 0.3 * (1 - self.exigente)))
        score += variacion
        
        # Limitar entre 1 y 5
        score = max(1.0, min(5.0, score))
        
        # Determinar éxito de forma objetiva
        success = score >= 3.5
        
        # Generar comentario
        if score >= 4.5:
            comentario_base = "Excelente menú, muy satisfecho"
        elif score >= 4.0:
            comentario_base = "Muy buen menú"
        elif score >= 3.5:
            comentario_base = "Buen menú, aceptable"
        elif score >= 3.0:
            comentario_base = "Menú correcto pero mejorable"
        else:
            comentario_base = "Menú insatisfactorio"
        
        if comentarios:
            comentario_final = f"{comentario_base}. Problemas: {', '.join(comentarios)}"
        else:
            comentario_final = comentario_base
        
        return FeedbackData(
            menu_id=menu.id,
            success=success,
            score=score,
            comments=comentario_final,
            would_recommend=score >= 4.0
        )


# Cargar casos reales desde initial_cases.json
def cargar_casos_reales() -> List[UsuarioSintetico]:
    """Carga los casos reales de initial_cases.json y crea usuarios sintéticos."""
    config_path = Path(__file__).parent.parent / "develop" / "config" / "initial_cases.json"
    
    usuarios = []
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, caso in enumerate(data.get("cases", [])[:20]):  # Limitar a 20 casos para la simulación
            # Crear nombre descriptivo basado en el evento
            evento = caso.get("event", "event")
            numero = i + 1
            
            # Variar el nivel de exigencia según la cultura/evento
            exigencia_base = {
                "wedding": 0.9,
                "congress": 0.7,
                "corporate": 0.7,
                "birthday": 0.5,
                "anniversary": 0.8,
                "communion": 0.6,
                "christening": 0.5,
                "familiar": 0.3,
            }.get(evento, 0.5)
            
            # Pequeña variación aleatoria
            exigencia = max(0.1, min(0.9, exigencia_base + random.uniform(-0.15, 0.15)))
            
            nombre = f"{evento.capitalize()} #{numero}"
            usuarios.append(UsuarioSintetico(
                nombre=nombre,
                caso_real=caso,
                exigente=exigencia
            ))
        
        print(f"✅ Cargados {len(usuarios)} casos reales de initial_cases.json\n")
        return usuarios
    
    except FileNotFoundError:
        print(f"⚠️  No se encontró initial_cases.json en {config_path}")
        print("Usando usuarios sintéticos por defecto...\n")
        return []


# Base de usuarios sintéticos (fallback si no se cargan casos reales)
USUARIOS_SINTETICOS_FALLBACK = []


def limpiar_pantalla():
    """Limpia la pantalla del terminal."""
    print("\033[2J\033[H", end="")


def mostrar_barra_progreso(iteracion: int, total: int, casos: int, 
                          feedback_avg: float, tasa_exito: float):
    """Muestra una barra de progreso animada."""
    porcentaje = (iteracion / total) * 100
    barra_len = 50
    filled = int(barra_len * iteracion / total)
    barra = "█" * filled + "░" * (barra_len - filled)
    
    print(f"\n{'=' * 70}")
    print(f"Progreso: [{barra}] {porcentaje:.0f}%")
    print(f"Iteración: {iteracion}/{total}")
    print(f"Casos en base: {casos}")
    print(f"Feedback promedio: {feedback_avg:.2f}/5 {'⭐' * int(feedback_avg)}")
    print(f"Tasa de éxito: {tasa_exito:.0%} {'✅' if tasa_exito > 0.8 else '⚠️'}")
    print(f"{'=' * 70}")


def visualizar_distribucion_casos(stats: dict):
    """Visualiza la distribución de casos por evento."""
    print("\n📊 Distribución de casos por evento:")
    
    if 'cases_by_event' not in stats:
        return
    
    casos_por_evento = stats['cases_by_event']
    max_casos = max(casos_por_evento.values()) if casos_por_evento else 1
    
    for evento, cantidad in casos_por_evento.items():
        barra_len = int((cantidad / max_casos) * 30)
        barra = "█" * barra_len
        print(f"  {evento:12s} [{cantidad:2d}] {barra}")


def visualizar_evolucion(historia: List[dict]):
    """Muestra la evolución del sistema a lo largo del tiempo."""
    print("\n📈 EVOLUCIÓN DEL SISTEMA")
    print("=" * 70)
    
    # Gráfico ASCII de feedback promedio
    print("\n💯 Feedback Promedio (escala 1-5):")
    for i, estado in enumerate(historia):
        iteracion = estado['iteracion']
        feedback = estado['feedback_avg']
        casos = estado['total_casos']
        
        # Escala de 1 a 5
        barra_len = int((feedback - 1) / 4 * 40)
        barra = "█" * barra_len
        
        print(f"  {iteracion:3d}: {barra} {feedback:.2f} ({casos} casos)")
    
    # Gráfico de total de casos
    print("\n📚 Total de Casos en la Base:")
    max_casos = max(e['total_casos'] for e in historia)
    for i, estado in enumerate(historia):
        iteracion = estado['iteracion']
        casos = estado['total_casos']
        
        barra_len = int((casos / max_casos) * 40) if max_casos > 0 else 0
        barra = "█" * barra_len
        
        marcador = ""
        if i > 0 and casos > historia[i-1]['total_casos']:
            marcador = " 🆕"
        elif i > 0 and casos < historia[i-1]['total_casos']:
            marcador = " 🗑️"
        
        print(f"  {iteracion:3d}: {barra} {casos}{marcador}")


def simular_usuarios(num_iteraciones: int = 30, velocidad: float = 0.5):
    """
    Simula múltiples usuarios usando el sistema.
    
    Usa casos reales de initial_cases.json para generar solicitudes realistas.
    
    Args:
        num_iteraciones: Número de iteraciones a simular
        velocidad: Tiempo de espera entre iteraciones (segundos)
    """
    print("=" * 70)
    print("🎭 SIMULACIÓN DE USUARIOS CON CASOS REALES")
    print("=" * 70)
    
    # Cargar casos reales
    usuarios = cargar_casos_reales()
    
    if not usuarios:
        print("❌ No se pudieron cargar los casos reales. Abortando.\n")
        return
    
    print(f"Simulando {num_iteraciones} peticiones con {len(usuarios)} usuarios reales...")
    print("Presiona Ctrl+C para detener la simulación\n")
    time.sleep(2)
    
    # Inicializar sistema
    config = CBRConfig(verbose=False, enable_learning=True)
    cbr = ChefDigitalCBR(config)
    
    # Historia para visualización
    historia = []
    
    try:
        for i in range(1, num_iteraciones + 1):
            # Seleccionar usuario aleatorio de los casos reales
            usuario = random.choice(usuarios)
            
            # Generar solicitud basada en caso real
            request = usuario.generar_solicitud()
            
            # Procesar con el sistema CBR
            result = cbr.process_request(request)
            
            # Simular evaluación del usuario
            if result.proposed_menus:
                # Usuario elige el primer menú (más similar)
                menu_elegido = result.proposed_menus[0].menu
                
                # Evaluar considerando restricciones reales del caso
                feedback = usuario.evaluar_menu(
                    menu_elegido, 
                    request.price_max,
                    restricciones_dieteticas=request.required_diets,
                    ingredientes_restringidos=request.restricted_ingredients
                )
                
                # Sistema aprende del feedback
                decision = cbr.retainer.evaluate_retention(request, menu_elegido, feedback)
                
                if decision.should_retain:
                    cbr.retainer.retain(request, menu_elegido, feedback)
                
                # Obtener estadísticas
                stats = cbr.get_statistics()
                
                # Guardar estado en historia
                estado = {
                    'iteracion': i,
                    'total_casos': stats['case_base']['total_cases'],
                    'feedback_avg': stats['case_base']['avg_feedback'],
                    'tasa_exito': stats['case_base']['success_rate'],
                    'usuario': usuario.nombre,
                    'evento': request.event_type.value,
                    'feedback_score': feedback.score,
                    'decision': decision.action,
                    'stats': stats
                }
                historia.append(estado)
                
                # Limpiar pantalla y mostrar progreso
                limpiar_pantalla()
                mostrar_barra_progreso(
                    i, num_iteraciones,
                    stats['case_base']['total_cases'],
                    stats['case_base']['avg_feedback'],
                    stats['case_base']['success_rate']
                )
                
                # Mostrar evento actual
                print(f"\n📝 Solicitud #{i}:")
                print(f"   Usuario: {usuario.nombre}")
                print(f"   Evento: {request.event_type.value}")
                print(f"   Presupuesto solicitado: {request.price_max:.0f}€")
                print(f"   Comensales: {request.num_guests}")
                
                # Mostrar restricciones si existen
                if request.required_diets:
                    print(f"   Dietas requeridas: {', '.join(request.required_diets)}")
                if request.restricted_ingredients:
                    print(f"   Ingredientes restringidos: {', '.join(request.restricted_ingredients)}")
                
                print(f"\n✅ Menú servido:")
                print(f"   Entrada: {menu_elegido.starter.name}")
                print(f"   Principal: {menu_elegido.main_course.name}")
                print(f"   Postre: {menu_elegido.dessert.name}")
                print(f"   Precio final: {menu_elegido.total_price:.2f}€")
                
                print(f"\n⭐ Feedback del usuario:")
                print(f"   Score: {feedback.score:.1f}/5 {'⭐' * int(feedback.score)}")
                print(f"   Comentario: {feedback.comments}")
                print(f"   {'✅ Recomendaría' if feedback.would_recommend else '❌ No recomendaría'}")
                
                print(f"\n🧠 Decisión de aprendizaje:")
                accion_emoji = {
                    'add_new': '🆕 AÑADIR NUEVO',
                    'update_existing': '♻️  ACTUALIZAR',
                    'discard': '🗑️  DESCARTAR'
                }
                print(f"   Acción: {accion_emoji.get(decision.action, decision.action)}")
                print(f"   Razón: {decision.reason}")
                
                # Mostrar distribución
                visualizar_distribucion_casos(stats)
                
                # Pausa para visualización
                time.sleep(velocidad)
            
            else:
                print(f"\n❌ No se pudieron generar menús para la solicitud #{i}")
    
    except KeyboardInterrupt:
        print("\n\n⏸️  Simulación detenida por el usuario")
    
    # Mostrar resumen final
    print("\n" * 2)
    print("=" * 70)
    print("📊 RESUMEN FINAL DE LA SIMULACIÓN")
    print("=" * 70)
    
    if historia:
        estado_inicial = historia[0]
        estado_final = historia[-1]
        
        print(f"\n🔢 Estadísticas Generales:")
        print(f"   Iteraciones completadas: {len(historia)}")
        print(f"   Casos iniciales: {estado_inicial['total_casos']}")
        print(f"   Casos finales: {estado_final['total_casos']}")
        print(f"   Casos aprendidos: {estado_final['total_casos'] - estado_inicial['total_casos']}")
        
        print(f"\n📈 Mejora del Sistema:")
        print(f"   Feedback inicial: {estado_inicial['feedback_avg']:.2f}/5")
        print(f"   Feedback final: {estado_final['feedback_avg']:.2f}/5")
        mejora = estado_final['feedback_avg'] - estado_inicial['feedback_avg']
        print(f"   Mejora: {mejora:+.2f} {'📈' if mejora > 0 else '📉' if mejora < 0 else '➡️'}")
        
        print(f"\n✅ Tasa de Éxito:")
        print(f"   Inicial: {estado_inicial['tasa_exito']:.0%}")
        print(f"   Final: {estado_final['tasa_exito']:.0%}")
        
        # Contar decisiones
        decisiones = {}
        for estado in historia:
            accion = estado['decision']
            decisiones[accion] = decisiones.get(accion, 0) + 1
        
        print(f"\n🧠 Decisiones de Aprendizaje:")
        for accion, count in decisiones.items():
            porcentaje = (count / len(historia)) * 100
            print(f"   {accion:20s}: {count:3d} ({porcentaje:5.1f}%)")
        
        # Mostrar evolución
        if len(historia) > 5:
            print(f"\n📊 Mostrando evolución cada 5 iteraciones:")
            historia_filtrada = [historia[i] for i in range(0, len(historia), 5)]
            visualizar_evolucion(historia_filtrada)
        else:
            visualizar_evolucion(historia)
        
        # Distribución final
        print("\n" + "=" * 70)
        visualizar_distribucion_casos(estado_final['stats'])
        
        print("\n" + "=" * 70)
        print("✨ Simulación completada exitosamente")
        print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulación de usuarios sintéticos CBR')
    parser.add_argument('-n', '--iteraciones', type=int, default=30,
                       help='Número de iteraciones (default: 30)')
    parser.add_argument('-v', '--velocidad', type=float, default=0.5,
                       help='Velocidad de animación en segundos (default: 0.5)')
    
    args = parser.parse_args()
    
    simular_usuarios(args.iteraciones, args.velocidad)
