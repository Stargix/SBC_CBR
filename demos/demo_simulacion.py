#!/usr/bin/env python3
"""
Simulación de usuarios sintéticos usando el sistema CBR.

Este script simula múltiples usuarios haciendo peticiones diversas,
dando feedback, y muestra cómo el sistema aprende y mejora con el tiempo.
"""

import sys
from pathlib import Path
import time
import random
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
    """Representa un usuario sintético con preferencias."""
    nombre: str
    evento: EventType
    presupuesto_min: float
    presupuesto_max: float
    estilo_preferido: CulinaryStyle = None
    cultura: CulturalTradition = None
    restricciones: List[str] = None
    exigente: float = 0.5  # 0.0 = permisivo, 1.0 = muy exigente
    
    def __post_init__(self):
        if self.restricciones is None:
            self.restricciones = []
    
    def generar_solicitud(self) -> Request:
        """Genera una solicitud basada en las preferencias del usuario."""
        return Request(
            event_type=self.evento,
            num_guests=random.randint(20, 150),
            price_max=random.uniform(self.presupuesto_min, self.presupuesto_max),
            season=random.choice(list(Season)),
            preferred_style=self.estilo_preferido,
            cultural_preference=self.cultura,
            required_diets=self.restricciones,
            wants_wine=random.choice([True, False])
        )
    
    def evaluar_menu(self, menu, precio_solicitado: float) -> FeedbackData:
        """Simula la evaluación del menú por parte del usuario."""
        score = 5.0
        comentarios = []
        
        # Evaluar precio
        diff_precio = abs(menu.total_price - precio_solicitado)
        if diff_precio > precio_solicitado * 0.2:
            score -= 1.0
            comentarios.append("precio fuera de rango")
        elif diff_precio > precio_solicitado * 0.1:
            score -= 0.3
        
        # Evaluar estilo
        if self.estilo_preferido and menu.dominant_style != self.estilo_preferido:
            score -= 0.5
            comentarios.append("estilo no coincide")
        
        # Evaluar cultura
        if self.cultura and menu.cultural_theme != self.cultura:
            score -= 0.3
        
        # Variabilidad aleatoria según exigencia
        variacion = random.gauss(0, 0.3 * self.exigente)
        score += variacion
        
        # Limitar entre 1 y 5
        score = max(1.0, min(5.0, score))
        
        # Determinar éxito
        success = score >= 3.5
        
        # Generar comentario
        if score >= 4.5:
            comentario_base = "Excelente menú"
        elif score >= 3.5:
            comentario_base = "Buen menú"
        else:
            comentario_base = "Menú mejorable"
        
        if comentarios:
            comentario_final = f"{comentario_base}, pero {', '.join(comentarios)}"
        else:
            comentario_final = comentario_base
        
        return FeedbackData(
            menu_id=menu.id,
            success=success,
            score=score,
            comments=comentario_final,
            would_recommend=score >= 4.0
        )


# Base de usuarios sintéticos
USUARIOS_SINTETICOS = [
    UsuarioSintetico("María (Novia exigente)", EventType.WEDDING, 80, 150, 
                     CulinaryStyle.GOURMET, exigente=0.8),
    UsuarioSintetico("Pedro (Familia económica)", EventType.FAMILIAR, 20, 40, 
                     CulinaryStyle.REGIONAL, exigente=0.3),
    UsuarioSintetico("Ana (Evento corporativo)", EventType.CORPORATE, 40, 70, 
                     CulinaryStyle.MODERN, exigente=0.6),
    UsuarioSintetico("Luis (Vegano estricto)", EventType.CONGRESS, 35, 60, 
                     CulinaryStyle.MODERN, restricciones=["vegetariano"], exigente=0.9),
    UsuarioSintetico("Carmen (Tradición española)", EventType.CHRISTENING, 30, 50, 
                     CulinaryStyle.REGIONAL, CulturalTradition.SPANISH, exigente=0.4),
    UsuarioSintetico("Jorge (Boda italiana)", EventType.WEDDING, 60, 100, 
                     CulinaryStyle.CLASSIC, CulturalTradition.ITALIAN, exigente=0.5),
    UsuarioSintetico("Laura (Comunión sencilla)", EventType.COMMUNION, 30, 50, 
                     CulinaryStyle.CLASSIC, exigente=0.4),
    UsuarioSintetico("Miguel (Ejecutivo)", EventType.CORPORATE, 50, 80, 
                     CulinaryStyle.FUSION, exigente=0.7),
    UsuarioSintetico("Isabel (Familia grande)", EventType.FAMILIAR, 25, 45, 
                     CulinaryStyle.REGIONAL, exigente=0.3),
    UsuarioSintetico("Antonio (Sibarita)", EventType.WEDDING, 100, 180, 
                     CulinaryStyle.SIBARITA, exigente=0.9),
]


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
    
    Args:
        num_iteraciones: Número de iteraciones a simular
        velocidad: Tiempo de espera entre iteraciones (segundos)
    """
    print("=" * 70)
    print("🎭 SIMULACIÓN DE USUARIOS SINTÉTICOS")
    print("=" * 70)
    print(f"\nSimulando {num_iteraciones} peticiones con {len(USUARIOS_SINTETICOS)} usuarios...")
    print("Presiona Ctrl+C para detener la simulación\n")
    time.sleep(2)
    
    # Inicializar sistema
    config = CBRConfig(verbose=False, enable_learning=True)
    cbr = ChefDigitalCBR(config)
    
    # Historia para visualización
    historia = []
    
    try:
        for i in range(1, num_iteraciones + 1):
            # Seleccionar usuario aleatorio
            usuario = random.choice(USUARIOS_SINTETICOS)
            
            # Generar solicitud
            request = usuario.generar_solicitud()
            
            # Procesar con el sistema CBR
            result = cbr.process_request(request)
            
            # Simular evaluación del usuario
            if result.proposed_menus:
                # Usuario elige el primer menú (más similar)
                menu_elegido = result.proposed_menus[0].menu
                feedback = usuario.evaluar_menu(menu_elegido, request.price_max)
                
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
                print(f"   Presupuesto: {request.price_max:.0f}€")
                print(f"   Comensales: {request.num_guests}")
                
                print(f"\n✅ Menú servido:")
                print(f"   Entrada: {menu_elegido.starter.name}")
                print(f"   Principal: {menu_elegido.main_course.name}")
                print(f"   Postre: {menu_elegido.dessert.name}")
                print(f"   Precio: {menu_elegido.total_price:.2f}€")
                
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
