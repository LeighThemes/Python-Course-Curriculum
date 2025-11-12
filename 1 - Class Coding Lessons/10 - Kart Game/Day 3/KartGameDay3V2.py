import pygame
import math
import sys
import random
import colorsys
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
UI_HEIGHT = 0  # Height for the UI panel at the bottom

class GameState(Enum):
    MAIN_MENU = 0
    MODE_SELECT = 1
    COUNTDOWN = 2
    PLAYING = 3
    WON = 4
    GAME_OVER = 5

class GameMode(Enum):
    TIME_TRIAL = 0
    RACE = 1

class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (19, 29, 46)
    FLOOR_GRAY = (49, 184, 37)
    ROOF = (3, 223, 252)
    CAR_RED = (200, 0, 0)
    CAR_DARK_RED = (150, 0, 0)
    CAR_ACCENT = (255, 100, 100)
    GOLD = (255, 215, 0)
    PURPLE = (128, 0, 128)
    ORANGE = (255, 165, 0)

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass

class Collectable(GameObject):
    def __init__(self, x, y):
        # Initialize the collectable at the center of the grid cell
        super().__init__(x + 0.5, y + 0.5)
        
        # Visual and game mechanic properties
        self.size = 0.1                      # Visual size of the collectable
        self.collected = False              # Whether the collectable is currently collected
        self.respawn_timer = 0              # Timestamp of when it was collected
        self.respawn_delay = 15             # Time (in seconds) before it respawns
        self.boost_amount = 0.03            # Speed boost given to the player
        self.boost_duration = 3             # Duration of the speed boost in seconds
        self.glow_intensity = 0             # For pulsing glow effect
        self.glow_direction = 1             # Direction of glow intensity change (+1 or -1)
        
    def update(self, player, current_time):
        # Handle collectable respawn logic
        if self.collected:
            # Check if enough time has passed to respawn the collectable
            if current_time - self.respawn_timer >= self.respawn_delay:
                self.collected = False  # Make collectable active again
        else:
            # Animate pulsing glow by adjusting intensity
            self.glow_intensity += 0.05 * self.glow_direction
            if self.glow_intensity >= 1.0:
                self.glow_direction = -1  # Reverse to dimming
            elif self.glow_intensity <= 0.2:
                self.glow_direction = 1   # Reverse to brightening
                
            # Collision detection with player
            dx = self.x - player.x
            dy = self.y - player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # If player is close enough, collect the item
            if distance < 0.5:
                self.collected = True
                self.respawn_timer = current_time
                return True  # Notify game that boost should be applied
        return False  # No collection happened
    
    def draw(self, screen, player, renderer):
        # Don't draw if already collected
        if self.collected:
            return
            
        # Relative position to player
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        # Only render if within a certain distance (performance optimization)
        if dist_sq > (renderer.MAX_DEPTH * 0.7) ** 2:
            return
            
        # Compute angle from player to object relative to view direction
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        # Only draw if within player's field of view
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT - UI_HEIGHT) / (dist + 0.0001)  # Perspective projection
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)  # Horizontal screen position
            
            size = int(proj_height * self.size)  # Adjust size based on distance
            
            # Calculate rainbow glow color using HSV color cycling
            hue = (pygame.time.get_ticks() * 0.002) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, self.glow_intensity)
            rainbow_color = (int(r*255), int(g*255), int(b*255))
            
            # Draw the main collectable
            pygame.draw.rect(screen, rainbow_color, 
                             (screen_x - size//2, 
                              (HEIGHT - UI_HEIGHT)//2 - size//2, 
                              size, size))
            
            # Add a soft glow using transparent rectangles
            for i in range(3, 0, -1):
                glow_size = size + i * 3
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*rainbow_color, 30//i), 
                                 (0, 0, glow_size, glow_size))
                screen.blit(glow_surface, 
                            (screen_x - glow_size//2, 
                             (HEIGHT - UI_HEIGHT)//2 - glow_size//2))

class Wall(GameObject):
    def __init__(self, x, y, is_finish=False, is_lap_line=False):
        super().__init__(x, y)
        self.is_finish = is_finish
        self.is_lap_line = is_lap_line
        if is_finish:
            self.color = Color.GOLD
        elif is_lap_line:
            self.color = Color.GOLD
        elif (x + y) % 7 in [0, 3]:
            self.color = Color.WHITE
        else:
            self.color = Color.GRAY
    
    def draw(self, screen, ray, proj_height, depth_shade):
        proj_height *= 0.2
        base_color = self.color.value
        shaded_color = (
            max(0, min(255, base_color[0] * (depth_shade[0]/255))),
            max(0, min(255, base_color[1] * (depth_shade[1]/255))),
            max(0, min(255, base_color[2] * (depth_shade[2]/255)))
        )
        
        if self.is_finish or self.is_lap_line:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            pulse_color = (
                min(255, shaded_color[0] + int(pulse * 50)),
                min(255, shaded_color[1] + int(pulse * 50)),
                min(255, shaded_color[2] + int(pulse * 20)))
            if self.is_lap_line and ray % 2 == 0:
                pygame.draw.rect(screen, pulse_color, 
                               (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                                1, proj_height))
            elif self.is_finish:
                pygame.draw.rect(screen, pulse_color, 
                               (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                                1, proj_height))
            if random.random() < 0.02:
                sparkle_y = (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2 + random.random() * proj_height
                pygame.draw.circle(screen, (255, 255, 255), (ray, int(sparkle_y)), 2)
        else:
            pygame.draw.rect(screen, shaded_color, 
                           (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                            1, proj_height))

class NPCRacer(GameObject):
    def __init__(self, x, y, color):
        super().__init__(x + 0.5, y + 0.5)
        self.color = color
        self.speed = 0.5
        self.angle = 0
        self.size = 0.15  # Reduced size for better performance
        self.waypoints = []
        self.current_waypoint = 0
        self.laps = 1
        self.last_lap_crossing = 0
        self.acceleration = 0.0008
        self.deceleration = 0.0005
        self.max_speed = 0.5
        
    def update(self, game_map):
        if not self.waypoints:
            return
            
        target_x, target_y = self.waypoints[self.current_waypoint]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.8:
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            target_x, target_y = self.waypoints[self.current_waypoint]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
        
        target_angle = math.atan2(dy, dx)
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += min(max(angle_diff, -0.04), 0.04)
        
        turn_factor = 1.0 - min(abs(angle_diff) / math.pi, 0.7)
        if distance < 2.0:
            turn_factor *= distance / 2.0
            
        front_x = self.x + math.cos(self.angle) * 0.7
        front_y = self.y + math.sin(self.angle) * 0.7
        if game_map.get_cell(int(front_x), int(front_y)) == 1:
            self.speed = max(0.01, self.speed - self.deceleration * 3)
        else:
            self.speed = min(self.max_speed * turn_factor, self.speed + self.acceleration)
        
        move_x = math.cos(self.angle) * self.speed
        move_y = math.sin(self.angle) * self.speed
        
        if game_map.get_cell(int(self.x + move_x), int(self.y)) == 0:
            self.x += move_x
        if game_map.get_cell(int(self.x), int(self.y + move_y)) == 0:
            self.y += move_y
            
        self.check_lap_completion(game_map, pygame.time.get_ticks() / 1000)
    
    def check_lap_completion(self, game_map, current_time):
        if current_time - self.last_lap_crossing < 2.0:
            return False
            
        player_cell_x = int(self.x)
        player_cell_y = int(self.y)
        
        if (0 <= player_cell_x < len(game_map.map_data[0])) and (0 <= player_cell_y < len(game_map.map_data)):
            if game_map.map_data[player_cell_y][player_cell_x] == 3:
                self.last_lap_crossing = current_time
                self.laps += 1
                return True
        return False
    
    def draw(self, screen, player, renderer):
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        # Only draw NPCs that are reasonably close (optimization)
        if dist_sq > (renderer.MAX_DEPTH * 0.7) ** 2:  # 70% of max depth
            return
            
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT-UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            size = int(proj_height * self.size)  # Smaller size due to reduced self.size
            
            # Simplified drawing - fewer elements for better performance
            base_y = (HEIGHT-UI_HEIGHT)//2 + size//2 + int(proj_height * 0.3)
            pygame.draw.ellipse(screen, self.color, 
                              (screen_x - size//2, base_y - size//2, size, size//1.5))
            
            # Remove some decorative elements to improve performance
            front_x = screen_x + math.cos(self.angle) * size//2
            front_y = base_y + math.sin(self.angle) * size//4
            pygame.draw.line(screen, (255, 255, 255), (screen_x, base_y), (front_x, front_y), 1)  # Thinner line

class GameMap:
    def __init__(self, map_data, mode):
        self.map_data = map_data
        self.walls = {}
        self.finish_walls = []
        self.lap_lines = []
        self.npcs = []
        self.collectables = []
        self.mode = mode
        self.initialize_walls()
        if mode == GameMode.RACE:
            self.initialize_npcs(1.5, 1.5)  # Only initialize NPCs for race mode
            self.initialize_collectables()
    
    def initialize_collectables(self):
        # Find all empty cells that are adjacent to walls
        for y in range(1, len(self.map_data)-1):
            for x in range(1, len(self.map_data[0])-1):
                if self.map_data[y][x] == 0:  # Empty cell
                    # Check if adjacent to at least one wall
                    if (self.map_data[y-1][x] == 1 or self.map_data[y+1][x] == 1 or
                        self.map_data[y][x-1] == 1 or self.map_data[y][x+1] == 1):
                        # 20% chance to spawn a collectable in this cell
                        if random.random() < 0.05:
                            self.collectables.append(Collectable(x, y))
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    wall = Wall(x, y)
                    self.walls[(x, y)] = wall
                elif self.map_data[y][x] == 2:
                    if self.mode == GameMode.TIME_TRIAL:
                        wall = Wall(x, y, is_finish=True)
                        self.walls[(x, y)] = wall
                        self.finish_walls.append((x, y))
                elif self.map_data[y][x] == 3:
                    if self.mode == GameMode.RACE:
                        wall = Wall(x, y, is_lap_line=True)
                        self.walls[(x, y)] = wall
                        self.lap_lines.append((x, y))
    
    def initialize_npcs(self, player_start_x, player_start_y):
        """
        Initializes NPC racers with different characteristics and positions them near the player's start position.
        
        Args:
            player_start_x (float): The x-coordinate of the player's starting position
            player_start_y (float): The y-coordinate of the player's starting position
        """
        
        # Define color schemes for the NPCs (RGB tuples)
        colors = [
            (200, 50, 50),   # Red NPC (will be the fastest)
            (50, 50, 200),   # Blue NPC (medium speed)
            (50, 200, 50)    # Green NPC (slowest)
        ]
        
        # Define waypoints that form the racing track path
        # All NPCs will follow this same path
        waypoints = [
            (1.5, 1.5),     # First corner
            (18.5, 1.5),     # Second corner
            (18.5, 18.5),    # Third corner
            (1.5, 18.5),     # Fourth corner
            (1.5, 13.5),     # Start of inner track section
            (12.5, 13.5),    # Inner track turn
            (12.5, 11.5),    # Inner track straight
            (1.5, 11.5),     # Return to outer track
            (1.5, 1.5)       # Back to start/finish line
        ]
        
        # Spawn position offsets from the player's start position
        # Each NPC will be slightly offset to avoid stacking
        offsets = [(-0.8, -0.8), (-0.8, -0.8), (-0.8, -0.8)]  # All same offset in this case
        
        # Create up to 3 NPCs (or fewer if less than 3 colors available)
        for i in range(min(3, len(colors))):
            # Create a new NPC instance with:
            # - Position offset from player start
            # - Color from the colors list
            npc = NPCRacer(
                player_start_x + offsets[i][0],  # X position with offset
                player_start_y + offsets[i][1],  # Y position with offset
                colors[i]                       # NPC color
            )
            
            # Assign the waypoints to this NPC
            npc.waypoints = waypoints
            
            # Configure NPC behavior based on its color (position in the array)
            if i == 0:   # Red NPC (fastest)
                npc.max_speed = 0.47      # Highest top speed (33% faster than default)
                npc.acceleration = 0.001   # Quick acceleration
                npc.deceleration = 0.0003  # Minimal braking (coasts well)
                
            elif i == 1:  # Blue NPC (medium)
                npc.max_speed = 0.45      # Default speed
                npc.acceleration = 0.0008  # Default acceleration
                
            else:         # Green NPC (slowest)
                npc.max_speed = 0.43       # Lowest top speed (33% slower)
                npc.acceleration = 0.0006  # Slower acceleration
                npc.deceleration = 0.0007  # Stronger braking
                
            # Add the configured NPC to the game's NPC list
            self.npcs.append(npc)
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            if self.mode == GameMode.RACE and self.map_data[y][x] == 3:
                return 0
            return self.map_data[y][x]
        return None
    
    def is_visible(self, player_x, player_y, wall_x, wall_y):
        dx = wall_x - player_x
        dy = wall_y - player_y
        distance = math.sqrt(dx*dx + dy*dy)
        steps = max(1, int(distance))  # Reduced steps for performance
        
        for i in range(1, steps):
            test_x = int(player_x + dx * (i/steps))
            test_y = int(player_y + dy * (i/steps))
            if self.get_cell(test_x, test_y) == 1:
                return False
        return True

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0
        self.max_speed = 0.08
        self.original_max_speed = self.max_speed
        self.acceleration = 0.0015
        self.deceleration = 0.001
        self.rot_speed = 0.05
        self.momentum = 0
        self.laps = 1
        self.lap_times = []
        self.current_lap_start = 0
        self.last_lap_crossing = 0
        self.boost_timer = 0
        self.is_boosted = False
    
    def apply_boost(self, boost_amount, duration, current_time):
        self.max_speed = self.original_max_speed + boost_amount
        self.boost_timer = current_time + duration
        self.is_boosted = True
        
    def update_boost(self, current_time):
        if self.is_boosted and current_time > self.boost_timer:
            self.max_speed = self.original_max_speed
            self.is_boosted = False
    
    def update_movement(self, game_map):
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed
        
        if game_map.get_cell(int(new_x), int(new_y)) == 0:
            self.x = new_x
            self.y = new_y
    
    def accelerate(self):
        self.speed = min(self.max_speed, self.speed + self.acceleration)
    
    def brake(self):
        self.speed = max(0, self.speed - self.acceleration * 2)
    
    def rotate_left(self):
        self.angle -= self.rot_speed * (0.5 + self.speed / self.max_speed)
    
    def rotate_right(self):
        self.angle += self.rot_speed * (0.5 + self.speed / self.max_speed)
    
    def check_lap_completion(self, game_map, current_time):
        if game_map.mode == GameMode.TIME_TRIAL:
            player_cell_x = int(self.x)
            player_cell_y = int(self.y)
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = player_cell_x + dx
                    check_y = player_cell_y + dy
                    if (0 <= check_x < len(game_map.map_data[0])) and (0 <= check_y < len(game_map.map_data)):
                        if game_map.map_data[check_y][check_x] == 2:
                            if current_time - self.last_lap_crossing >= 1.0:
                                self.last_lap_crossing = current_time
                                return True
            return False
        
        elif game_map.mode == GameMode.RACE:
            if current_time - self.last_lap_crossing < 3.0:
                return False
                
            player_cell_x = int(self.x)
            player_cell_y = int(self.y)
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = player_cell_x + dx
                    check_y = player_cell_y + dy
                    if (0 <= check_x < len(game_map.map_data[0])) and (0 <= check_y < len(game_map.map_data)):
                        if game_map.map_data[check_y][check_x] == 3:
                            self.last_lap_crossing = current_time
                            if len(self.lap_times) < self.laps - 1:
                                self.lap_times.append(current_time - self.current_lap_start)
                                self.current_lap_start = current_time
                            self.laps += 1
                            return True
            return False

class Car:
    def __init__(self):
        self.width = 100
        self.height = 60
        self.hood_height = 20
        self.wheel_size = 15
        self.animation_offset = 0
        self.animation_speed = 0.1
        self.speed_effect = 0
    
    def update(self, player_speed, max_speed):
        speed_ratio = player_speed / max_speed
        self.animation_offset = math.sin(pygame.time.get_ticks() * self.animation_speed) * 2 * speed_ratio
        self.speed_effect = speed_ratio * 5
    
    def draw(self, screen):
        center_x = WIDTH // 2
        center_y = (HEIGHT - UI_HEIGHT) - 50 + self.animation_offset
        
        hover_height = 5 + math.sin(pygame.time.get_ticks() * 0.005) * 2
        glow_intensity = 100 + int(math.sin(pygame.time.get_ticks() * 0.01) * 50)
        engine_glow = (0, glow_intensity, 255, 150)
        
        chassis_points = [
            (center_x - self.width//2, center_y - self.height//4),
            (center_x - self.width//3, center_y - self.height//2),
            (center_x + self.width//3, center_y - self.height//2),
            (center_x + self.width//2, center_y - self.height//4),
            (center_x + self.width//2.5, center_y + self.height//3),
            (center_x - self.width//2.5, center_y + self.height//3)
        ]
        pygame.draw.polygon(screen, (200, 50, 50), chassis_points)
        
        canopy_points = [
            (center_x - self.width//3, center_y - self.height//2 + 5),
            (center_x - self.width//4, center_y - self.height//3),
            (center_x + self.width//4, center_y - self.height//3),
            (center_x + self.width//3, center_y - self.height//2 + 5)
        ]
        pygame.draw.polygon(screen, (50, 150, 255, 150), canopy_points)
        
        pygame.draw.circle(screen, engine_glow, 
                         (center_x, center_y + self.height//3), 
                         self.width//4, width=3)
        
        engine_positions = [
            (center_x - self.width//3, center_y + self.height//4),
            (center_x + self.width//3, center_y + self.height//4),
            (center_x - self.width//4, center_y + self.height//3),
            (center_x + self.width//4, center_y + self.height//3)
        ]
        for engine_x, engine_y in engine_positions:
            pygame.draw.circle(screen, (0, 150, 255), 
                             (engine_x, engine_y + hover_height), 
                             self.wheel_size//2)
        
        if self.speed_effect > 0.5:
            for i in range(int(self.speed_effect * 2)):
                offset = random.randint(0, 100)
                alpha = random.randint(100, 200)
                length = random.randint(30, 60)
                pygame.draw.line(screen, (0, 200, 255, alpha),
                               (center_x - self.width//2 - offset, center_y - self.height//1.5 - offset),
                               (center_x - self.width//2 - offset - length, center_y - self.height//2 - offset - length), 2)
                pygame.draw.line(screen, (0, 200, 255, alpha),
                               (center_x + self.width//2 + offset, center_y - self.height//1.5 - offset),
                               (center_x + self.width//2 + offset + length, center_y - self.height//2 - offset - length), 2)
        
        pygame.draw.polygon(screen, (0, 255, 255), chassis_points, 2)
        pygame.draw.polygon(screen, (0, 200, 255), canopy_points, 1)

class Renderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Racing Game")
        
        # Performance optimizations
        self.FOV = math.pi / 2
        self.HALF_FOV = self.FOV / 2
        self.NUM_RAYS = WIDTH // 2  # Reduced number of rays
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS
        self.MAX_DEPTH = 15  # Reduced draw distance
        
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 72)
        self.timer_font = pygame.font.Font(None, 48)
        self.speed_font = pygame.font.Font(None, 24)
        self.lap_font = pygame.font.Font(None, 36)
        self.position_font = pygame.font.Font(None, 28)
    
    def draw_floor_and_ceiling(self):
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2, WIDTH, (HEIGHT-UI_HEIGHT)//2))
        pygame.draw.rect(self.screen, Color.ROOF.value, (0, 0, WIDTH, (HEIGHT-UI_HEIGHT)//2))
    
    def cast_rays(self, player, game_map):
        visible_special_walls = set()
        visible_npcs = []
        
        if game_map.mode == GameMode.TIME_TRIAL:
            for wall_x, wall_y in game_map.finish_walls:
                if game_map.is_visible(player.x, player.y, wall_x, wall_y):
                    visible_special_walls.add((wall_x, wall_y))
        elif game_map.mode == GameMode.RACE:
            for wall_x, wall_y in game_map.lap_lines:
                if game_map.is_visible(player.x, player.y, wall_x, wall_y):
                    visible_special_walls.add((wall_x, wall_y))
        
        for ray in range(self.NUM_RAYS):
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            depth = 0
            hit_wall = False
            hit_special = False
            wall_x, wall_y = 0, 0

            while not hit_wall and depth < self.MAX_DEPTH:
                depth += 0.1
                
                test_x = int(player.x + depth * math.cos(ray_angle))
                test_y = int(player.y + depth * math.sin(ray_angle))

                if game_map.get_cell(test_x, test_y) is None:
                    hit_wall = True
                    depth = self.MAX_DEPTH
                elif game_map.get_cell(test_x, test_y) == 1:
                    hit_wall = True
                    wall_x, wall_y = test_x, test_y
                elif (game_map.get_cell(test_x, test_y) in [2, 3]) and (test_x, test_y) in visible_special_walls:
                    hit_wall = True
                    hit_special = True
                    wall_x, wall_y = test_x, test_y
                else:
                    # Only check for NPCs every few rays for performance
                    if ray % 3 == 0:  # Check every 3rd ray
                        for npc in game_map.npcs:
                            if (int(npc.x) == test_x and int(npc.y) == test_y and
                                (npc, depth) not in visible_npcs):
                                visible_npcs.append((npc, depth, ray_angle))

            if hit_wall and (game_map.get_cell(test_x, test_y) in [1, 2, 3]):
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001) * 0.95
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y) in game_map.walls:
                    if hit_special:
                        game_map.walls[(wall_x, wall_y)].draw(self.screen, ray*2, proj_height, depth_shade)
                    else:
                        game_map.walls[(wall_x, wall_y)].draw(self.screen, ray*2, proj_height, depth_shade)
        
        # Draw collectables after walls but before NPCs
        for collectable in game_map.collectables:
            collectable.draw(self.screen, player, self)
        
        # Draw NPCs after walls and collectables
        for npc, depth, angle in visible_npcs:
            npc.draw(self.screen, player, self)
    
    def draw_speedometer(self, speed, max_speed):
        center_x = WIDTH - 60
        center_y = HEIGHT - 60
        radius = 40
        
        speed_ratio = min(1, speed / max_speed)
        glow_intensity = int(100 + speed_ratio * 155)
        speed_color = (0, glow_intensity, 255)
        
        if speed_ratio >= 0.99:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            pulse_radius = int(radius + pulse * 15)
            glow_intensity = 255
            speed_color = (240, glow_intensity, 35)
        else:
            pulse_radius = radius
        
        for i in range(3, 0, -1):
            glow_radius = pulse_radius + i * 3
            glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            glow_alpha = 30//i
            if speed_ratio >= 0.99:
                glow_alpha = min(60, glow_alpha * 2)
            pygame.draw.circle(glow_surface, (*speed_color, glow_alpha), 
                             (glow_radius, glow_radius), glow_radius)
            self.screen.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius))
        
        pygame.draw.circle(self.screen, speed_color, (center_x, center_y), pulse_radius)
        pygame.draw.circle(self.screen, (0, 0, 50), (center_x, center_y), pulse_radius, 2)
        
        if speed_ratio >= 0.99:
            speed_font = pygame.font.Font(None, 28)
        else:
            speed_font = self.speed_font
            
        speed_text = speed_font.render(f"{int(speed_ratio * 100)}", True, Color.WHITE.value)
        text_rect = speed_text.get_rect(center=(center_x, center_y))
        self.screen.blit(speed_text, text_rect)
        
        if speed_ratio >= 0.99:
            label_y_offset = 25 + pulse * 2
        else:
            label_y_offset = 25
            
        label = self.speed_font.render("MPH", True, Color.WHITE.value)
        label_rect = label.get_rect(center=(center_x, center_y + label_y_offset))
        self.screen.blit(label, label_rect)
    
    def draw_race_positions(self, player, npcs):
        def get_distance(racer):
            lap_line_x, lap_line_y = 1.5, 18.5
            return math.sqrt((racer.x - lap_line_x)**2 + (racer.y - lap_line_y)**2)
        
        racers = []
        racers.append({
            'name': 'YOU',
            'laps': player.laps,
            'distance': get_distance(player),
            'color': Color.GOLD.value,
            'is_player': True
        })
        
        for i, npc in enumerate(npcs):
            racers.append({
                'name': f'RACER {i+1}',
                'laps': npc.laps,
                'distance': get_distance(npc),
                'color': npc.color,
                'is_player': False
            })
        
        racers.sort(key=lambda x: (-x['laps'], x['distance']))
        
        for i, racer in enumerate(racers[:4]):
            position_text = f"{i+1}. {racer['name']} - Lap {racer['laps']}"
            text_surf = self.position_font.render(position_text, True, racer['color'])
            self.screen.blit(text_surf, (20, 20 + i * 30))
    
    def draw_main_menu(self):
        for y in range(HEIGHT):
            shade = int(49 + (y / HEIGHT) * 100)
            pygame.draw.line(self.screen, (49, min(184, shade), 37), (0, y), (WIDTH, y))
        
        title_text = self.big_font.render("F-ZERO STYLE RACER", True, (200, 200, 255))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        
        car_x = WIDTH // 2
        car_y = HEIGHT // 2
        car_width = 120
        car_height = 70
        
        pygame.draw.ellipse(self.screen, (200, 50, 50), 
                          (car_x - car_width//2, car_y - car_height//2, car_width, car_height))
        
        pygame.draw.ellipse(self.screen, (50, 150, 255, 150), 
                          (car_x - car_width//3, car_y - car_height//3, car_width//1.5, car_height//2))
        
        pygame.draw.circle(self.screen, (0, 200, 255), 
                         (car_x + car_width//3, car_y), 15)
        
        button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
        pygame.draw.rect(self.screen, Color.PURPLE.value, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), button_rect, 3, border_radius=10)
        
        start_text = self.font.render("START", True, Color.WHITE.value)
        self.screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 15))
    
    def draw_mode_select(self):
        for y in range(HEIGHT):
            shade = int(49 + (y / HEIGHT) * 100)
            pygame.draw.line(self.screen, (49, min(184, shade), 37), (0, y), (WIDTH, y))
        
        title_text = self.big_font.render("SELECT MODE", True, (200, 200, 255))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
        
        time_trial_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 70, 300, 80)
        pygame.draw.rect(self.screen, Color.PURPLE.value, time_trial_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), time_trial_rect, 3, border_radius=10)
        
        time_trial_text = self.font.render("TIME TRIAL", True, Color.WHITE.value)
        time_trial_desc = self.speed_font.render("Race against the clock!", True, Color.WHITE.value)
        self.screen.blit(time_trial_text, (WIDTH//2 - time_trial_text.get_width()//2, HEIGHT//2 - 50))
        self.screen.blit(time_trial_desc, (WIDTH//2 - time_trial_desc.get_width()//2, HEIGHT//2 - 20))
        
        race_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 80)
        pygame.draw.rect(self.screen, Color.PURPLE.value, race_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), race_rect, 3, border_radius=10)
        
        race_text = self.font.render("RACE", True, Color.WHITE.value)
        race_desc = self.speed_font.render("3 laps against opponents!", True, Color.WHITE.value)
        self.screen.blit(race_text, (WIDTH//2 - race_text.get_width()//2, HEIGHT//2 + 50))
        self.screen.blit(race_desc, (WIDTH//2 - race_desc.get_width()//2, HEIGHT//2 + 80))
    
    def draw_countdown(self, count):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        count_text = self.big_font.render(str(count), True, (255, 255, 255))
        text_rect = count_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        size = 100 + (3 - count) * 20
        count_text = pygame.transform.scale(count_text, (size, size))
        text_rect = count_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        self.screen.blit(count_text, text_rect)
    
    def draw_timer(self, time_seconds, mode, current_lap=None, total_laps=None):
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds * 100) % 100)
        time_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        
        if mode == GameMode.RACE and current_lap is not None and total_laps is not None:
            time_text = f"Lap {current_lap}/{total_laps} - {time_text}"
        
        timer_surf = self.timer_font.render(time_text, True, Color.WHITE.value)
        timer_rect = timer_surf.get_rect(topright=(WIDTH - 20, 20))
        
        bg_rect = timer_rect.inflate(20, 10)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, bg_rect)
        
        self.screen.blit(timer_surf, timer_rect)
    
    def draw_lap_notification(self, lap_number):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        lap_number += 1
        
        lap_text = self.lap_font.render(f"LAP {lap_number}", True, Color.GOLD.value)
        text_rect = lap_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
        size = 1.0 + pulse * 0.2
        
        scaled_text = pygame.transform.scale(lap_text, 
                                          (int(lap_text.get_width() * size), 
                                           int(lap_text.get_height() * size)))
        scaled_rect = scaled_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        
        self.screen.blit(scaled_text, scaled_rect)
    
    def draw_end_screen(self, time_seconds, restart_rect, mode, player, npcs):
        # Create overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_y = HEIGHT//4 - 40
        if mode == GameMode.TIME_TRIAL:
            title_text = self.big_font.render("FINISHED!", True, Color.GOLD.value)
        else:
            title_text = self.big_font.render("RACE COMPLETE!", True, Color.GOLD.value)
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, title_y))
        
        # Time display
        time_y = title_y + 70
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds * 100) % 100)
        time_text = f"Time: {minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        time_surf = self.big_font.render(time_text, True, Color.WHITE.value)
        self.screen.blit(time_surf, (WIDTH//2 - time_surf.get_width()//2, time_y))
    
        # Final positions
        results = []
        results.append(("YOU", player.laps, Color.GOLD.value))
        
        # Only include NPCs if in race mode
        if mode == GameMode.RACE:
            for i, npc in enumerate(npcs):
                results.append((f"RACER {i+1}", npc.laps, npc.color))
        
        # Sort by laps (highest first)
        results.sort(key=lambda x: -x[1])
    
        # Display results
        results_start_y = time_y + 80
        results_title = self.font.render("FINAL RESULTS:", True, Color.WHITE.value)
        self.screen.blit(results_title, (WIDTH//2 - results_title.get_width()//2, results_start_y))
    
        # Show positions (up to 4)
        for i, (name, laps, color) in enumerate(results[:4]):
            pos_y = results_start_y + 40 + i * 35
            position_text = f"{i+1}. {name}"
            if mode == GameMode.RACE:
                position_text += f" - Lap {laps}"
            text_surf = self.font.render(position_text, True, color)
            self.screen.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, pos_y))
    
        # Restart button
        button_y = HEIGHT * 3//4 + 50
        restart_rect = pygame.Rect(WIDTH//2 - 150, button_y, 300, 50)  # Define the button rect at button_y
        
        # Draw button background and border
        pygame.draw.rect(self.screen, Color.PURPLE.value, restart_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), restart_rect, 3, border_radius=10)
        
        # Render and position text perfectly centered
        restart_text = self.font.render("Go To Main Menu", True, Color.WHITE.value)
        text_rect = restart_text.get_rect(center=restart_rect.center)  # Perfect centering
        self.screen.blit(restart_text, text_rect)


class Game:
    def __init__(self):
        self.initialize_game()
    
    def initialize_game(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU
        self.game_mode = None
        self.countdown_timer = 0
        self.countdown_value = 3
        self.race_start_time = 0
        self.race_time = 0
        self.lap_notification_timer = 0
        self.total_laps = 3
        self.restart_button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*3//4 + 50, 300, 50)
        
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        self.car = Car()
        self.game_map = None
    
    def initialize_time_trial_map(self):
        return GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ], GameMode.TIME_TRIAL)
    
    def initialize_race_map(self):
        return GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ], GameMode.RACE)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MAIN_MENU:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.state = GameState.MODE_SELECT
                elif self.state == GameState.MODE_SELECT:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    time_trial_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 70, 300, 80)
                    race_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 80)
                    
                    if time_trial_rect.collidepoint(mouse_x, mouse_y):
                        self.game_mode = GameMode.TIME_TRIAL
                        self.game_map = self.initialize_time_trial_map()
                        self.state = GameState.COUNTDOWN
                        self.countdown_timer = 0
                        self.countdown_value = 3
                        self.player = Player(1.5, 1.5)
                    elif race_rect.collidepoint(mouse_x, mouse_y):
                        self.game_mode = GameMode.RACE
                        self.game_map = self.initialize_race_map()
                        self.state = GameState.COUNTDOWN
                        self.countdown_timer = 0
                        self.countdown_value = 3
                        self.player = Player(1.5, 1.5)
                        self.player.laps = 1
                        self.player.lap_times = []
                elif self.state == GameState.WON:
                    if self.restart_button_rect.collidepoint(event.pos):
                        self.initialize_game()
    
    def update(self):
        if self.state == GameState.COUNTDOWN:
            self.countdown_timer += 1
            # Changed from 60 to 30 frames per count (half the time)
            if self.countdown_timer >= 30:  # Now counts down twice as fast
                self.countdown_timer = 0
                self.countdown_value -= 1
                if self.countdown_value <= 0:
                    self.state = GameState.PLAYING
                    self.race_start_time = pygame.time.get_ticks() / 1000
                    if self.game_mode == GameMode.RACE:
                        self.player.current_lap_start = self.race_start_time
        
        if self.state == GameState.PLAYING:
            current_time = pygame.time.get_ticks() / 1000
            self.race_time = current_time - self.race_start_time
            
            # Update collectables
            for collectable in self.game_map.collectables:
                if collectable.update(self.player, current_time):
                    self.player.apply_boost(collectable.boost_amount, 
                                          collectable.boost_duration, 
                                          current_time)
            
            # Update player boost status
            self.player.update_boost(current_time)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.player.accelerate()
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.player.brake()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.rotate_left()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.rotate_right()
            
            self.player.update_movement(self.game_map)
            self.car.update(self.player.speed, self.player.max_speed)
            
            if self.game_mode == GameMode.RACE:
                # Only update NPCs every other frame for better performance
                if pygame.time.get_ticks() % 2 == 0:
                    for npc in self.game_map.npcs:
                        npc.update(self.game_map)
            
            if self.player.check_lap_completion(self.game_map, current_time):
                if self.game_mode == GameMode.TIME_TRIAL:
                    self.state = GameState.WON
                elif self.game_mode == GameMode.RACE:
                    self.lap_notification_timer = 120
                    if self.player.laps >= self.total_laps + 1:
                        self.state = GameState.WON
            
            if self.lap_notification_timer > 0:
                self.lap_notification_timer -= 1
    
    def render(self):
        if self.state == GameState.MAIN_MENU:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_main_menu()
        elif self.state == GameState.MODE_SELECT:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_mode_select()
        elif self.state == GameState.COUNTDOWN:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            self.renderer.draw_countdown(self.countdown_value)
        elif self.state == GameState.PLAYING:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            if self.game_mode == GameMode.RACE:
                self.renderer.draw_timer(self.race_time, self.game_mode, 
                                       self.player.laps, self.total_laps)
                self.renderer.draw_race_positions(self.player, self.game_map.npcs)
                if self.lap_notification_timer > 0 and self.player.laps > 1:
                    self.renderer.draw_lap_notification(self.player.laps - 1)
            else:
                self.renderer.draw_timer(self.race_time, self.game_mode)
            
            self.renderer.draw_speedometer(self.player.speed, self.player.max_speed)
        elif self.state == GameState.WON:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            # Call end screen with proper parameters
            npcs_to_show = []
            if hasattr(self.game_map, 'npcs'):
                npcs_to_show = self.game_map.npcs
            
            self.renderer.draw_end_screen(
                time_seconds=self.race_time,
                restart_rect=self.restart_button_rect,
                mode=self.game_mode,
                player=self.player,
                npcs=npcs_to_show
            )
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    finally:
        pygame.quit()
        sys.exit()