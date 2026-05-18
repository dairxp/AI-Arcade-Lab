"""
Callbacks para entrenamiento con Stable-Baselines3
"""

from stable_baselines3.common.callbacks import BaseCallback
from typing import Optional, Dict, Any
import numpy as np
import os


class TrainingCallback(BaseCallback):
    """
    Callback para monitorear y guardar modelos durante el entrenamiento
    """

    def __init__(self,
                 check_freq: int = 1000,
                 save_path: str = './models/',
                 verbose: int = 1):
        """
        Args:
            check_freq: Frecuencia de verificación (en steps)
            save_path: Directorio donde guardar modelos
            verbose: Nivel de verbosidad
        """
        super().__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        """Inicializa el callback"""
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        """
        Ejecutado en cada step

        Returns:
            True para continuar entrenamiento
        """
        if self.n_calls % self.check_freq == 0:
            # Obtener recompensas del monitor
            if len(self.model.ep_info_buffer) > 0:
                mean_reward = np.mean([ep_info["r"] for ep_info in self.model.ep_info_buffer])
                mean_length = np.mean([ep_info["l"] for ep_info in self.model.ep_info_buffer])

                if self.verbose > 0:
                    print(f"\n{'='*60}")
                    print(f"Steps: {self.num_timesteps:,}")
                    print(f"Mean Reward: {mean_reward:.2f}")
                    print(f"Mean Episode Length: {mean_length:.1f}")
                    print(f"{'='*60}")

                # Guardar el mejor modelo
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    if self.verbose > 0:
                        print(f"[OK] New best mean reward: {self.best_mean_reward:.2f}")
                        print(f"[OK] Saving model to {self.save_path}/best_model.zip")

                    self.model.save(f"{self.save_path}/best_model")

        return True


class CurriculumCallback(BaseCallback):
    """
    Callback para manejar Curriculum Learning

    Detecta cuando el agente debe avanzar al siguiente stage
    y actualiza el entorno accordingly.
    """

    def __init__(self,
                 curriculum_scheduler,
                 update_env_fn=None,
                 verbose: int = 1):
        """
        Args:
            curriculum_scheduler: Instancia de CurriculumScheduler
            update_env_fn: Función para actualizar el entorno al cambiar de stage
            verbose: Nivel de verbosidad
        """
        super().__init__(verbose)
        self.curriculum = curriculum_scheduler
        self.update_env_fn = update_env_fn
        self.last_episode_count = 0

    def _on_step(self) -> bool:
        """
        Verifica si debe avanzar de stage

        Returns:
            True para continuar entrenamiento
        """
        # Detectar fin de episodio
        dones = self.locals.get('dones', [False])

        if dones[0]:  # Fin de episodio
            # Obtener info del episodio
            infos = self.locals.get('infos', [{}])
            info = infos[0]

            # Determinar resultado
            winner = info.get('actual_winner', info.get('winner'))
            won = winner == 0  # Asumimos que agente es team 0
            draw = winner is None

            # Registrar resultado
            self.curriculum.add_episode_result(won, draw)

            # Verificar si debe avanzar
            if self.curriculum.should_advance() and self.curriculum.can_advance():
                old_stage = self.curriculum.get_stage_name()
                success = self.curriculum.advance_stage()

                if success:
                    new_stage = self.curriculum.get_stage_name()

                    if self.verbose > 0:
                        print(f"\n{'='*60}")
                        print(f"[CURRICULUM] Avanzando de stage!")
                        print(f"[CURRICULUM] {old_stage} -> {new_stage}")
                        print(f"[CURRICULUM] Win rate alcanzado: {self.curriculum.get_win_rate():.1%}")
                        print(f"{'='*60}\n")

                    # Actualizar entorno si se proporcionó función
                    if self.update_env_fn is not None:
                        new_config = self.curriculum.get_current_config()
                        self.update_env_fn(new_config)

            # Mostrar progreso periódicamente
            elif self.verbose > 1 and self.curriculum.episode_count % 50 == 0:
                progress = self.curriculum.get_progress_info()
                print(f"\n[CURRICULUM] {progress['stage_name']}: "
                      f"Win rate {progress['win_rate']:.1%} "
                      f"({progress['episodes_in_stage']} episodes)")

        return True


class OpponentPoolCallback(BaseCallback):
    """
    Callback para manejar Opponent Pool

    Guarda modelos periódicamente y actualiza el oponente
    del entorno de self-play.
    """

    def __init__(self,
                 opponent_pool,
                 self_play_env,
                 verbose: int = 1):
        """
        Args:
            opponent_pool: Instancia de OpponentPool
            self_play_env: Entorno de self-play
            verbose: Nivel de verbosidad
        """
        super().__init__(verbose)
        self.pool = opponent_pool
        self.env = self_play_env
        self.last_save_step = 0

    def _on_step(self) -> bool:
        """
        Verifica si debe guardar modelo en pool

        Returns:
            True para continuar entrenamiento
        """
        if self.pool.should_save(self.num_timesteps):
            # Evitar guardar múltiples veces en el mismo step
            if self.num_timesteps != self.last_save_step:
                if self.verbose > 0:
                    print(f"\n[OPPONENT POOL] Guardando modelo en pool (step {self.num_timesteps:,})")

                # Guardar modelo actual
                self.pool.add_model(self.model, self.num_timesteps)

                # Actualizar oponente del entorno
                new_opponent = self.pool.sample_opponent(self.env.env)

                if new_opponent:
                    self.env.set_opponent_policy(new_opponent)

                    if self.verbose > 0:
                        pool_size = len(self.pool.pool)
                        print(f"[OPPONENT POOL] Oponente actualizado. Pool size: {pool_size}")

                self.last_save_step = self.num_timesteps

        return True


class MultiCallback(BaseCallback):
    """
    Wrapper para ejecutar múltiples callbacks

    Útil para combinar TrainingCallback, CurriculumCallback y OpponentPoolCallback
    """

    def __init__(self, callbacks: list):
        """
        Args:
            callbacks: Lista de callbacks a ejecutar
        """
        super().__init__()
        self.callbacks = callbacks

    def _init_callback(self) -> None:
        """Inicializa todos los callbacks"""
        for callback in self.callbacks:
            callback.init_callback(self.model)

    def _on_training_start(self) -> None:
        """Ejecutado al inicio del entrenamiento"""
        for callback in self.callbacks:
            callback.on_training_start(self.locals, self.globals)

    def _on_rollout_start(self) -> None:
        """Ejecutado al inicio de cada rollout"""
        for callback in self.callbacks:
            callback.on_rollout_start()

    def _on_step(self) -> bool:
        """
        Ejecuta todos los callbacks en cada step

        Returns:
            True si todos los callbacks retornan True
        """
        for callback in self.callbacks:
            if not callback.on_step():
                return False
        return True

    def _on_rollout_end(self) -> None:
        """Ejecutado al final de cada rollout"""
        for callback in self.callbacks:
            callback.on_rollout_end()

    def _on_training_end(self) -> None:
        """Ejecutado al final del entrenamiento"""
        for callback in self.callbacks:
            callback.on_training_end()
