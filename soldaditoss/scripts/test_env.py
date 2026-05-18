"""
Script para probar que el entorno funciona correctamente
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.env import RTSEnv, SelfPlayEnv
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


def test_basic_env():
    """Prueba el entorno básico"""
    print("=" * 60)
    print("Probando RTSEnv básico")
    print("=" * 60)

    env = RTSEnv(map_size=(800, 600), units_per_team=5)

    print("\nEspacio de observación:", env.observation_space)
    print("Espacio de acción:", env.action_space)

    # Reset
    obs, info = env.reset()
    print(f"\nObservación shape: {obs.shape}")
    print(f"Info inicial: {info}")

    # Ejecutar algunos pasos con acciones aleatorias
    print("\nEjecutando 10 pasos con acciones aleatorias...")
    for i in range(10):
        action = env.action_space.sample()

        # Aplicar acciones del oponente antes de step
        opponent_actions = _get_simple_opponent_actions(env)
        env._apply_actions(team=1, actions=opponent_actions)

        obs, reward, terminated, truncated, info = env.step(action)

        print(f"Step {i+1}: reward={reward:.2f}, "
              f"team0_units={info['team0_units']}, "
              f"team1_units={info['team1_units']}, "
              f"terminated={terminated}")

        if terminated:
            print(f"\n¡Juego terminado! Ganador: Team {info['winner']}")
            break

    env.close()
    print("\n[OK] Prueba de RTSEnv completada")


def test_self_play_env():
    """Prueba el entorno de self-play"""
    print("\n" + "=" * 60)
    print("Probando SelfPlayEnv")
    print("=" * 60)

    base_env = RTSEnv(map_size=(800, 600), units_per_team=5)
    env = SelfPlayEnv(base_env, opponent_policy=None, swap_teams_prob=0.5)

    print("\nEspacio de observación:", env.observation_space)
    print("Espacio de acción:", env.action_space)

    # Ejecutar 2 episodios
    for episode in range(2):
        print(f"\n--- Episodio {episode + 1} ---")

        obs, info = env.reset()
        print(f"Teams swapped: {info['teams_swapped']}")

        done = False
        step_count = 0
        total_reward = 0

        while not done and step_count < 20:  # Limitar a 20 pasos para el test
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            total_reward += reward
            step_count += 1

        print(f"Pasos: {step_count}")
        print(f"Recompensa total: {total_reward:.2f}")
        print(f"Terminado: {done}")

        if done and info['winner'] is not None:
            print(f"Ganador (perspectiva del entorno): Team {info['winner']}")
            print(f"Ganador real: Team {info['actual_winner']}")

    env.close()
    print("\n[OK] Prueba de SelfPlayEnv completada")


def test_render():
    """Prueba el renderizado del entorno"""
    print("\n" + "=" * 60)
    print("Probando renderizado")
    print("=" * 60)
    print("Se abrirá una ventana de Pygame. Presiona ESC para cerrar.")

    env = RTSEnv(map_size=(800, 600), units_per_team=5, render_mode='human')

    obs, info = env.reset()

    print("\nEjecutando 100 pasos con renderizado...")
    for i in range(100):
        action = env.action_space.sample()

        # Aplicar acciones del oponente antes de step
        opponent_actions = _get_simple_opponent_actions(env)
        env._apply_actions(team=1, actions=opponent_actions)

        obs, reward, terminated, truncated, info = env.step(action)

        env.render()

        if terminated:
            print(f"\n¡Juego terminado en el paso {i+1}!")
            print(f"Ganador: Team {info['winner']}")
            break

        # Pequeña pausa para hacer la visualización más lenta
        import time
        time.sleep(0.05)

    # Mantener la ventana abierta un momento más
    import time
    time.sleep(2)

    env.close()
    print("\n[OK] Prueba de renderizado completada")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Probar el entorno RTS")
    parser.add_argument(
        '--render',
        action='store_true',
        help='Incluir prueba de renderizado (abre ventana de Pygame)'
    )

    args = parser.parse_args()

    try:
        test_basic_env()
        test_self_play_env()

        if args.render:
            test_render()

        print("\n" + "=" * 60)
        print("[OK] TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
