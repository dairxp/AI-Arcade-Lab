"""
Curriculum Learning para entrenamiento progresivo
"""

from typing import Dict, Any, List, Optional
import numpy as np


class CurriculumScheduler:
    """
    Gestor de Curriculum Learning

    Maneja la progresión a través de diferentes stages de dificultad
    basándose en el rendimiento del agente.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Diccionario de configuración completo
        """
        if 'curriculum' not in config:
            raise ValueError("Configuración de curriculum no encontrada")

        curriculum_config = config['curriculum']

        if not curriculum_config.get('enabled', False):
            raise ValueError("Curriculum learning no está habilitado en la configuración")

        self.stages = curriculum_config.get('stages', [])
        if not self.stages:
            raise ValueError("No hay stages definidos en el curriculum")

        self.current_stage = 0
        self.episode_results: List[bool] = []
        self.episode_count = 0

        # Stats por stage
        self.stage_stats = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'episodes': 0
        }

    def get_current_stage(self) -> int:
        """Retorna el índice del stage actual"""
        return self.current_stage

    def get_current_config(self) -> Dict[str, Any]:
        """Retorna configuración del stage actual"""
        return self.stages[self.current_stage].copy()

    def get_stage_name(self) -> str:
        """Retorna nombre del stage actual"""
        return self.stages[self.current_stage].get('name', f'Stage {self.current_stage + 1}')

    def add_episode_result(self, won: bool, draw: bool = False) -> None:
        """
        Registra resultado de un episodio

        Args:
            won: Si el agente ganó
            draw: Si fue empate
        """
        self.episode_results.append(won)
        self.episode_count += 1

        if draw:
            self.stage_stats['draws'] += 1
        elif won:
            self.stage_stats['wins'] += 1
        else:
            self.stage_stats['losses'] += 1

        self.stage_stats['episodes'] += 1

        # Mantener solo últimos 100 episodios
        if len(self.episode_results) > 100:
            self.episode_results.pop(0)

    def get_win_rate(self) -> float:
        """
        Calcula tasa de victoria actual

        Returns:
            Win rate (0.0 a 1.0)
        """
        if not self.episode_results:
            return 0.0

        return sum(self.episode_results) / len(self.episode_results)

    def should_advance(self) -> bool:
        """
        Verifica si debe avanzar al siguiente stage

        Returns:
            True si debe avanzar
        """
        current_config = self.get_current_config()

        # Verificar mínimo de episodios
        min_episodes = current_config.get('min_episodes', 100)
        if len(self.episode_results) < min_episodes:
            return False

        # Verificar win rate threshold
        win_rate = self.get_win_rate()
        threshold = current_config.get('win_rate_threshold', 0.6)

        return win_rate >= threshold

    def can_advance(self) -> bool:
        """Verifica si hay un siguiente stage disponible"""
        return self.current_stage < len(self.stages) - 1

    def advance_stage(self) -> bool:
        """
        Avanza al siguiente stage si es posible

        Returns:
            True si avanzó, False si ya está en el último stage
        """
        if not self.can_advance():
            return False

        self.current_stage += 1
        self.episode_results = []

        # Reset stats
        self.stage_stats = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'episodes': 0
        }

        return True

    def get_progress_info(self) -> Dict[str, Any]:
        """
        Retorna información de progreso actual

        Returns:
            Diccionario con info de progreso
        """
        return {
            'current_stage': self.current_stage,
            'total_stages': len(self.stages),
            'stage_name': self.get_stage_name(),
            'win_rate': self.get_win_rate(),
            'episodes_in_stage': len(self.episode_results),
            'total_episodes': self.episode_count,
            'stats': self.stage_stats.copy(),
            'can_advance': self.can_advance(),
            'should_advance': self.should_advance()
        }

    def reset(self) -> None:
        """Reinicia el curriculum al stage inicial"""
        self.current_stage = 0
        self.episode_results = []
        self.episode_count = 0
        self.stage_stats = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'episodes': 0
        }

    def __repr__(self) -> str:
        """Representación en string"""
        return (
            f"CurriculumScheduler(stage={self.current_stage}/{len(self.stages)}, "
            f"win_rate={self.get_win_rate():.2%})"
        )
