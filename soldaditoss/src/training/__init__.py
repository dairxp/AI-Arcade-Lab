"""
Modulo de training para Soldaditos RTS v2.0

Incluye:
- Curriculum Learning
- Opponent Pool
- Callbacks de entrenamiento
"""

from .curriculum import CurriculumScheduler
from .callbacks import TrainingCallback, CurriculumCallback, OpponentPoolCallback
from .opponent_pool import OpponentPool

__all__ = [
    'CurriculumScheduler',
    'TrainingCallback',
    'CurriculumCallback',
    'OpponentPoolCallback',
    'OpponentPool'
]
