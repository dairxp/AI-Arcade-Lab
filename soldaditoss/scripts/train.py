"""
Script de entrenamiento para agentes RTS con PPO y self-play
"""

import sys
import os
import argparse
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.env import RTSEnv, SelfPlayEnv
from src.agents import create_ppo_agent
from src.training import TrainingCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor


def create_env(render_mode=None):
    """Crea el entorno de entrenamiento"""
    base_env = RTSEnv(
        map_size=(1200, 800),  # IMPORTANTE: Debe coincidir con play.py para compatibilidad
        units_per_team=5,
        max_steps=1000,
        render_mode=render_mode
    )
    return SelfPlayEnv(base_env, opponent_policy=None, swap_teams_prob=0.5)


def train(total_timesteps: int = 1_000_000,
          save_freq: int = 50_000,
          model_dir: str = './models/',
          log_dir: str = './logs/',
          continue_training: bool = False,
          model_path: str = None):
    """
    Entrena un agente PPO con self-play

    Args:
        total_timesteps: Número total de pasos de entrenamiento
        save_freq: Frecuencia de guardado del modelo
        model_dir: Directorio para guardar modelos
        log_dir: Directorio para logs de TensorBoard
        continue_training: Si True, continúa entrenamiento desde un modelo existente
        model_path: Ruta al modelo para continuar entrenamiento
    """
    print("=" * 60)
    print("Entrenamiento RTS con PPO y Self-Play")
    print("=" * 60)

    # Crear directorios si no existen
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # Crear entorno
    print("\nCreando entorno...")
    env = create_env()

    # Vectorizar el entorno
    vec_env = DummyVecEnv([lambda: env])
    vec_env = VecMonitor(vec_env)

    # Crear o cargar el modelo
    if continue_training and model_path and os.path.exists(model_path):
        print(f"\nCargando modelo desde {model_path}...")
        from src.agents import load_agent
        model = load_agent(model_path, vec_env)
    else:
        print("\nCreando nuevo modelo PPO...")
        model = create_ppo_agent(
            env=vec_env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            tensorboard_log=log_dir,
            verbose=1
        )

    # Callback para guardar modelos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    callback = TrainingCallback(
        check_freq=save_freq,
        save_path=model_dir,
        verbose=1
    )

    print(f"\nIniciando entrenamiento por {total_timesteps:,} timesteps...")
    print(f"Modelos se guardarán en: {model_dir}")
    print(f"Logs de TensorBoard en: {log_dir}")
    print("\nPara ver el progreso en tiempo real, ejecuta:")
    print(f"  tensorboard --logdir {log_dir}")
    print("=" * 60)

    try:
        # Entrenar
        model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            progress_bar=True
        )

        # Guardar modelo final
        final_model_path = f"{model_dir}/final_model_{timestamp}"
        model.save(final_model_path)
        print(f"\n[OK] Modelo final guardado en: {final_model_path}.zip")

    except KeyboardInterrupt:
        print("\n\nEntrenamiento interrumpido por el usuario.")
        interrupt_model_path = f"{model_dir}/interrupted_model_{timestamp}"
        model.save(interrupt_model_path)
        print(f"[OK] Modelo guardado en: {interrupt_model_path}.zip")

    finally:
        env.close()

    print("\n" + "=" * 60)
    print("Entrenamiento completado!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar agente RTS con PPO")

    parser.add_argument(
        '--timesteps',
        type=int,
        default=1_000_000,
        help='Número total de timesteps para entrenar (default: 1,000,000)'
    )

    parser.add_argument(
        '--save-freq',
        type=int,
        default=50_000,
        help='Frecuencia para guardar el modelo (default: 50,000)'
    )

    parser.add_argument(
        '--model-dir',
        type=str,
        default='./models/',
        help='Directorio para guardar modelos (default: ./models/)'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default='./logs/',
        help='Directorio para logs de TensorBoard (default: ./logs/)'
    )

    parser.add_argument(
        '--continue',
        dest='continue_training',
        action='store_true',
        help='Continuar entrenamiento desde un modelo existente'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default='./models/best_model.zip',
        help='Ruta al modelo para continuar entrenamiento'
    )

    args = parser.parse_args()

    train(
        total_timesteps=args.timesteps,
        save_freq=args.save_freq,
        model_dir=args.model_dir,
        log_dir=args.log_dir,
        continue_training=args.continue_training,
        model_path=args.model_path
    )
