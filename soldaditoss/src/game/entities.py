import numpy as np
from typing import Tuple, Optional, Dict, Any


class Unit:
    """Representa una unidad en el juego RTS"""

    def __init__(self,
                 unit_id: int,
                 team: int,
                 position: Tuple[float, float],
                 unit_type: str = "soldier",
                 max_health: float = 100.0,
                 speed: float = 4.0,  # DUPLICADO: 2.0 → 4.0 para combate más rápido
                 attack_damage: float = 10.0,
                 attack_range: float = 100.0,  # DUPLICADO: 50 → 100 para engagement más rápido
                 attack_cooldown: float = 1.0,
                 vision_range: float = 150.0):
        """
        Args:
            unit_id: ID único de la unidad
            team: 0 para equipo azul, 1 para equipo rojo
            position: Posición (x, y) inicial
            unit_type: Tipo de unidad ('soldier', 'tank', 'scout')
            max_health: Salud máxima
            speed: Velocidad de movimiento (píxeles por step)
            attack_damage: Daño por ataque
            attack_range: Rango de ataque
            attack_cooldown: Tiempo entre ataques (en steps)
            vision_range: Rango de visión para Fog of War
        """
        self.unit_id = unit_id
        self.team = team
        self.unit_type = unit_type
        self.position = np.array(position, dtype=np.float32)
        self.max_health = max_health
        self.health = max_health
        self.speed = speed
        self.attack_damage = attack_damage
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self.vision_range = vision_range
        self.cooldown_timer = 0.0

        # Estado de la unidad
        self.target_position: Optional[np.ndarray] = None
        self.target_enemy: Optional['Unit'] = None

        # Sistema anti-atrapamiento
        self.stuck_counter = 0
        self.last_position = self.position.copy()

    @classmethod
    def create_from_config(cls,
                          unit_id: int,
                          team: int,
                          position: Tuple[float, float],
                          unit_type: str,
                          config_stats: Dict[str, Any]) -> 'Unit':
        """
        Crea una unidad desde configuración

        Args:
            unit_id: ID único de la unidad
            team: Equipo (0 o 1)
            position: Posición inicial
            unit_type: Tipo de unidad
            config_stats: Diccionario con stats desde configuración

        Returns:
            Instancia de Unit configurada
        """
        return cls(
            unit_id=unit_id,
            team=team,
            position=position,
            unit_type=unit_type,
            max_health=config_stats.get('max_health', 100.0),
            speed=config_stats.get('speed', 2.0),
            attack_damage=config_stats.get('attack_damage', 10.0),
            attack_range=config_stats.get('attack_range', 50.0),
            attack_cooldown=config_stats.get('attack_cooldown', 1.0),
            vision_range=config_stats.get('vision_range', 150.0)
        )

    @property
    def is_alive(self) -> bool:
        """Verifica si la unidad está viva"""
        return self.health > 0

    @property
    def health_percentage(self) -> float:
        """Retorna el porcentaje de salud (0-1)"""
        return max(0.0, self.health / self.max_health)

    def take_damage(self, damage: float) -> None:
        """Aplica daño a la unidad"""
        self.health = max(0.0, self.health - damage)

    def distance_to(self, other: 'Unit') -> float:
        """Calcula la distancia a otra unidad"""
        return np.linalg.norm(self.position - other.position)

    def distance_to_point(self, point: Tuple[float, float]) -> float:
        """Calcula la distancia a un punto"""
        return np.linalg.norm(self.position - np.array(point))

    def can_attack(self, target: 'Unit') -> bool:
        """Verifica si puede atacar a un objetivo"""
        if not target.is_alive or target.team == self.team:
            return False
        if self.cooldown_timer > 0:
            return False
        return self.distance_to(target) <= self.attack_range

    def attack(self, target: 'Unit') -> bool:
        """Ataca a un objetivo si es posible"""
        if self.can_attack(target):
            target.take_damage(self.attack_damage)
            self.cooldown_timer = self.attack_cooldown
            return True
        return False

    def move_towards(self, target_pos: np.ndarray, delta_time: float = 1.0, obstacle_manager=None, force_through: bool = False) -> None:
        """
        Mueve la unidad hacia una posición objetivo.

        Args:
            force_through: Si True, ignora obstáculos (usado en combate)
        """
        direction = target_pos - self.position
        distance = np.linalg.norm(direction)

        if distance > 0:
            direction = direction / distance
            move_distance = min(self.speed * delta_time, distance)
            new_position = self.position + direction * move_distance

            # Si está en modo forzado (combate), ignorar obstáculos
            if force_through or obstacle_manager is None:
                self.position = new_position
                self.stuck_counter = 0
                return

            # Radio MUCHO más pequeño para permitir movimiento
            unit_radius = 5 if self.unit_type == "scout" else (6 if self.unit_type == "soldier" else 7)

            # Detectar si está atrapado
            movement = np.linalg.norm(self.position - self.last_position)
            if movement < 0.3:  # Umbral más bajo
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0

            self.last_position = self.position.copy()

            # MUCHO más agresivo: solo 3 frames de espera
            if self.stuck_counter > 3:
                self.position = new_position
                self.stuck_counter = 0
                return

            if obstacle_manager.is_position_blocked(tuple(new_position), unit_radius):
                # Intentar ángulos alternativos
                angles_to_try = [22.5, -22.5, 45, -45, 67.5, -67.5, 90, -90,
                                112.5, -112.5, 135, -135, 157.5, -157.5, 180]

                for angle_offset in angles_to_try:
                    angle = np.arctan2(direction[1], direction[0]) + np.radians(angle_offset)
                    alt_direction = np.array([np.cos(angle), np.sin(angle)])
                    alt_position = self.position + alt_direction * move_distance
                    if not obstacle_manager.is_position_blocked(tuple(alt_position), unit_radius):
                        self.position = alt_position
                        self.stuck_counter = 0
                        return

                # No hay camino, pero no quedarse quieto - moverse de todos modos
                self.position = new_position
                return

            self.position = new_position
            self.stuck_counter = 0

    def update(self, delta_time: float = 1.0, obstacle_manager=None) -> None:
        """Actualiza el estado de la unidad"""
        # Actualizar cooldown de ataque
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - delta_time)

        # Moverse hacia la posición objetivo si existe
        if self.target_position is not None:
            self.move_towards(self.target_position, delta_time, obstacle_manager)

            # Si llegó al objetivo, limpiarlo
            if self.distance_to_point(self.target_position) < 1.0:
                self.target_position = None

    def set_move_target(self, position: Tuple[float, float]) -> None:
        """Establece una posición objetivo para moverse"""
        self.target_position = np.array(position, dtype=np.float32)
        self.target_enemy = None

    def set_attack_target(self, enemy: 'Unit') -> None:
        """Establece un enemigo objetivo para atacar"""
        self.target_enemy = enemy
        self.target_position = None

    def to_dict(self) -> dict:
        """Convierte la unidad a diccionario para observaciones"""
        return {
            'id': self.unit_id,
            'team': self.team,
            'type': self.unit_type,
            'position': self.position.copy(),
            'health': self.health,
            'health_pct': self.health_percentage,
            'cooldown': self.cooldown_timer,
            'vision_range': self.vision_range
        }
