"""
Script para visualizar partidas con modelos entrenados
"""

import sys
import os
import argparse
import time

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.env import RTSEnv, SelfPlayEnv
from src.agents import load_agent
import numpy as np


def _get_simple_opponent_actions(env: RTSEnv) -> np.ndarray:
    """
    Estrategia simple para el oponente: atacar al enemigo más cercano
    """
    actions = []
    opponent_units = sorted(env.game_state.get_units_by_team(1), key=lambda x: x.unit_id)
    enemy_units = sorted(env.game_state.get_units_by_team(0), key=lambda x: x.unit_id)

    for unit in opponent_units:
        if enemy_units:
            # Encontrar el enemigo más cercano
            closest_idx = 0
            min_dist = float('inf')
            for i, enemy in enumerate(enemy_units):
                if enemy.is_alive:
                    dist = unit.distance_to(enemy)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
            actions.append(closest_idx)
        else:
            actions.append(0)  # Acción por defecto

    return np.array(actions)


def play_game(model_path: str,
              num_games: int = 1,
              render: bool = True,
              opponent_model_path: str = None,
              delay: float = 0.05):
    """
    Juega partidas usando modelos entrenados

    Args:
        model_path: Ruta al modelo del agente principal
        num_games: Número de partidas a jugar
        render: Si True, renderiza el juego visualmente
        opponent_model_path: Ruta al modelo del oponente (si None, usa el mismo modelo)
        delay: Delay entre frames en segundos
    """
    print("=" * 60)
    print("Visualización de Partidas RTS")
    print("=" * 60)

    # Crear entorno
    render_mode = 'human' if render else None
    base_env = RTSEnv(
        map_size=(1200, 800),  # Mapa más grande y realista
        units_per_team=5,  # Must match train.py configuration
        max_steps=1000,
        render_mode=render_mode
    )

    # Cargar modelo principal
    print(f"\nCargando modelo principal desde: {model_path}")
    model = load_agent(model_path, base_env)

    # Cargar modelo oponente (si se especifica)
    if opponent_model_path:
        print(f"Cargando modelo oponente desde: {opponent_model_path}")
        opponent_model = load_agent(opponent_model_path, base_env)
    else:
        print("Usando el mismo modelo para ambos equipos (self-play)")
        opponent_model = model

    # Crear entorno con self-play
    env = SelfPlayEnv(base_env, opponent_policy=opponent_model, swap_teams_prob=0.5)

    # Estadísticas
    wins = 0
    losses = 0
    draws = 0

    print(f"\nJugando {num_games} partida(s)...")
    print("Presiona ESC para salir durante la visualización")
    print("=" * 60)

    for game_num in range(num_games):
        print(f"\n--- Partida {game_num + 1}/{num_games} ---")

        obs, info = env.reset()
        teams_swapped = info['teams_swapped']

        done = False
        step_count = 0
        total_reward = 0

        while not done:
            # Obtener acción del modelo
            action, _ = model.predict(obs, deterministic=True)

            # Ejecutar acción
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            total_reward += reward
            step_count += 1

            # Renderizar si está habilitado
            if render:
                env.render()
                time.sleep(delay)

        # Resultados de la partida
        winner = info.get('actual_winner', info.get('winner'))

        print(f"Pasos: {step_count}")
        print(f"Recompensa total: {total_reward:.2f}")

        if winner is None:
            print("Resultado: EMPATE")
            draws += 1
        elif (winner == 0 and not teams_swapped) or (winner == 1 and teams_swapped):
            print("Resultado: VICTORIA")
            wins += 1
        else:
            print("Resultado: DERROTA")
            losses += 1

        print(f"Unidades restantes - Team 0: {info['team0_units']}, Team 1: {info['team1_units']}")

    # Mostrar estadísticas finales
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS FINALES")
    print("=" * 60)
    print(f"Total de partidas: {num_games}")
    print(f"Victorias: {wins} ({wins/num_games*100:.1f}%)")
    print(f"Derrotas: {losses} ({losses/num_games*100:.1f}%)")
    print(f"Empates: {draws} ({draws/num_games*100:.1f}%)")
    print("=" * 60)

    env.close()


def watch_random_game(delay: float = 0.05):
    """
    Visualiza una partida con agentes aleatorios (para debugging)

    Args:
        delay: Delay entre frames en segundos
    """
    print("=" * 60)
    print("Visualización de Partida Aleatoria")
    print("=" * 60)

    env = RTSEnv(
        map_size=(1200, 800),  # Mapa más grande y realista
        units_per_team=5,  # Must match train.py configuration
        max_steps=1000,
        render_mode='human'
    )

    obs, info = env.reset()
    done = False
    step_count = 0

    print("\nPresiona ESC para salir")
    print("Jugando con acciones aleatorias...")

    while not done:
        action = env.action_space.sample()

        # Aplicar acciones del oponente antes de step
        opponent_actions = _get_simple_opponent_actions(env)
        env._apply_actions(team=1, actions=opponent_actions)

        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

        env.render()
        time.sleep(delay)
        step_count += 1

    print(f"\nPartida terminó en {step_count} pasos")
    print(f"Ganador: Team {info['winner']}" if info['winner'] is not None else "Empate")

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualizar partidas RTS")

    parser.add_argument(
        '--model',
        type=str,
        default='./models/best_model.zip',
        help='Ruta al modelo entrenado (default: ./models/best_model.zip)'
    )

    parser.add_argument(
        '--opponent',
        type=str,
        default=None,
        help='Ruta al modelo del oponente (default: mismo que --model)'
    )

    parser.add_argument(
        '--games',
        type=int,
        default=1,
        help='Número de partidas a jugar (default: 1)'
    )

    parser.add_argument(
        '--no-render',
        action='store_true',
        help='No renderizar visualmente (solo estadísticas)'
    )

    parser.add_argument(
        '--random',
        action='store_true',
        help='Jugar con agentes aleatorios (para testing)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=0.05,
        help='Delay entre frames en segundos (default: 0.05)'
    )

    args = parser.parse_args()

    if args.random:
        watch_random_game(delay=args.delay)
    else:
        if not os.path.exists(args.model):
            print(f"Error: No se encontró el modelo en {args.model}")
            print("Entrena un modelo primero con: python scripts/train.py")
            sys.exit(1)

        play_game(
            model_path=args.model,
            num_games=args.games,
            render=not args.no_render,
            opponent_model_path=args.opponent,
            delay=args.delay
        )
