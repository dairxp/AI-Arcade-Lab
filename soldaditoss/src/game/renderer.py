import pygame
import numpy as np
import math
import random
from typing import Optional, Tuple, List, Dict
from .game_state import GameState


class DamageNumber:
    """Números flotantes de daño"""
    def __init__(self, pos, damage):
        self.pos = np.array([pos[0], pos[1] - 20], dtype=np.float32)
        self.damage = int(damage)
        self.lifetime = 0.8
        self.age = 0.0
        self.velocity = np.array([random.uniform(-20, 20), -80], dtype=np.float32)

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt
        self.velocity *= 0.9
        return self.age < self.lifetime

    def draw(self, screen, font):
        alpha = 1.0 - (self.age / self.lifetime)
        if alpha > 0:
            color = (255, int(100 * alpha), int(100 * alpha))
            text = font.render(f"-{self.damage}", True, color)
            pos = (int(self.pos[0]), int(self.pos[1]))
            screen.blit(text, pos)


class Explosion:
    """Explosión mejorada con shockwave"""
    def __init__(self, pos, explosion_type="small"):
        self.pos = pos
        self.type = explosion_type
        self.lifetime = 0.8 if explosion_type == "large" else 0.5
        self.age = 0.0
        self.max_radius = 60 if explosion_type == "large" else 35
        self.shockwave_radius = 0

    def update(self, dt):
        self.age += dt
        self.shockwave_radius += 200 * dt
        return self.age < self.lifetime

    def draw(self, screen):
        progress = self.age / self.lifetime

        # Shockwave
        if progress < 0.4:
            wave_alpha = int(150 * (1 - progress / 0.4))
            wave_radius = int(self.shockwave_radius)
            if wave_radius < 100:
                surface = pygame.Surface((wave_radius*2, wave_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(surface, (255, 200, 100, wave_alpha),
                                 (wave_radius, wave_radius), wave_radius, 3)
                screen.blit(surface, (self.pos[0] - wave_radius, self.pos[1] - wave_radius))

        # Explosión principal
        if progress < 0.25:
            radius = int(self.max_radius * (progress / 0.25))
            color = (255, 255, 200)
            alpha = 255
        elif progress < 0.5:
            radius = self.max_radius
            color = (255, 150, 50)
            alpha = int(255 * (1 - (progress - 0.25) / 0.25))
        elif progress < 0.75:
            radius = int(self.max_radius * 0.9)
            color = (200, 80, 50)
            alpha = int(200 * (1 - (progress - 0.5) / 0.25))
        else:
            radius = int(self.max_radius * 0.7)
            color = (150, 50, 50)
            alpha = int(150 * (1 - (progress - 0.75) / 0.25))

        # Múltiples capas de explosión
        for i in range(4):
            r = radius - i * 8
            if r > 0:
                surface = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                a = max(0, alpha - i * 50)
                c = tuple(max(0, c - i * 20) for c in color)
                pygame.draw.circle(surface, (*c, a), (r, r), r)
                screen.blit(surface, (self.pos[0] - r, self.pos[1] - r))


class Projectile:
    """Proyectil mejorado con mejor física y visibilidad"""
    def __init__(self, start_pos, end_pos, projectile_type="bullet", color=(255, 255, 100), owner_unit=None):
        self.start_pos = np.array(start_pos, dtype=np.float32)
        self.end_pos = np.array(end_pos, dtype=np.float32)
        self.current_pos = self.start_pos.copy()
        self.projectile_type = projectile_type
        self.color = color
        self.lifetime = 0.8  # Más tiempo visible
        self.age = 0.0
        # Velocidades MUCHO más lentas para visibilidad
        self.speed = 400.0 if projectile_type == "bullet" else 250.0
        self.trail = []
        self.owner_unit = owner_unit

    def update(self, dt):
        self.age += dt
        old_pos = self.current_pos.copy()

        direction = self.end_pos - self.start_pos
        distance = np.linalg.norm(direction)

        if distance > 0:
            direction = direction / distance
            move_distance = self.speed * dt
            self.current_pos += direction * move_distance

        self.trail.append((int(old_pos[0]), int(old_pos[1])))
        if len(self.trail) > 20:  # Trail más largo para mejor visibilidad
            self.trail.pop(0)

        return self.age < self.lifetime and np.linalg.norm(self.current_pos - self.start_pos) < distance

    def draw(self, screen):
        pos = (int(self.current_pos[0]), int(self.current_pos[1]))

        # Trail ULTRA VISIBLE con gradiente mejorado
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int(255 * (i / len(self.trail)))  # Más opaco
                thickness = max(2, int(6 * (i / len(self.trail))))  # Más grueso
                color_with_alpha = (*self.color[:3], alpha)

                # Dibujar directamente sin crear surface cada vez (más eficiente)
                pygame.draw.line(screen, self.color[:3], self.trail[i], self.trail[i+1], thickness)

        # Proyectil MÁS GRANDE Y BRILLANTE
        if self.projectile_type == "bullet":
            # Halo brillante
            pygame.draw.circle(screen, (255, 255, 100), pos, 8)
            pygame.draw.circle(screen, self.color, pos, 6)
            pygame.draw.circle(screen, (255, 255, 255), pos, 4)
            pygame.draw.circle(screen, (255, 255, 220), pos, 2)
        elif self.projectile_type == "shell":
            # Proyectil de tanque más grande
            pygame.draw.circle(screen, (255, 200, 50), pos, 12)
            pygame.draw.circle(screen, self.color, pos, 10)
            pygame.draw.circle(screen, (255, 220, 100), pos, 7)
            angle = math.atan2(self.end_pos[1] - self.start_pos[1],
                             self.end_pos[0] - self.start_pos[0])
            end = (pos[0] + int(math.cos(angle) * 16),
                  pos[1] + int(math.sin(angle) * 16))
            pygame.draw.line(screen, (220, 120, 0), pos, end, 6)


class Particle:
    """Partícula mejorada"""
    def __init__(self, pos, velocity, color, lifetime=0.5, particle_type="fire", size=5):
        self.pos = np.array(pos, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.size = size
        self.particle_type = particle_type
        self.gravity = 200.0 if particle_type == "debris" else 0.0
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-360, 360)

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt
        self.velocity *= 0.90
        if self.gravity > 0:
            self.velocity[1] += self.gravity * dt
        self.rotation += self.rotation_speed * dt
        return self.age < self.lifetime

    def draw(self, screen):
        alpha = 1.0 - (self.age / self.lifetime)
        size = int(self.size * alpha)
        if size > 0:
            surface = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
            color = tuple(int(c * alpha) for c in self.color)

            if self.particle_type == "debris":
                # Partícula cuadrada rotada
                points = [
                    (size*2 + size, size*2),
                    (size*2, size*2 + size),
                    (size*2 - size, size*2),
                    (size*2, size*2 - size)
                ]
                pygame.draw.polygon(surface, color, points)
            else:
                pygame.draw.circle(surface, (*color, int(255 * alpha)), (size*2, size*2), size)

            screen.blit(surface, (int(self.pos[0]) - size*2, int(self.pos[1]) - size*2))


class SmokeParticle:
    """Humo mejorado"""
    def __init__(self, pos):
        self.pos = np.array(pos, dtype=np.float32)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(15, 40)
        self.velocity = np.array([math.cos(angle) * speed, math.sin(angle) * speed - 30])
        self.size = random.uniform(5, 10)
        self.max_size = random.uniform(20, 35)
        self.lifetime = random.uniform(1.2, 2.5)
        self.age = 0.0
        self.color = random.randint(70, 110)

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt
        self.velocity *= 0.92
        self.size = min(self.max_size, self.size + 10 * dt)
        return self.age < self.lifetime

    def draw(self, screen):
        alpha = int(140 * (1.0 - self.age / self.lifetime))
        if alpha > 0:
            surface = pygame.Surface((int(self.size)*2, int(self.size)*2), pygame.SRCALPHA)
            color = (self.color, self.color, self.color, alpha)
            pygame.draw.circle(surface, color, (int(self.size), int(self.size)), int(self.size))
            screen.blit(surface, (int(self.pos[0] - self.size), int(self.pos[1] - self.size)))


class MovementTrail:
    """Trail de movimiento de unidades"""
    def __init__(self, pos, color):
        self.pos = np.array(pos, dtype=np.float32)
        self.color = color
        self.lifetime = 0.4
        self.age = 0.0
        self.max_size = random.uniform(8, 12)
        self.size = self.max_size

    def update(self, dt):
        self.age += dt
        self.size = self.max_size * (1.0 - self.age / self.lifetime)
        return self.age < self.lifetime

    def draw(self, screen):
        alpha = int(100 * (1.0 - self.age / self.lifetime))
        if alpha > 0 and self.size > 0:
            surface = pygame.Surface((int(self.size)*2, int(self.size)*2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(surface, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
            screen.blit(surface, (int(self.pos[0] - self.size), int(self.pos[1] - self.size)))


class BloodParticle:
    """Partícula de sangre al recibir daño"""
    def __init__(self, pos, velocity):
        self.pos = np.array(pos, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)
        self.lifetime = random.uniform(0.3, 0.6)
        self.age = 0.0
        self.size = random.uniform(2, 5)
        self.color_base = random.randint(140, 180)  # Tonos de rojo

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt
        self.velocity[1] += 200 * dt  # Gravedad
        self.velocity *= 0.95  # Resistencia del aire
        return self.age < self.lifetime

    def draw(self, screen):
        alpha = int(255 * (1.0 - self.age / self.lifetime))
        if alpha > 0:
            surface = pygame.Surface((int(self.size)*2, int(self.size)*2), pygame.SRCALPHA)
            # Color rojo oscuro
            color = (self.color_base, int(self.color_base * 0.2), int(self.color_base * 0.2), alpha)
            pygame.draw.circle(surface, color, (int(self.size), int(self.size)), int(self.size))
            screen.blit(surface, (int(self.pos[0] - self.size), int(self.pos[1] - self.size)))


class Spark:
    """Chispas al impactar proyectiles"""
    def __init__(self, pos, color=(255, 200, 50)):
        self.pos = np.array(pos, dtype=np.float32)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)
        self.velocity = np.array([math.cos(angle) * speed, math.sin(angle) * speed])
        self.lifetime = random.uniform(0.1, 0.3)
        self.age = 0.0
        self.color = color

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt
        self.velocity *= 0.9
        return self.age < self.lifetime

    def draw(self, screen):
        alpha = int(255 * (1.0 - self.age / self.lifetime))
        if alpha > 0:
            surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*self.color, alpha), (2, 2), 2)
            screen.blit(surface, (int(self.pos[0]), int(self.pos[1])))


class BattleStats:
    """Sistema de estadísticas en tiempo real"""
    def __init__(self):
        self.damage_events = []  # (step, team, damage)
        self.kills = []  # (step, killer_team, victim_unit_id)
        self.team_damage = {0: 0, 1: 0}  # Total damage dealt by each team
        self.team_kills = {0: 0, 1: 0}
        self.unit_kills = {}  # unit_id -> kill count
        self.current_step = 0

    def update(self, game_state):
        """Actualizar estadísticas"""
        self.current_step = game_state.steps

    def register_damage(self, damage, attacker_team):
        """Registrar daño causado"""
        self.team_damage[attacker_team] += damage
        self.damage_events.append((self.current_step, attacker_team, damage))

        # Mantener solo eventos recientes (últimos 300 steps)
        self.damage_events = [(s, t, d) for s, t, d in self.damage_events if self.current_step - s < 300]

    def register_kill(self, killer_team, victim_unit_id):
        """Registrar kill"""
        self.team_kills[killer_team] += 1
        self.kills.append((self.current_step, killer_team, victim_unit_id))

        # Mantener solo kills recientes
        self.kills = [(s, t, v) for s, t, v in self.kills if self.current_step - s < 300]

    def get_dps(self, team, window_seconds=5.0):
        """Calcular DPS en los últimos N segundos"""
        # Asumiendo 60 FPS, 5 segundos = 300 steps
        window_steps = int(window_seconds * 60)
        recent_damage = sum(d for s, t, d in self.damage_events
                          if t == team and self.current_step - s < window_steps)
        return recent_damage / window_seconds if window_seconds > 0 else 0

    def reset(self):
        """Resetear estadísticas"""
        self.damage_events = []
        self.kills = []
        self.team_damage = {0: 0, 1: 0}
        self.team_kills = {0: 0, 1: 0}
        self.unit_kills = {}
        self.current_step = 0


class WeatherSystem:
    """Sistema climático - lluvia"""
    def __init__(self, screen_size, intensity=0.5):
        self.screen_size = screen_size
        self.intensity = intensity
        self.raindrops = []
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled

    def update(self, dt):
        if not self.enabled:
            return

        # Generar nuevas gotas
        num_new = int(self.intensity * 50)
        for _ in range(num_new):
            x = random.randint(0, self.screen_size[0])
            y = random.randint(-50, 0)
            self.raindrops.append([x, y, random.uniform(300, 500)])

        # Actualizar gotas existentes
        self.raindrops = [[x, y + speed * dt, speed]
                          for x, y, speed in self.raindrops
                          if y < self.screen_size[1]]

    def draw(self, screen):
        if not self.enabled:
            return

        for x, y, speed in self.raindrops:
            length = int(speed * 0.05)
            pygame.draw.line(screen, (180, 200, 220, 100),
                           (int(x), int(y)), (int(x), int(y) + length), 1)


class Minimap:
    """Minimapa táctico profesional"""
    def __init__(self, game_map_size, minimap_size=(200, 150), position=(20, 100)):
        self.game_map_size = game_map_size
        self.minimap_size = minimap_size
        self.position = position
        self.scale_x = minimap_size[0] / game_map_size[0]
        self.scale_y = minimap_size[1] / game_map_size[1]

    def world_to_minimap(self, pos):
        """Convierte coordenadas del mundo a minimapa"""
        x = int(pos[0] * self.scale_x)
        y = int(pos[1] * self.scale_y)
        return (self.position[0] + x, self.position[1] + y)

    def draw(self, screen, game_state):
        # Fondo oscuro
        bg = pygame.Surface(self.minimap_size, pygame.SRCALPHA)
        bg.fill((20, 30, 40, 220))
        screen.blit(bg, self.position)

        # Borde
        pygame.draw.rect(screen, (100, 150, 200),
                        (*self.position, *self.minimap_size), 2)

        # Obstáculos en minimap
        for obstacle in game_state.obstacle_manager.obstacles:
            mini_pos = self.world_to_minimap(obstacle.position)
            mini_w = max(2, int(obstacle.size[0] * self.scale_x))
            mini_h = max(2, int(obstacle.size[1] * self.scale_y))

            if obstacle.type in ['building', 'bunker']:
                color = (80, 80, 80)
            else:
                color = (60, 80, 60)

            pygame.draw.rect(screen, color,
                           (mini_pos[0] - mini_w//2, mini_pos[1] - mini_h//2,
                            mini_w, mini_h))

        # Unidades
        for unit in game_state.units:
            if unit.is_alive:
                mini_pos = self.world_to_minimap(unit.position)
                color = (80, 150, 255) if unit.team == 0 else (255, 80, 80)

                # Punto más grande según tipo
                if unit.unit_type == "tank":
                    size = 4
                elif unit.unit_type == "scout":
                    size = 2
                else:
                    size = 3

                pygame.draw.circle(screen, color, mini_pos, size)
                pygame.draw.circle(screen, (255, 255, 255), mini_pos, size, 1)

        # Título
        font = pygame.font.Font(None, 18)
        title = font.render("TACTICAL MAP", True, (200, 220, 255))
        screen.blit(title, (self.position[0] + 5, self.position[1] - 18))


class CoverSystem:
    """Sistema de cobertura táctica"""
    @staticmethod
    def get_cover_bonus(unit_pos, attacker_pos, obstacle_manager):
        """
        Calcula el bono de cobertura basado en obstáculos entre atacante y objetivo
        Retorna un multiplicador de daño (1.0 = sin cobertura, 0.5 = cobertura completa)
        """
        # Línea entre atacante y objetivo
        direction = np.array(unit_pos) - np.array(attacker_pos)
        distance = np.linalg.norm(direction)

        if distance < 1:
            return 1.0

        direction = direction / distance

        # Verificar intersecciones con obstáculos
        steps = int(distance / 10)  # Muestreo cada 10 píxeles

        for i in range(1, steps):
            check_pos = np.array(attacker_pos) + direction * (i * 10)

            for obstacle in obstacle_manager.obstacles:
                if obstacle.type in ['building', 'bunker', 'rock']:
                    # Verificar si el rayo pasa cerca del obstáculo
                    dist_to_obstacle = np.linalg.norm(check_pos - obstacle.position)

                    # Radio de cobertura basado en tamaño del obstáculo
                    cover_radius = max(obstacle.size) / 2

                    if dist_to_obstacle < cover_radius:
                        # Cobertura completa para bunkers y edificios
                        if obstacle.type in ['building', 'bunker']:
                            return 0.3  # 70% reducción de daño
                        else:  # rocks
                            return 0.5  # 50% reducción de daño

        return 1.0  # Sin cobertura


class GameRenderer:
    """Renderizador profesional de campo de batalla táctico"""

    # Colores mejorados
    GRASS_DARK = (50, 75, 35)
    GRASS_LIGHT = (65, 90, 45)
    GRASS_MED = (58, 82, 40)
    DIRT_DARK = (85, 65, 45)
    DIRT_LIGHT = (105, 85, 60)
    MUD_COLOR = (70, 55, 40)
    SKY = (120, 160, 200)

    TEAM_BLUE = (40, 110, 200)
    TEAM_RED = (200, 40, 40)

    def __init__(self, screen_size: Optional[Tuple[int, int]] = None, fps: int = 60):
        pygame.init()
        self.screen_size = screen_size
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.fps = fps

        # Fuentes
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_tiny = None

        # Efectos
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []
        self.smoke_particles: List[SmokeParticle] = []
        self.explosions: List[Explosion] = []
        self.damage_numbers: List[DamageNumber] = []
        self.movement_trails: List[MovementTrail] = []
        self.blood_particles: List[BloodParticle] = []
        self.sparks: List[Spark] = []

        # Terreno
        self.terrain_surface = None
        self.background_surface = None

        # Sistemas avanzados
        self.minimap = None
        self.weather = None
        self.cover_system = CoverSystem()
        self.battle_stats = BattleStats()  # NUEVO: Estadísticas en vivo

        # Camera shake
        self.camera_shake = 0.0
        self.camera_offset = [0, 0]

        # NUEVO: Modo espectador con cámara libre
        self.spectator_mode = False
        self.camera_zoom = 1.0
        self.camera_pan = [0, 0]  # Offset adicional de cámara
        self.following_unit = None  # Unidad a seguir
        self.camera_speed = 15  # Velocidad de pan

        # Estado de teclas para movimiento suave
        self.keys_pressed = set()

        # Tracking
        self.last_attack_check = {}
        self.last_health = {}  # Para detectar daño
        self.last_time = pygame.time.get_ticks()

        # Cache
        self.unit_sprites = {}
        self.show_ranges = False
        self.show_cover = False

    def initialize(self, game_state: GameState):
        if self.screen_size is None:
            self.screen_size = game_state.map_size

        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("⚔️ SOLDADITOS - Professional Tactical Battlefield Simulator")

        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self._generate_advanced_terrain()
        self._create_advanced_unit_sprites()

        # Inicializar sistemas
        self.minimap = Minimap(game_state.map_size, position=(20, 100))
        self.weather = WeatherSystem(self.screen_size, intensity=0.3)

        # Inicializar tracking de salud
        for unit in game_state.units:
            self.last_health[unit.unit_id] = unit.health

    def _generate_advanced_terrain(self):
        """Genera terreno multi-capa ultra realista"""
        self.background_surface = pygame.Surface(self.screen_size)
        self.background_surface.fill(self.SKY)

        self.terrain_surface = pygame.Surface(self.screen_size)

        # Capa base con Perlin-like noise
        random.seed(42)
        for y in range(0, self.screen_size[1], 15):
            for x in range(0, self.screen_size[0], 15):
                noise = random.randint(-15, 15)
                base_color = self.GRASS_DARK if (x // 30 + y // 30) % 2 == 0 else self.GRASS_LIGHT
                color = tuple(max(0, min(255, c + noise)) for c in base_color)
                pygame.draw.rect(self.terrain_surface, color, (x, y, 15, 15))

        # Parches de diferentes terrenos
        for _ in range(30):
            x = random.randint(50, self.screen_size[0] - 50)
            y = random.randint(50, self.screen_size[1] - 50)
            size = random.randint(40, 120)
            terrain_type = random.choice(['dirt', 'mud', 'grass'])

            if terrain_type == 'dirt':
                color = self.DIRT_DARK if random.random() < 0.5 else self.DIRT_LIGHT
            elif terrain_type == 'mud':
                color = self.MUD_COLOR
            else:
                color = self.GRASS_MED

            pygame.draw.ellipse(self.terrain_surface, color,
                              (x-size//2, y-size//2, size, size))

            # Textura interna
            for _ in range(10):
                tx = x + random.randint(-size//3, size//3)
                ty = y + random.randint(-size//3, size//3)
                tsize = random.randint(2, 6)
                tcolor = tuple(max(0, c + random.randint(-20, 20)) for c in color)
                pygame.draw.circle(self.terrain_surface, tcolor, (tx, ty), tsize)

        # Caminos de batalla
        for _ in range(5):
            x1 = random.randint(0, self.screen_size[0])
            y1 = random.randint(0, self.screen_size[1])
            x2 = random.randint(0, self.screen_size[0])
            y2 = random.randint(0, self.screen_size[1])
            pygame.draw.line(self.terrain_surface, self.DIRT_DARK,
                           (x1, y1), (x2, y2), random.randint(12, 20))
            pygame.draw.line(self.terrain_surface, self.MUD_COLOR,
                           (x1, y1), (x2, y2), random.randint(6, 10))

        # Pasto detallado
        for _ in range(400):
            x = random.randint(0, self.screen_size[0])
            y = random.randint(0, self.screen_size[1])
            length = random.randint(3, 8)
            angle = random.uniform(-0.3, 0.3)
            color = (random.randint(35, 65), random.randint(85, 115), random.randint(25, 45))
            end_x = x + int(math.sin(angle) * length)
            pygame.draw.line(self.terrain_surface, color, (x, y), (end_x, y + length), 1)

        # Pequeñas piedras
        for _ in range(100):
            x = random.randint(0, self.screen_size[0])
            y = random.randint(0, self.screen_size[1])
            size = random.randint(2, 5)
            color = (random.randint(80, 120), random.randint(80, 120), random.randint(80, 120))
            pygame.draw.circle(self.terrain_surface, color, (x, y), size)

    def _create_advanced_unit_sprites(self):
        """Crea sprites mejorados con más detalle"""
        for team in [0, 1]:
            base_color = self.TEAM_BLUE if team == 0 else self.TEAM_RED

            # SOLDIER - Mejorado
            soldier = pygame.Surface((28, 36), pygame.SRCALPHA)
            skin = (220, 180, 140)

            # Sombra del cuerpo
            shadow = pygame.Surface((28, 36), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 40), (8, 26, 12, 8))
            soldier.blit(shadow, (0, 0))

            # Piernas
            pygame.draw.line(soldier, base_color, (10, 24), (9, 34), 4)
            pygame.draw.line(soldier, base_color, (18, 24), (19, 34), 4)
            # Botas
            pygame.draw.circle(soldier, (40, 40, 40), (9, 34), 3)
            pygame.draw.circle(soldier, (40, 40, 40), (19, 34), 3)

            # Torso
            pygame.draw.ellipse(soldier, base_color, (8, 10, 12, 16))
            # Equipo en el torso
            pygame.draw.rect(soldier, tuple(int(c * 0.7) for c in base_color), (11, 14, 6, 8))

            # Brazos
            pygame.draw.line(soldier, base_color, (9, 14), (5, 22), 3)
            pygame.draw.line(soldier, base_color, (19, 14), (23, 22), 3)
            pygame.draw.circle(soldier, skin, (5, 22), 2)
            pygame.draw.circle(soldier, skin, (23, 22), 2)

            # Arma (rifle)
            pygame.draw.rect(soldier, (60, 60, 60), (21, 14, 5, 10))
            pygame.draw.rect(soldier, (40, 40, 40), (21, 20, 5, 2))

            # Cabeza
            pygame.draw.circle(soldier, skin, (14, 7), 6)
            # Casco
            pygame.draw.arc(soldier, (50, 50, 50), (8, 1, 12, 10), 0, math.pi, 3)
            # Ojos
            pygame.draw.circle(soldier, (0, 0, 0), (12, 7), 1)
            pygame.draw.circle(soldier, (0, 0, 0), (16, 7), 1)

            self.unit_sprites[f'soldier_{team}'] = soldier

            # TANK - Ultra detallado
            tank = pygame.Surface((48, 36), pygame.SRCALPHA)
            dark_color = tuple(int(c * 0.6) for c in base_color)

            # Orugas
            for x_offset in [4, 40]:
                pygame.draw.rect(tank, (30, 30, 30), (x_offset, 10, 6, 22))
                for y in range(12, 30, 4):
                    pygame.draw.circle(tank, (50, 50, 50), (x_offset + 3, y), 2)

            # Cuerpo principal
            pygame.draw.rect(tank, base_color, (8, 13, 32, 16), border_radius=2)
            pygame.draw.rect(tank, dark_color, (8, 13, 32, 16), 2, border_radius=2)

            # Detalles del cuerpo
            for i in range(3):
                x = 12 + i * 10
                pygame.draw.line(tank, dark_color, (x, 16), (x, 26), 1)

            # Torreta
            pygame.draw.ellipse(tank, base_color, (16, 12, 16, 14))
            pygame.draw.ellipse(tank, dark_color, (16, 12, 16, 14), 2)
            pygame.draw.circle(tank, (80, 80, 80), (24, 19), 3)

            # Cañón
            pygame.draw.rect(tank, (70, 70, 70), (30, 17, 16, 4))
            pygame.draw.rect(tank, (50, 50, 50), (30, 18, 16, 2))
            pygame.draw.circle(tank, (60, 60, 60), (45, 19), 2)

            # Escotilla
            pygame.draw.rect(tank, (90, 90, 90), (22, 15, 4, 3))

            self.unit_sprites[f'tank_{team}'] = tank

            # SCOUT - Más ágil y ligero
            scout = pygame.Surface((24, 32), pygame.SRCALPHA)

            # Piernas (en movimiento)
            pygame.draw.line(scout, base_color, (8, 20), (6, 30), 3)
            pygame.draw.line(scout, base_color, (16, 20), (18, 30), 3)
            pygame.draw.circle(scout, (40, 40, 40), (6, 30), 2)
            pygame.draw.circle(scout, (40, 40, 40), (18, 30), 2)

            # Torso delgado
            pygame.draw.ellipse(scout, base_color, (7, 8, 10, 14))

            # Brazos (corriendo)
            pygame.draw.line(scout, base_color, (7, 12), (3, 18), 2)
            pygame.draw.line(scout, base_color, (17, 12), (21, 18), 2)

            # Mochila ligera
            pygame.draw.rect(scout, (80, 80, 80), (10, 10, 4, 8), border_radius=1)

            # Cabeza
            pygame.draw.circle(scout, skin, (12, 5), 5)
            # Gorra
            pygame.draw.arc(scout, (70, 70, 70), (7, 0, 10, 8), 0, math.pi, 2)
            # Visor
            pygame.draw.rect(scout, (0, 0, 0), (9, 4, 6, 2))

            self.unit_sprites[f'scout_{team}'] = scout

    def render(self, game_state: GameState, show_ranges: bool = False):
        if self.screen is None:
            self.initialize(game_state)

        # Delta time
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        self.last_time = current_time

        # NUEVO: Actualizar cámara de espectador
        self._update_spectator_camera(game_state)

        # Actualizar camera shake
        if self.camera_shake > 0:
            self.camera_shake -= dt * 5
            shake_x = random.randint(-int(self.camera_shake * 10), int(self.camera_shake * 10))
            shake_y = random.randint(-int(self.camera_shake * 10), int(self.camera_shake * 10))
            # NUEVO: Incluir pan de espectador en el offset
            if self.spectator_mode:
                self.camera_offset = [shake_x + self.camera_pan[0], shake_y + self.camera_pan[1]]
            else:
                self.camera_offset = [shake_x, shake_y]
        else:
            # NUEVO: Incluir pan de espectador
            if self.spectator_mode:
                self.camera_offset = [self.camera_pan[0], self.camera_pan[1]]
            else:
                self.camera_offset = [0, 0]

        # Aplicar offset de cámara
        self.screen.blit(self.background_surface, self.camera_offset)
        self.screen.blit(self.terrain_surface, self.camera_offset)

        # Clima
        self.weather.update(dt)

        # Obstáculos
        self._draw_advanced_obstacles(game_state.obstacle_manager)

        # Sistema de cobertura (overlay)
        if self.show_cover:
            self._draw_cover_indicators(game_state)

        # Humo
        self.smoke_particles = [p for p in self.smoke_particles if p.update(dt)]
        for smoke in self.smoke_particles:
            smoke.draw(self.screen)

        # Detectar ataques y daño
        self._check_attacks_and_damage(game_state)

        # Proyectiles
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

        # Sombras de unidades
        for unit in game_state.units:
            if unit.is_alive:
                self._draw_advanced_unit_shadow(unit)

        # Proyectiles
        for projectile in self.projectiles:
            projectile.draw(self.screen)

        # Partículas
        self.particles = [p for p in self.particles if p.update(dt)]
        for particle in self.particles:
            particle.draw(self.screen)

        # NUEVO: Trails de movimiento (dibujar ANTES de las unidades)
        self.movement_trails = [t for t in self.movement_trails if t.update(dt)]
        for trail in self.movement_trails:
            trail.draw(self.screen)

        # NUEVO: Partículas de sangre
        self.blood_particles = [b for b in self.blood_particles if b.update(dt)]
        for blood in self.blood_particles:
            blood.draw(self.screen)

        # NUEVO: Chispas
        self.sparks = [s for s in self.sparks if s.update(dt)]
        for spark in self.sparks:
            spark.draw(self.screen)

        # Explosiones
        self.explosions = [e for e in self.explosions if e.update(dt)]
        for explosion in self.explosions:
            explosion.draw(self.screen)

        # Unidades
        for unit in game_state.units:
            if unit.is_alive:
                self._draw_advanced_unit(unit, show_ranges)

        # Números de daño
        self.damage_numbers = [d for d in self.damage_numbers if d.update(dt)]
        for dmg in self.damage_numbers:
            dmg.draw(self.screen, self.font_small)

        # Clima (lluvia sobre todo)
        self.weather.draw(self.screen)

        # NUEVO: Actualizar estadísticas
        self.battle_stats.update(game_state)

        # UI
        self._draw_advanced_ui(game_state)

        # NUEVO: Dibujar estadísticas en vivo
        self._draw_live_stats(game_state)

        # Minimapa
        self.minimap.draw(self.screen, game_state)

        pygame.display.flip()
        self.clock.tick(self.fps)

    def _draw_cover_indicators(self, game_state):
        """Dibuja indicadores visuales de cobertura"""
        for obstacle in game_state.obstacle_manager.obstacles:
            if obstacle.type in ['building', 'bunker', 'rock']:
                pos = (int(obstacle.position[0] + self.camera_offset[0]),
                      int(obstacle.position[1] + self.camera_offset[1]))
                radius = max(obstacle.size) // 2

                surface = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
                color = (50, 150, 255, 40) if obstacle.type in ['building', 'bunker'] else (100, 200, 100, 30)
                pygame.draw.circle(surface, color, (radius*2, radius*2), radius*2)
                self.screen.blit(surface, (pos[0] - radius*2, pos[1] - radius*2))

    def _draw_advanced_unit_shadow(self, unit):
        """Sombra dinámica mejorada"""
        shadow_offset = 5
        pos = (int(unit.position[0] + shadow_offset + self.camera_offset[0]),
               int(unit.position[1] + shadow_offset + self.camera_offset[1]))

        size_map = {"soldier": 10, "tank": 15, "scout": 8}
        size = size_map.get(unit.unit_type, 10)

        surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (0, 0, 0, 90), (0, 0, size*2, size*2))
        self.screen.blit(surface, (pos[0] - size, pos[1] - size))

    def _draw_advanced_unit(self, unit, show_ranges):
        """Dibuja unidad con todos los detalles"""
        pos = (unit.position[0] + self.camera_offset[0],
               unit.position[1] + self.camera_offset[1])
        sprite_key = f'{unit.unit_type}_{unit.team}'

        # Rango de ataque
        if show_ranges or self.show_ranges:
            surface = pygame.Surface((int(unit.attack_range)*2, int(unit.attack_range)*2), pygame.SRCALPHA)
            color = (100, 150, 255, 30) if unit.team == 0 else (255, 100, 100, 30)
            pygame.draw.circle(surface, color,
                             (int(unit.attack_range), int(unit.attack_range)),
                             int(unit.attack_range))
            self.screen.blit(surface,
                           (int(pos[0]) - int(unit.attack_range),
                            int(pos[1]) - int(unit.attack_range)))

        # Sprite
        if sprite_key in self.unit_sprites:
            sprite = self.unit_sprites[sprite_key].copy()

            # Rotación
            angle = 0
            if unit.target_enemy and unit.target_enemy.is_alive:
                dx = unit.target_enemy.position[0] - unit.position[0]
                dy = unit.target_enemy.position[1] - unit.position[1]
                angle = -math.degrees(math.atan2(dy, dx))
            elif unit.target_position is not None:
                dx = unit.target_position[0] - unit.position[0]
                dy = unit.target_position[1] - unit.position[1]
                angle = -math.degrees(math.atan2(dy, dx))

            if angle != 0:
                sprite = pygame.transform.rotate(sprite, angle)

            rect = sprite.get_rect(center=(int(pos[0]), int(pos[1])))
            self.screen.blit(sprite, rect)

            # Barra de salud
            self._draw_advanced_health_bar(unit, (int(pos[0]), int(pos[1])))

            # NUEVO: Indicador de tipo de unidad
            self._draw_unit_type_indicator(unit, (int(pos[0]), int(pos[1])))

            # Flash de disparo
            if unit.cooldown_timer > unit.attack_cooldown * 0.85:
                flash_size = 12
                surface = pygame.Surface((flash_size*2, flash_size*2), pygame.SRCALPHA)
                pygame.draw.circle(surface, (255, 255, 100, 180), (flash_size, flash_size), flash_size)
                pygame.draw.circle(surface, (255, 200, 0, 220), (flash_size, flash_size), flash_size//2)
                self.screen.blit(surface, (int(pos[0]) - flash_size, int(pos[1]) - flash_size))

    def _draw_advanced_health_bar(self, unit, pos):
        """Barra de salud profesional"""
        bar_width = 35
        bar_height = 5
        bar_x = pos[0] - bar_width // 2
        bar_y = pos[1] - 30

        # Fondo con borde
        pygame.draw.rect(self.screen, (30, 30, 30),
                        (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(self.screen, (20, 20, 20),
                        (bar_x, bar_y, bar_width, bar_height))

        # Salud
        health_width = int(bar_width * unit.health_percentage)
        if unit.health_percentage > 0.6:
            color = (60, 220, 60)
        elif unit.health_percentage > 0.3:
            color = (220, 220, 60)
        else:
            color = (220, 60, 60)

        if health_width > 0:
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, health_width, bar_height))
            # Brillo
            pygame.draw.rect(self.screen, tuple(min(255, c + 40) for c in color),
                           (bar_x, bar_y, health_width, 2))

        # Borde
        pygame.draw.rect(self.screen, (200, 200, 200),
                        (bar_x, bar_y, bar_width, bar_height), 1)

    def _draw_unit_type_indicator(self, unit, pos):
        """Dibuja icono/texto del tipo de unidad ARRIBA de la barra de salud"""
        # Iconos y colores por tipo
        type_config = {
            'soldier': {'icon': '⚔', 'color': (200, 200, 200), 'bg': (40, 40, 40)},
            'tank': {'icon': '🛡', 'color': (255, 180, 80), 'bg': (60, 40, 20)},
            'scout': {'icon': '👁', 'color': (100, 200, 255), 'bg': (20, 40, 60)}
        }

        config = type_config.get(unit.unit_type, type_config['soldier'])

        # Posición: encima de la barra de salud
        indicator_y = pos[1] - 45
        indicator_x = pos[0]

        # Fondo del indicador
        bg_size = 18
        bg_rect = pygame.Rect(indicator_x - bg_size//2, indicator_y - bg_size//2,
                             bg_size, bg_size)

        # Dibujar fondo con transparencia
        bg_surface = pygame.Surface((bg_size, bg_size), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (*config['bg'], 200), (0, 0, bg_size, bg_size), border_radius=3)
        self.screen.blit(bg_surface, bg_rect.topleft)

        # Borde de color del equipo
        team_color = (100, 180, 255) if unit.team == 0 else (255, 100, 100)
        pygame.draw.rect(self.screen, team_color, bg_rect, 2, border_radius=3)

        # Texto del icono
        icon_text = self.font_tiny.render(config['icon'], True, config['color'])
        icon_rect = icon_text.get_rect(center=(indicator_x, indicator_y))
        self.screen.blit(icon_text, icon_rect)

    def _draw_advanced_obstacles(self, obstacle_manager):
        """Obstáculos con sombras y profundidad mejoradas"""
        for obstacle in obstacle_manager.obstacles:
            pos = (int(obstacle.position[0] + self.camera_offset[0]),
                   int(obstacle.position[1] + self.camera_offset[1]))
            w, h = obstacle.size

            if obstacle.type == 'tree':
                # Sombra más realista
                shadow_surf = pygame.Surface((int(w*1.8), int(w*1.8)), pygame.SRCALPHA)
                for i in range(3):
                    alpha = 70 - i * 20
                    pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                      (i*4, i*4, int(w*1.8) - i*8, int(w*1.8) - i*8))
                self.screen.blit(shadow_surf, (pos[0] - w//2 + 6, pos[1] - w//2 + 6))

                # Tronco con textura
                trunk_w, trunk_h = int(w * 0.35), int(h * 0.65)
                trunk_color = (95, 63, 30)
                pygame.draw.rect(self.screen, trunk_color,
                               (pos[0] - trunk_w//2, pos[1] - trunk_h//2, trunk_w, trunk_h),
                               border_radius=2)
                pygame.draw.rect(self.screen, (75, 48, 22),
                               (pos[0] - trunk_w//2, pos[1] - trunk_h//2, trunk_w, trunk_h), 2)

                # Detalles del tronco
                for i in range(3):
                    y_pos = pos[1] - trunk_h//2 + (i + 1) * trunk_h // 4
                    pygame.draw.line(self.screen, (75, 48, 22),
                                   (pos[0] - trunk_w//2, y_pos),
                                   (pos[0] + trunk_w//2, y_pos), 1)

                # Copa con múltiples capas
                foliage_colors = [(30, 130, 30), (45, 150, 45), (55, 170, 105), (65, 190, 115)]
                for i, color in enumerate(foliage_colors):
                    offset_y = -h//2.5 - i * 4
                    radius = int(w * (0.65 - i * 0.08))
                    pygame.draw.circle(self.screen, color, (pos[0], int(pos[1] + offset_y)), radius)
                    # Borde más oscuro
                    pygame.draw.circle(self.screen, tuple(int(c * 0.6) for c in color),
                                     (pos[0], int(pos[1] + offset_y)), radius, 2)
                    # Highlights
                    highlight_pos = (pos[0] - radius//3, int(pos[1] + offset_y) - radius//3)
                    pygame.draw.circle(self.screen, tuple(min(255, int(c * 1.3)) for c in color),
                                     highlight_pos, radius//3)

            elif obstacle.type == 'rock':
                # Sombra de roca
                shadow_surf = pygame.Surface((int(w*1.3), int(h*1.3)), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect())
                self.screen.blit(shadow_surf, (pos[0] - w//2 + 5, pos[1] - h//2 + 5))

                # Forma irregular mejorada
                points = [
                    (pos[0], pos[1] - h//2 - 2),
                    (pos[0] + w//2 + 2, pos[1] - h//4),
                    (pos[0] + w//2, pos[1] + h//3),
                    (pos[0] + w//4, pos[1] + h//2 + 2),
                    (pos[0] - w//4, pos[1] + h//2),
                    (pos[0] - w//2 - 2, pos[1] + h//4),
                    (pos[0] - w//2, pos[1] - h//6),
                ]

                # Capas de color
                base_color = (100, 100, 100)
                pygame.draw.polygon(self.screen, base_color, points)
                pygame.draw.polygon(self.screen, (75, 75, 75), points, 3)

                # Textura y highlights
                highlight_color = (135, 135, 135)
                highlight_points = points[:4] + [(pos[0], pos[1])]
                pygame.draw.polygon(self.screen, highlight_color, highlight_points)

                # Grietas
                for _ in range(2):
                    start = random.choice(points)
                    end = random.choice(points)
                    pygame.draw.line(self.screen, (60, 60, 60), start, end, 1)

            elif obstacle.type == 'building':
                # Sombra de edificio
                pygame.draw.rect(self.screen, (0, 0, 0, 120),
                               (pos[0] - w//2 + 8, pos[1] - h//2 + 8, w, h))

                # Estructura principal
                wall_color = (135, 115, 95)
                pygame.draw.rect(self.screen, wall_color,
                               (pos[0] - w//2, pos[1] - h//2, w, h))

                # Daño de guerra (más detallado)
                damage_color = (95, 80, 65)
                random.seed(int(pos[0] + pos[1]))  # Consistente
                for _ in range(4):
                    dx = random.randint(-w//3, w//3)
                    dy = random.randint(-h//3, h//3)
                    size_w = random.randint(15, 25)
                    size_h = random.randint(15, 25)
                    pygame.draw.ellipse(self.screen, damage_color,
                                      (pos[0] + dx - size_w//2, pos[1] + dy - size_h//2,
                                       size_w, size_h))

                # Ventanas rotas
                for i in range(2):
                    for j in range(2):
                        wx = pos[0] - w//4 + i * w//2
                        wy = pos[1] - h//4 + j * h//3
                        # Marco
                        pygame.draw.rect(self.screen, (60, 50, 40),
                                       (wx - 10, wy - 12, 20, 24))
                        # Interior oscuro
                        pygame.draw.rect(self.screen, (30, 30, 30),
                                       (wx - 8, wy - 10, 16, 20))
                        # Vidrio roto
                        pygame.draw.line(self.screen, (50, 50, 50),
                                       (wx - 8, wy - 10), (wx + 8, wy + 10), 2)
                        pygame.draw.line(self.screen, (50, 50, 50),
                                       (wx + 8, wy - 10), (wx - 8, wy + 10), 2)

                # Borde y detalles
                pygame.draw.rect(self.screen, (95, 75, 55),
                               (pos[0] - w//2, pos[1] - h//2, w, h), 4)

                random.seed()  # Reset seed

            elif obstacle.type == 'bunker':
                # Sombra fuerte
                pygame.draw.rect(self.screen, (0, 0, 0, 140),
                               (pos[0] - w//2 + 6, pos[1] - h//2 + 6, w, h))

                # Base de concreto con gradiente
                concrete_base = (105, 120, 135)
                concrete_dark = (85, 100, 115)

                pygame.draw.rect(self.screen, concrete_base,
                               (pos[0] - w//2, pos[1] - h//2, w, h))

                # Sombra en la parte inferior
                pygame.draw.rect(self.screen, concrete_dark,
                               (pos[0] - w//2, pos[1] + h//4, w, h//4))

                # Borde fortificado
                pygame.draw.rect(self.screen, (75, 90, 105),
                               (pos[0] - w//2, pos[1] - h//2, w, h), 5)

                # Aspillera (abertura)
                slot_w, slot_h = w//2, h//5
                pygame.draw.rect(self.screen, (15, 15, 15),
                               (pos[0] - slot_w//2, pos[1] - slot_h//2, slot_w, slot_h))
                pygame.draw.rect(self.screen, (30, 30, 30),
                               (pos[0] - slot_w//2, pos[1] - slot_h//2, slot_w, slot_h), 2)

                # Bolsas de arena
                for i in range(4):
                    bag_x = pos[0] - w//2 + 10 + i * (w - 20) // 3
                    bag_y = pos[1] - h//2 - 6
                    pygame.draw.ellipse(self.screen, (150, 120, 75),
                                      (bag_x - 10, bag_y - 5, 20, 10))
                    pygame.draw.ellipse(self.screen, (120, 95, 60),
                                      (bag_x - 10, bag_y - 5, 20, 10), 2)
                    # Cuerda
                    pygame.draw.line(self.screen, (80, 60, 40),
                                   (bag_x - 7, bag_y), (bag_x + 7, bag_y), 1)

    def _check_attacks_and_damage(self, game_state):
        """Detecta ataques y cambios en salud"""
        for unit in game_state.units:
            if not unit.is_alive:
                continue

            unit_key = unit.unit_id

            # Detectar daño
            if unit_key in self.last_health:
                if unit.health < self.last_health[unit_key]:
                    damage = self.last_health[unit_key] - unit.health
                    self.damage_numbers.append(DamageNumber(unit.position, damage))

                    # NUEVO: Registrar daño en stats (enemigo causó el daño)
                    enemy_team = 1 - unit.team
                    self.battle_stats.register_damage(damage, enemy_team)

                    # Detectar kill
                    if unit.health <= 0 and unit.is_alive:  # Acaba de morir
                        self.battle_stats.register_kill(enemy_team, unit.unit_id)

                    # NUEVO: Partículas de sangre (BloodParticle)
                    num_blood = 12
                    for _ in range(num_blood):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(40, 120)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        self.blood_particles.append(BloodParticle(unit.position, velocity))

                    # NUEVO: Chispas al recibir daño
                    num_sparks = 6
                    for _ in range(num_sparks):
                        self.sparks.append(Spark(unit.position, color=(255, 220, 100)))

                    # Partículas de debris (mantener las originales)
                    for _ in range(5):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(30, 80)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        color = (200, 50, 50) if unit.unit_type != "tank" else (100, 100, 100)
                        self.particles.append(
                            Particle(unit.position, velocity, color,
                                   lifetime=0.4, particle_type="debris", size=3)
                        )

            # NUEVO: Generar trails cuando la unidad se mueve
            if hasattr(unit, 'last_position'):
                dist = np.linalg.norm(unit.position - unit.last_position)
                if dist > 5:  # Solo si se movió significativamente
                    color = self.TEAM_BLUE if unit.team == 0 else self.TEAM_RED
                    self.movement_trails.append(MovementTrail(unit.position, color))

            # Guardar posición para el siguiente frame
            unit.last_position = unit.position.copy()

            self.last_health[unit_key] = unit.health

            # Detectar ataques
            if unit.target_enemy and unit.target_enemy.is_alive:
                if unit.can_attack(unit.target_enemy):
                    if unit.cooldown_timer == unit.attack_cooldown:
                        self._create_epic_attack_effects(unit, unit.target_enemy, game_state)
                        self.last_attack_check[unit_key] = True
                    elif self.last_attack_check.get(unit_key, False):
                        self.last_attack_check[unit_key] = False

    def _create_epic_attack_effects(self, attacker, target, game_state):
        """Efectos de ataque épicos con sistema de cobertura"""
        start_pos = attacker.position.copy()
        end_pos = target.position.copy()

        # Calcular cobertura
        cover_multiplier = self.cover_system.get_cover_bonus(
            target.position, attacker.position, game_state.obstacle_manager
        )

        # Proyectil
        if attacker.unit_type == "tank":
            proj_type = "shell"
            color = (255, 130, 20)
        else:
            proj_type = "bullet"
            color = (255, 255, 180)

        self.projectiles.append(Projectile(start_pos, end_pos, proj_type, color, attacker))

        # Muzzle flash mejorado
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            color_var = random.choice([(255, 220, 120), (255, 180, 80), (255, 200, 100)])
            self.particles.append(
                Particle(start_pos, velocity, color_var,
                       lifetime=0.2, particle_type="fire", size=6)
            )

        # Humo del disparo
        for _ in range(4):
            self.smoke_particles.append(SmokeParticle(start_pos))

        # Impacto
        self._schedule_epic_impact(end_pos, attacker.unit_type, cover_multiplier)

        # Camera shake
        shake_intensity = 0.8 if attacker.unit_type == "tank" else 0.4
        self.camera_shake = max(self.camera_shake, shake_intensity)

    def _schedule_epic_impact(self, pos, weapon_type, cover_multiplier):
        """Impacto épico con indicador de cobertura"""
        explosion_type = "large" if weapon_type == "tank" else "small"
        self.explosions.append(Explosion(pos, explosion_type))

        # Más partículas para impactos grandes
        num_particles = 25 if weapon_type == "tank" else 18
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice([
                (255, 180, 50), (255, 120, 40), (200, 60, 60),
                (255, 220, 120), (180, 80, 40)
            ])
            self.particles.append(
                Particle(pos, velocity, color,
                       lifetime=0.6, particle_type="debris", size=random.randint(4, 8))
            )

        # Humo de impacto
        for _ in range(8):
            self.smoke_particles.append(SmokeParticle(pos))

        # Indicador visual de cobertura
        if cover_multiplier < 0.9:
            # Mostrar que hubo cobertura
            surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surface, (100, 200, 255, 100), (30, 30), 25, 4)
            # Este surface se mostraría temporalmente

    def _draw_advanced_ui(self, game_state):
        """UI profesional mejorada"""
        # Panel superior con gradiente
        panel = pygame.Surface((self.screen_size[0], 90), pygame.SRCALPHA)
        for i in range(90):
            alpha = 240 - i
            pygame.draw.line(panel, (15 + i//6, 20 + i//6, 25 + i//6, alpha),
                           (0, i), (self.screen_size[0], i))
        self.screen.blit(panel, (0, 0))

        # Información de equipos
        team0_units = len(game_state.get_units_by_team(0))
        team1_units = len(game_state.get_units_by_team(1))
        team0_health = int(game_state.get_total_health(0))
        team1_health = int(game_state.get_total_health(1))

        # Team Blue (izquierda)
        blue_icon = "🔵"
        blue_text = f"{blue_icon} BLUE FORCE"
        blue_surf = self.font_medium.render(blue_text, True, (120, 200, 255))
        self.screen.blit(blue_surf, (25, 12))

        blue_stats = f"Units: {team0_units} | Health: {team0_health}"
        blue_stats_surf = self.font_small.render(blue_stats, True, (150, 220, 255))
        self.screen.blit(blue_stats_surf, (25, 48))

        # Team Red (derecha)
        red_icon = "🔴"
        red_text = f"RED FORCE {red_icon}"
        red_surf = self.font_medium.render(red_text, True, (255, 120, 120))
        red_rect = red_surf.get_rect(topright=(self.screen_size[0] - 25, 12))
        self.screen.blit(red_surf, red_rect)

        red_stats = f"Units: {team1_units} | Health: {team1_health}"
        red_stats_surf = self.font_small.render(red_stats, True, (255, 150, 150))
        red_stats_rect = red_stats_surf.get_rect(topright=(self.screen_size[0] - 25, 48))
        self.screen.blit(red_stats_surf, red_stats_rect)

        # Centro - tiempo de batalla
        progress_pct = (game_state.steps / game_state.max_steps) * 100
        time_text = f"⚔️ COMBAT TIME: {game_state.steps}/{game_state.max_steps} ({progress_pct:.1f}%)"
        time_surf = self.font_small.render(time_text, True, (220, 220, 220))
        time_rect = time_surf.get_rect(center=(self.screen_size[0] // 2, 28))
        self.screen.blit(time_surf, time_rect)

        # Barras de progreso mejoradas
        bar_y = 60
        bar_width = 250
        bar_height = 18

        # Blue team bar
        total_health = team0_health + team1_health + 1
        blue_pct = team0_health / total_health

        pygame.draw.rect(self.screen, (30, 30, 30), (25, bar_y, bar_width, bar_height), border_radius=3)
        if blue_pct > 0:
            blue_bar_w = int(bar_width * blue_pct)
            pygame.draw.rect(self.screen, (40, 100, 180),
                           (25, bar_y, blue_bar_w, bar_height), border_radius=3)
            pygame.draw.rect(self.screen, (80, 150, 220),
                           (25, bar_y, blue_bar_w, 6), border_radius=3)
        pygame.draw.rect(self.screen, (120, 200, 255),
                        (25, bar_y, bar_width, bar_height), 3, border_radius=3)

        # Red team bar
        red_pct = team1_health / total_health
        red_bar_x = self.screen_size[0] - 275

        pygame.draw.rect(self.screen, (30, 30, 30),
                        (red_bar_x, bar_y, bar_width, bar_height), border_radius=3)
        if red_pct > 0:
            red_bar_w = int(bar_width * red_pct)
            pygame.draw.rect(self.screen, (180, 40, 40),
                           (red_bar_x + bar_width - red_bar_w, bar_y, red_bar_w, bar_height),
                           border_radius=3)
            pygame.draw.rect(self.screen, (220, 80, 80),
                           (red_bar_x + bar_width - red_bar_w, bar_y, red_bar_w, 6),
                           border_radius=3)
        pygame.draw.rect(self.screen, (255, 120, 120),
                        (red_bar_x, bar_y, bar_width, bar_height), 3, border_radius=3)

        # Mensaje de victoria
        if game_state.is_game_over():
            winner = game_state.get_winner()

            # Oscurecer pantalla
            overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))

            if winner is not None:
                team_name = "BLUE" if winner == 0 else "RED"
                color = (120, 200, 255) if winner == 0 else (255, 120, 120)
                icon = "🔵" if winner == 0 else "🔴"
                text = f"⚔️ {icon} {team_name} FORCE VICTORIOUS! {icon} ⚔️"
            else:
                text = "⚔️ TACTICAL STALEMATE ⚔️"
                color = (220, 220, 220)

            # Fondo del mensaje con gradiente
            msg_surf = self.font_large.render(text, True, color)
            msg_rect = msg_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))

            bg_rect = pygame.Rect(msg_rect.x - 40, msg_rect.y - 25,
                                 msg_rect.width + 80, msg_rect.height + 50)

            # Gradiente en el fondo
            for i in range(bg_rect.height):
                alpha = 200 + int(55 * (i / bg_rect.height))
                pygame.draw.line(self.screen, (15, 15, 15, alpha),
                               (bg_rect.x, bg_rect.y + i),
                               (bg_rect.x + bg_rect.width, bg_rect.y + i))

            pygame.draw.rect(self.screen, color, bg_rect, 5, border_radius=10)

            self.screen.blit(msg_surf, msg_rect)

            # Subtexto
            sub_text = "Press ESC to exit"
            sub_surf = self.font_small.render(sub_text, True, (180, 180, 180))
            sub_rect = sub_surf.get_rect(center=(self.screen_size[0] // 2, msg_rect.bottom + 40))
            self.screen.blit(sub_surf, sub_rect)

        # NUEVO: Indicador de modo espectador
        if self.spectator_mode:
            # Badge en la esquina superior derecha
            badge_x = self.screen_size[0] - 220
            badge_y = 100

            # Fondo
            badge = pygame.Surface((200, 90), pygame.SRCALPHA)
            pygame.draw.rect(badge, (30, 80, 120, 230), (0, 0, 200, 90), border_radius=8)
            pygame.draw.rect(badge, (100, 180, 255, 255), (0, 0, 200, 90), 2, border_radius=8)
            self.screen.blit(badge, (badge_x, badge_y))

            # Título
            title = self.font_small.render("📹 SPECTATOR MODE", True, (255, 255, 255))
            self.screen.blit(title, (badge_x + 10, badge_y + 8))

            # Controles
            controls = [
                "⌨️ ARROWS: Move camera",
                "🔍 +/-: Zoom",
                "🎯 SPACE: Follow unit",
                "⏹️ S: Stop following"
            ]

            for i, control in enumerate(controls):
                ctrl_surf = self.font_tiny.render(control, True, (200, 220, 255))
                self.screen.blit(ctrl_surf, (badge_x + 10, badge_y + 28 + i * 14))

    def _draw_live_stats(self, game_state):
        """Dibuja estadísticas en tiempo real"""
        stats = self.battle_stats

        # Panel de stats en la esquina inferior izquierda
        panel_x = 20
        panel_y = self.screen_size[1] - 180
        panel_width = 280
        panel_height = 160

        # Fondo semi-transparente
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 20, 30, 220), (0, 0, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(panel, (60, 100, 140, 255), (0, 0, panel_width, panel_height), 2, border_radius=10)
        self.screen.blit(panel, (panel_x, panel_y))

        # Título
        title = self.font_small.render("📊 LIVE STATS", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 15, panel_y + 10))

        # DPS por equipo
        dps_0 = stats.get_dps(0, window_seconds=5.0)
        dps_1 = stats.get_dps(1, window_seconds=5.0)

        # Team 0 DPS
        dps0_text = self.font_tiny.render(f"BLUE DPS: {dps_0:.1f}", True, (100, 180, 255))
        self.screen.blit(dps0_text, (panel_x + 15, panel_y + 40))

        # Barra de DPS
        dps_bar_width = 200
        max_dps = max(dps_0, dps_1, 50)  # Mínimo 50 para escala
        dps0_width = int((dps_0 / max_dps) * dps_bar_width)
        pygame.draw.rect(self.screen, (30, 30, 30), (panel_x + 15, panel_y + 58, dps_bar_width, 8), border_radius=4)
        if dps0_width > 0:
            pygame.draw.rect(self.screen, (60, 150, 255), (panel_x + 15, panel_y + 58, dps0_width, 8), border_radius=4)

        # Team 1 DPS
        dps1_text = self.font_tiny.render(f"RED DPS: {dps_1:.1f}", True, (255, 100, 100))
        self.screen.blit(dps1_text, (panel_x + 15, panel_y + 75))

        # Barra de DPS
        dps1_width = int((dps_1 / max_dps) * dps_bar_width)
        pygame.draw.rect(self.screen, (30, 30, 30), (panel_x + 15, panel_y + 93, dps_bar_width, 8), border_radius=4)
        if dps1_width > 0:
            pygame.draw.rect(self.screen, (255, 80, 80), (panel_x + 15, panel_y + 93, dps1_width, 8), border_radius=4)

        # Kills
        kills_text = self.font_tiny.render(f"KILLS - 🔵{stats.team_kills[0]} | 🔴{stats.team_kills[1]}",
                                         True, (220, 220, 220))
        self.screen.blit(kills_text, (panel_x + 15, panel_y + 115))

        # Total damage
        damage_text = self.font_tiny.render(f"DMG - 🔵{stats.team_damage[0]} | 🔴{stats.team_damage[1]}",
                                          True, (220, 220, 220))
        self.screen.blit(damage_text, (panel_x + 15, panel_y + 135))

    def _update_spectator_camera(self, game_state):
        """Actualiza la cámara del modo espectador"""
        if not self.spectator_mode:
            return

        # Movimiento con flechas
        pan_speed = self.camera_speed / self.camera_zoom
        if pygame.K_LEFT in self.keys_pressed:
            self.camera_pan[0] += pan_speed
        if pygame.K_RIGHT in self.keys_pressed:
            self.camera_pan[0] -= pan_speed
        if pygame.K_UP in self.keys_pressed:
            self.camera_pan[1] += pan_speed
        if pygame.K_DOWN in self.keys_pressed:
            self.camera_pan[1] -= pan_speed

        # Auto-seguir unidad si se presionó SPACE
        if self.following_unit is None:
            # Buscar unidad viva aleatoria para seguir
            alive_units = [u for u in game_state.units if u.is_alive]
            if alive_units:
                self.following_unit = alive_units[0]

        # Si estamos siguiendo una unidad, actualizar pan para centrarla
        if self.following_unit and self.following_unit.is_alive:
            # Calcular offset para centrar la unidad
            target_x = self.screen_size[0] // 2 - self.following_unit.position[0]
            target_y = self.screen_size[1] // 2 - self.following_unit.position[1]

            # Suavizar movimiento
            self.camera_pan[0] += (target_x - self.camera_pan[0]) * 0.1
            self.camera_pan[1] += (target_y - self.camera_pan[1]) * 0.1
        else:
            self.following_unit = None

    def close(self):
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                # Controles existentes
                if event.key == pygame.K_r:  # Toggle rangos
                    self.show_ranges = not self.show_ranges
                if event.key == pygame.K_c:  # Toggle cobertura
                    self.show_cover = not self.show_cover
                if event.key == pygame.K_w:  # Toggle clima
                    self.weather.toggle()

                # NUEVO: Controles de modo espectador
                if event.key == pygame.K_TAB:  # Toggle modo espectador
                    self.spectator_mode = not self.spectator_mode
                    if not self.spectator_mode:
                        # Resetear cámara al salir del modo espectador
                        self.camera_zoom = 1.0
                        self.camera_pan = [0, 0]
                        self.following_unit = None

                if self.spectator_mode:
                    if event.key == pygame.K_SPACE:  # Seguir siguiente unidad
                        self.following_unit = None  # Auto-seleccionar en update
                    if event.key == pygame.K_s:  # Detener seguimiento
                        self.following_unit = None
                    if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:  # Zoom in
                        self.camera_zoom = min(2.0, self.camera_zoom + 0.1)
                    if event.key == pygame.K_MINUS:  # Zoom out
                        self.camera_zoom = max(0.5, self.camera_zoom - 0.1)

            # Track teclas presionadas para movimiento suave
            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed.remove(event.key)

        return True
