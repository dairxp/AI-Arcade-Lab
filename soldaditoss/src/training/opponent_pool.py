"""
Opponent Pool para entrenamiento con self-play
"""

import os
import glob
import random
from typing import List, Optional, Dict, Any
from stable_baselines3 import PPO


class OpponentPool:
    """
    Pool de oponentes para self-play

    Mantiene un conjunto de modelos guardados para usar como
    oponentes durante el entrenamiento, evitando overfitting.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Diccionario de configuración completo
        """
        if 'opponent_pool' not in config:
            raise ValueError("Configuración de opponent_pool no encontrada")

        pool_config = config['opponent_pool']

        if not pool_config.get('enabled', False):
            raise ValueError("Opponent pool no está habilitado en la configuración")

        self.max_size = pool_config.get('max_size', 5)
        self.save_freq = pool_config.get('save_frequency', 100000)
        self.pool_dir = pool_config.get('pool_dir', './models/opponent_pool/')

        self.pool: List[str] = []  # Lista de paths a modelos

        # Crear directorio si no existe
        os.makedirs(self.pool_dir, exist_ok=True)

        # Cargar modelos existentes
        self._load_existing_models()

    def _load_existing_models(self) -> None:
        """Carga modelos existentes del disco"""
        # Buscar archivos .zip en pool_dir
        pattern = os.path.join(self.pool_dir, "model_*.zip")
        existing_models = glob.glob(pattern)

        if existing_models:
            # Ordenar por timestep (extraído del nombre)
            def get_timestep(path):
                try:
                    filename = os.path.basename(path)
                    timestep_str = filename.replace('model_', '').replace('.zip', '')
                    return int(timestep_str)
                except:
                    return 0

            existing_models.sort(key=get_timestep)

            # Tomar solo los últimos max_size modelos
            self.pool = [p.replace('.zip', '') for p in existing_models[-self.max_size:]]

            print(f"[OPPONENT POOL] Cargados {len(self.pool)} modelos existentes")

    def add_model(self, model: PPO, timestep: int) -> None:
        """
        Agrega un modelo al pool

        Args:
            model: Modelo PPO a guardar
            timestep: Timestep actual del entrenamiento
        """
        model_path = os.path.join(self.pool_dir, f"model_{timestep}")

        # Guardar modelo
        model.save(model_path)
        self.pool.append(model_path)

        print(f"[OPPONENT POOL] Modelo guardado: {model_path}.zip")

        # Mantener solo últimos max_size modelos
        if len(self.pool) > self.max_size:
            old_path = self.pool.pop(0)

            # Eliminar archivo antiguo
            if os.path.exists(old_path + '.zip'):
                os.remove(old_path + '.zip')
                print(f"[OPPONENT POOL] Modelo antiguo eliminado: {old_path}.zip")

    def sample_opponent(self, base_env) -> Optional[PPO]:
        """
        Selecciona un oponente aleatorio del pool

        Args:
            base_env: Entorno base para cargar el modelo

        Returns:
            Modelo PPO cargado o None si el pool está vacío
        """
        if not self.pool:
            print("[OPPONENT POOL] Pool vacío, no hay oponente disponible")
            return None

        # Seleccionar modelo aleatorio
        model_path = random.choice(self.pool)

        try:
            # Cargar modelo (CPU es mejor para políticas MLP)
            opponent = PPO.load(model_path, env=base_env, device='cpu')
            print(f"[OPPONENT POOL] Oponente cargado: {os.path.basename(model_path)}.zip")
            return opponent

        except Exception as e:
            print(f"[OPPONENT POOL] Error cargando oponente {model_path}: {e}")
            return None

    def sample_opponent_weighted(self, base_env, recent_bias: float = 0.7) -> Optional[PPO]:
        """
        Selecciona un oponente con sesgo hacia modelos más recientes

        Args:
            base_env: Entorno base
            recent_bias: Probabilidad de elegir del 50% más reciente (0-1)

        Returns:
            Modelo PPO cargado o None
        """
        if not self.pool:
            return None

        # Decidir si elegir del grupo reciente o de todo el pool
        if random.random() < recent_bias and len(self.pool) > 1:
            # Elegir de la mitad más reciente
            recent_half = self.pool[len(self.pool)//2:]
            model_path = random.choice(recent_half)
        else:
            # Elegir de todo el pool
            model_path = random.choice(self.pool)

        try:
            # Cargar modelo (CPU es mejor para políticas MLP)
            opponent = PPO.load(model_path, env=base_env, device='cpu')
            return opponent
        except Exception as e:
            print(f"[OPPONENT POOL] Error cargando oponente: {e}")
            return None

    def should_save(self, timestep: int) -> bool:
        """
        Verifica si debe guardar en este timestep

        Args:
            timestep: Timestep actual

        Returns:
            True si debe guardar
        """
        return timestep > 0 and timestep % self.save_freq == 0

    def get_pool_size(self) -> int:
        """Retorna el tamaño actual del pool"""
        return len(self.pool)

    def clear_pool(self) -> None:
        """Elimina todos los modelos del pool"""
        for model_path in self.pool:
            if os.path.exists(model_path + '.zip'):
                os.remove(model_path + '.zip')

        self.pool = []
        print("[OPPONENT POOL] Pool limpiado")

    def get_pool_info(self) -> Dict[str, Any]:
        """
        Retorna información del pool

        Returns:
            Diccionario con info del pool
        """
        timesteps = []
        for path in self.pool:
            try:
                filename = os.path.basename(path)
                timestep = int(filename.replace('model_', ''))
                timesteps.append(timestep)
            except:
                pass

        return {
            'size': len(self.pool),
            'max_size': self.max_size,
            'save_frequency': self.save_freq,
            'timesteps': timesteps,
            'oldest_timestep': min(timesteps) if timesteps else None,
            'newest_timestep': max(timesteps) if timesteps else None
        }

    def __repr__(self) -> str:
        """Representación en string"""
        return f"OpponentPool(size={len(self.pool)}/{self.max_size})"
