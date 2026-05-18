import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from .entities import Unit
from .obstacles import ObstacleManager


class GameState:
    """Maneja el estado completo del juego RTS"""

    def __init__(self,
                 map_size: Tuple[int, int] = (800, 600),
                 units_per_team: int = 5,
                 unit_composition: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Args:
            map_size: Tamaño del mapa (ancho, alto)
            units_per_team: Número de unidades por equipo
            unit_composition: Lista con tipos de unidades (ej: ["soldier", "tank", "scout"])
            config: Diccionario de configuración con stats de unidades
        """
        self.map_size = map_size
        self.units_per_team = units_per_team
        self.config = config or {}

        # Si no hay composición especificada, usar soldados por defecto
        if unit_composition is None:
            unit_composition = ["soldier"] * units_per_team
        elif len(unit_composition) != units_per_team:
            raise ValueError(
                f"unit_composition debe tener {units_per_team} elementos, "
                f"tiene {len(unit_composition)}"
            )

        self.unit_composition = unit_composition
        self.units: List[Unit] = []
        self.steps = 0
        self.max_steps = 1000

        # Sistema de obstáculos
        self.obstacle_manager = ObstacleManager(map_size)
        self.obstacle_manager.generate_obstacles()

        self._initialize_units()

    def _get_formation_position(self, index: int, team: int, total_units: int) -> Tuple[float, float]:
        """
        Calcula la posición inicial de una unidad en formación táctica

        Para 5 unidades: columna vertical (backward compatible)
        Para 10+ unidades: formación en cuadrícula (filas y columnas)

        Args:
            index: Índice de la unidad (0 a total_units-1)
            team: Equipo (0 o 1)
            total_units: Total de unidades por equipo

        Returns:
            Tupla (x, y) con la posición
        """
        # Para 5 o menos unidades: formación vertical clásica
        if total_units <= 5:
            x = 100 if team == 0 else self.map_size[0] - 100
            y = (index + 1) * self.map_size[1] // (total_units + 1)
            return (x, y)

        # Para más unidades: formación en cuadrícula táctica
        # Calcular número de filas y columnas
        import math
        cols = math.ceil(math.sqrt(total_units))  # Ejemplo: 20 → 5 columnas
        rows = math.ceil(total_units / cols)       # Ejemplo: 20 → 4 filas

        row = index // cols
        col = index % cols

        # Espaciado entre unidades
        spacing_x = 60  # Separación horizontal
        spacing_y = 60  # Separación vertical

        # Centrar la formación verticalmente
        formation_height = (rows - 1) * spacing_y
        start_y = (self.map_size[1] - formation_height) // 2

        if team == 0:
            # Team 0 (Azul) - lado izquierdo
            base_x = 80
            x = base_x + col * spacing_x
            y = start_y + row * spacing_y
        else:
            # Team 1 (Rojo) - lado derecho
            base_x = self.map_size[0] - 80
            x = base_x - col * spacing_x
            y = start_y + row * spacing_y

        return (x, y)

    def _initialize_units(self) -> None:
        """Inicializa las unidades de ambos equipos con formaciones tácticas"""
        self.units = []
        unit_id = 0

        # Equipo 0 (Azul) - lado izquierdo
        for i in range(self.units_per_team):
            x, y = self._get_formation_position(i, team=0, total_units=self.units_per_team)
            unit_type = self.unit_composition[i]

            # Crear unidad con stats desde config si está disponible
            if self.config and 'unit_types' in self.config:
                unit_stats = self.config['unit_types'].get(unit_type, {})
                unit = Unit.create_from_config(
                    unit_id=unit_id,
                    team=0,
                    position=(x, y),
                    unit_type=unit_type,
                    config_stats=unit_stats
                )
            else:
                # Fallback a valores por defecto
                unit = Unit(
                    unit_id=unit_id,
                    team=0,
                    position=(x, y),
                    unit_type=unit_type
                )

            self.units.append(unit)
            unit_id += 1

        # Equipo 1 (Rojo) - lado derecho
        for i in range(self.units_per_team):
            x, y = self._get_formation_position(i, team=1, total_units=self.units_per_team)
            unit_type = self.unit_composition[i]

            # Crear unidad con stats desde config si está disponible
            if self.config and 'unit_types' in self.config:
                unit_stats = self.config['unit_types'].get(unit_type, {})
                unit = Unit.create_from_config(
                    unit_id=unit_id,
                    team=1,
                    position=(x, y),
                    unit_type=unit_type,
                    config_stats=unit_stats
                )
            else:
                # Fallback a valores por defecto
                unit = Unit(
                    unit_id=unit_id,
                    team=1,
                    position=(x, y),
                    unit_type=unit_type
                )

            self.units.append(unit)
            unit_id += 1

    def reset(self) -> None:
        """Reinicia el juego a su estado inicial"""
        self._initialize_units()
        self.steps = 0

    def get_units_by_team(self, team: int) -> List[Unit]:
        """Retorna todas las unidades vivas de un equipo"""
        return [u for u in self.units if u.team == team and u.is_alive]

    def get_enemy_units(self, team: int) -> List[Unit]:
        """Retorna todas las unidades enemigas vivas"""
        return [u for u in self.units if u.team != team and u.is_alive]

    def get_visible_enemies(self, team: int) -> List[Unit]:
        """
        Retorna enemigos visibles para un equipo según Fog of War

        Un enemigo es visible si está dentro del rango de visión
        de al menos una unidad aliada.

        Args:
            team: Equipo para el cual calcular visibilidad

        Returns:
            Lista de unidades enemigas visibles
        """
        my_units = self.get_units_by_team(team)
        enemies = self.get_enemy_units(team)

        visible_enemies = []
        for enemy in enemies:
            # Verificar si alguna unidad aliada puede ver este enemigo
            for unit in my_units:
                if unit.distance_to(enemy) <= unit.vision_range:
                    visible_enemies.append(enemy)
                    break  # No necesitamos seguir verificando

        return visible_enemies

    def update(self, delta_time: float = 1.0) -> None:
        """Actualiza el estado del juego"""
        self.steps += 1

        # Actualizar todas las unidades
        for unit in self.units:
            if unit.is_alive:
                unit.update(delta_time, self.obstacle_manager)

        # Procesar ataques automáticos a objetivos
        for unit in self.units:
            if unit.is_alive and unit.target_enemy is not None:
                if unit.target_enemy.is_alive:
                    # Intentar atacar si está en rango
                    if unit.can_attack(unit.target_enemy):
                        unit.attack(unit.target_enemy)
                    else:
                        # Distancia al enemigo
                        dist_to_enemy = unit.distance_to(unit.target_enemy)

                        # Si el enemigo está "cerca" (dentro de 1.5x el rango de ataque),
                        # FORZAR movimiento ignorando obstáculos para garantizar combate
                        force_through = dist_to_enemy < (unit.attack_range * 1.5)

                        unit.move_towards(unit.target_enemy.position, delta_time,
                                        self.obstacle_manager, force_through=force_through)
                else:
                    # El objetivo murió, limpiar
                    unit.target_enemy = None

    def is_game_over(self) -> bool:
        """Verifica si el juego terminó"""
        team0_alive = len(self.get_units_by_team(0)) > 0
        team1_alive = len(self.get_units_by_team(1)) > 0

        # Juego termina si un equipo fue eliminado o se alcanzó el límite de steps
        return not team0_alive or not team1_alive or self.steps >= self.max_steps

    def get_winner(self) -> Optional[int]:
        """
        Retorna el equipo ganador o None si es empate

        Returns:
            0 o 1 para el equipo ganador, None si es empate
        """
        team0_alive = len(self.get_units_by_team(0))
        team1_alive = len(self.get_units_by_team(1))

        if team0_alive > team1_alive:
            return 0
        elif team1_alive > team0_alive:
            return 1
        else:
            return None  # Empate

    def get_total_health(self, team: int) -> float:
        """Retorna la salud total de un equipo"""
        return sum(u.health for u in self.get_units_by_team(team))

    def get_max_health(self, team: int) -> float:
        """Retorna la salud máxima posible de un equipo (suma de max_health de todas las unidades)"""
        return sum(u.max_health for u in self.get_units_by_team(team))

    def get_state_dict(self) -> Dict:
        """Retorna el estado del juego como diccionario"""
        return {
            'steps': self.steps,
            'max_steps': self.max_steps,
            'units': [u.to_dict() for u in self.units if u.is_alive],
            'team0_units': len(self.get_units_by_team(0)),
            'team1_units': len(self.get_units_by_team(1)),
            'team0_health': self.get_total_health(0),
            'team1_health': self.get_total_health(1)
        }
