"""
Sistema de configuracion centralizado para Soldaditos RTS
"""

import yaml
import os
from typing import Dict, Any, Optional


class GameConfig:
    """Clase para manejar la configuracion del juego"""

    _instance: Optional['GameConfig'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        """Singleton para asegurar una sola instancia de config"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = "config/game_config.yaml") -> None:
        """
        Carga configuracion desde archivo YAML

        Args:
            config_path: Ruta al archivo de configuracion
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Archivo de configuracion no encontrado: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        self._validate_config()

    def _validate_config(self) -> None:
        """Valida que la configuracion tenga los campos requeridos"""
        required_sections = ['game', 'unit_types', 'curriculum', 'opponent_pool', 'fog_of_war', 'training']

        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Seccion requerida faltante en configuracion: {section}")

        # Validar tipos de unidades
        required_unit_types = ['soldier', 'tank', 'scout']
        for unit_type in required_unit_types:
            if unit_type not in self._config['unit_types']:
                raise ValueError(f"Tipo de unidad requerido faltante: {unit_type}")

    def get(self, *keys, default=None) -> Any:
        """
        Obtiene valor de configuracion con acceso anidado

        Args:
            *keys: Claves para acceder anidadamente (ej: 'game', 'map_size')
            default: Valor por defecto si no se encuentra

        Returns:
            Valor de configuracion

        Example:
            config.get('game', 'map_size')  # [800, 600]
            config.get('training', 'learning_rate')  # 0.0003
        """
        if self._config is None:
            raise RuntimeError("Configuracion no cargada. Llama a load() primero.")

        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_unit_stats(self, unit_type: str) -> Dict[str, float]:
        """
        Obtiene estadisticas de un tipo de unidad

        Args:
            unit_type: Tipo de unidad ('soldier', 'tank', 'scout')

        Returns:
            Diccionario con stats de la unidad
        """
        return self.get('unit_types', unit_type, default={})

    def get_curriculum_stage(self, stage_index: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene configuracion de un stage del curriculum

        Args:
            stage_index: Indice del stage (0-based)

        Returns:
            Configuracion del stage o None si no existe
        """
        stages = self.get('curriculum', 'stages', default=[])
        if 0 <= stage_index < len(stages):
            return stages[stage_index]
        return None

    def get_num_curriculum_stages(self) -> int:
        """Retorna el numero total de stages en el curriculum"""
        return len(self.get('curriculum', 'stages', default=[]))

    @property
    def map_size(self) -> tuple:
        """Retorna tamano del mapa como tupla"""
        size = self.get('game', 'map_size', default=[800, 600])
        return tuple(size)

    @property
    def max_steps(self) -> int:
        """Retorna numero maximo de steps por episodio"""
        return self.get('game', 'max_steps', default=1000)

    @property
    def fog_of_war_enabled(self) -> bool:
        """Retorna si Fog of War esta habilitado"""
        return self.get('fog_of_war', 'enabled', default=True)

    @property
    def curriculum_enabled(self) -> bool:
        """Retorna si Curriculum Learning esta habilitado"""
        return self.get('curriculum', 'enabled', default=True)

    @property
    def opponent_pool_enabled(self) -> bool:
        """Retorna si Opponent Pool esta habilitado"""
        return self.get('opponent_pool', 'enabled', default=True)

    def to_dict(self) -> Dict[str, Any]:
        """Retorna configuracion completa como diccionario"""
        if self._config is None:
            raise RuntimeError("Configuracion no cargada. Llama a load() primero.")
        return self._config.copy()

    def __repr__(self) -> str:
        """Representacion en string de la configuracion"""
        if self._config is None:
            return "GameConfig(not loaded)"
        return f"GameConfig(map_size={self.map_size}, curriculum={self.curriculum_enabled}, fow={self.fog_of_war_enabled})"


# Instancia global de configuracion
config = GameConfig()


def load_config(config_path: str = "config/game_config.yaml") -> GameConfig:
    """
    Funcion helper para cargar configuracion

    Args:
        config_path: Ruta al archivo de configuracion

    Returns:
        Instancia de GameConfig cargada
    """
    config.load(config_path)
    return config


def get_config() -> GameConfig:
    """
    Obtiene la instancia de configuracion

    Returns:
        Instancia de GameConfig

    Raises:
        RuntimeError: Si la configuracion no ha sido cargada
    """
    if config._config is None:
        raise RuntimeError(
            "Configuracion no cargada. "
            "Llama a load_config() antes de usar get_config()"
        )
    return config
