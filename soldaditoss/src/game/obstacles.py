import numpy as np
import pygame
from typing import Tuple, List
import random


class Obstacle:
    """Obstáculo físico en el campo de batalla"""
    def __init__(self, position: Tuple[float, float], size: Tuple[float, float], obstacle_type: str):
        self.position = np.array(position, dtype=np.float32)
        self.size = size  # (width, height)
        self.type = obstacle_type  # 'tree', 'rock', 'bunker', 'building'
        self.blocking = True

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Verifica si un punto está dentro del obstáculo"""
        x, y = point
        half_w, half_h = self.size[0] / 2, self.size[1] / 2
        return (self.position[0] - half_w <= x <= self.position[0] + half_w and
                self.position[1] - half_h <= y <= self.position[1] + half_h)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Retorna (left, top, right, bottom)"""
        half_w, half_h = self.size[0] / 2, self.size[1] / 2
        return (
            self.position[0] - half_w,
            self.position[1] - half_h,
            self.position[0] + half_w,
            self.position[1] + half_h
        )

    def intersects_circle(self, center: Tuple[float, float], radius: float) -> bool:
        """Verifica si un círculo intersecta con el obstáculo"""
        # Encontrar el punto más cercano del rectángulo al centro del círculo
        left, top, right, bottom = self.get_bounds()

        closest_x = max(left, min(center[0], right))
        closest_y = max(top, min(center[1], bottom))

        # Calcular distancia del círculo al punto más cercano
        dx = center[0] - closest_x
        dy = center[1] - closest_y

        return (dx * dx + dy * dy) < (radius * radius)


class ObstacleManager:
    """Gestiona todos los obstáculos del mapa"""
    def __init__(self, map_size: Tuple[int, int]):
        self.map_size = map_size
        self.obstacles: List[Obstacle] = []

    def generate_obstacles(self, seed: int = 42):
        """Genera obstáculos procedurales para el mapa"""
        random.seed(seed)
        np.random.seed(seed)

        # Zonas de seguridad (spawn zones)
        safe_zone_blue = (0, 0, 250, self.map_size[1])
        safe_zone_red = (self.map_size[0] - 250, 0, self.map_size[0], self.map_size[1])

        # Árboles (pequeños, muchos)
        for _ in range(30):
            x = random.randint(300, self.map_size[0] - 300)
            y = random.randint(50, self.map_size[1] - 50)
            size = random.randint(20, 35)
            self.obstacles.append(Obstacle((x, y), (size, size), 'tree'))

        # Rocas grandes (medianas)
        for _ in range(15):
            x = random.randint(300, self.map_size[0] - 300)
            y = random.randint(50, self.map_size[1] - 50)
            width = random.randint(40, 70)
            height = random.randint(30, 50)
            self.obstacles.append(Obstacle((x, y), (width, height), 'rock'))

        # Edificios destruidos (grandes)
        for _ in range(8):
            x = random.randint(350, self.map_size[0] - 350)
            y = random.randint(100, self.map_size[1] - 100)
            width = random.randint(60, 100)
            height = random.randint(50, 80)
            self.obstacles.append(Obstacle((x, y), (width, height), 'building'))

        # Bunkers (fortificaciones)
        for _ in range(5):
            x = random.randint(400, self.map_size[0] - 400)
            y = random.randint(100, self.map_size[1] - 100)
            self.obstacles.append(Obstacle((x, y), (50, 50), 'bunker'))

    def is_position_blocked(self, position: Tuple[float, float], unit_radius: float = 12) -> bool:
        """Verifica si una posición está bloqueada por obstáculos"""
        for obstacle in self.obstacles:
            if obstacle.blocking and obstacle.intersects_circle(position, unit_radius):
                return True
        return False

    def find_clear_path(self, start: Tuple[float, float], end: Tuple[float, float],
                       unit_radius: float = 12) -> Tuple[float, float]:
        """
        Encuentra un punto intermedio para evitar obstáculos
        Pathfinding simple: si el destino está bloqueado, busca el punto más cercano libre
        """
        # Si el destino está libre, ir directamente
        if not self.is_position_blocked(end, unit_radius):
            return end

        # Buscar punto libre más cercano al destino
        search_radius = 50
        best_pos = end
        min_dist = float('inf')

        for angle in np.linspace(0, 2 * np.pi, 16):
            for r in range(20, search_radius, 10):
                test_x = end[0] + r * np.cos(angle)
                test_y = end[1] + r * np.sin(angle)
                test_pos = (test_x, test_y)

                # Verificar si está dentro del mapa
                if not (0 <= test_x < self.map_size[0] and 0 <= test_y < self.map_size[1]):
                    continue

                # Verificar si está libre
                if not self.is_position_blocked(test_pos, unit_radius):
                    dist = np.linalg.norm(np.array(test_pos) - np.array(start))
                    if dist < min_dist:
                        min_dist = dist
                        best_pos = test_pos

        return best_pos
