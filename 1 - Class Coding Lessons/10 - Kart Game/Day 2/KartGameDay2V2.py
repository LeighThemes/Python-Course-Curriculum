import pygame
import math
import sys
import random
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
    GRAY = (19, 29, 46)  # Wall color
    FLOOR_GRAY = (49, 184, 37)  # Track color
    ROOF = (3, 223, 252)    # Sky color
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

class Wall(GameObject):
    def __init__(self, x, y, is_finish=False, is_lap_line=False):
        super().__init__(x, y)
        self.is_finish = is_finish
        self.is_lap_line = is_lap_line
        if is_finish:
            self.color = Color.GOLD
        elif is_lap_line:
            self.color = Color.GOLD
        elif (x + y) % 7 in [0, 3]:  # Alternate pattern for visual interest
            self.color = Color.WHITE
        else:
            self.color = Color.GRAY
    
    def draw(self, screen, ray, proj_height, depth_shade):
        # Make walls 80% smaller by reducing their height
        proj_height *= 0.2  # 20% of original height (80% reduction)
        
        # Use the wall's color but apply depth shading
        base_color = self.color.value
        # Blend with depth shading
        shaded_color = (
            max(0, min(255, base_color[0] * (depth_shade[0]/255))),
            max(0, min(255, base_color[1] * (depth_shade[1]/255))),
            max(0, min(255, base_color[2] * (depth_shade[2]/255)))
        )
        
        # Add special effect for finish wall or lap line
        if self.is_finish or self.is_lap_line:
            # Pulsing gold effect
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            pulse_color = (
                min(255, shaded_color[0] + int(pulse * 50)),
                min(255, shaded_color[1] + int(pulse * 50)),
                min(255, shaded_color[2] + int(pulse * 20))
            )
            # Draw as thin lines (every other ray) for lap lines
            if self.is_lap_line and ray % 2 == 0:
                pygame.draw.rect(screen, pulse_color, 
                               (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                                1, proj_height))
            
            # For finish walls, draw normally
            elif self.is_finish:
                pygame.draw.rect(screen, pulse_color, 
                               (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                                1, proj_height))
            
            # Add sparkle effect occasionally
            if random.random() < 0.02:
                sparkle_y = (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2 + random.random() * proj_height
                pygame.draw.circle(screen, (255, 255, 255), (ray, int(sparkle_y)), 2)
        else:
            pygame.draw.rect(screen, shaded_color, 
                           (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                            1, proj_height))

class GameMap:
    def __init__(self, map_data, mode):
        self.map_data = map_data
        self.walls = {}
        self.finish_walls = []  # Track finish walls separately
        self.lap_lines = []     # Track lap lines separately
        self.mode = mode
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    wall = Wall(x, y)
                    self.walls[(x, y)] = wall
                elif self.map_data[y][x] == 2:  # Finish wall (time trial)
                    if self.mode == GameMode.TIME_TRIAL:
                        wall = Wall(x, y, is_finish=True)
                        self.walls[(x, y)] = wall
                        self.finish_walls.append((x, y))
                elif self.map_data[y][x] == 3:  # Lap line (race mode)
                    if self.mode == GameMode.RACE:
                        wall = Wall(x, y, is_lap_line=True)
                        self.walls[(x, y)] = wall
                        self.lap_lines.append((x, y))
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            # In race mode, lap lines (3) are passable
            if self.mode == GameMode.RACE and self.map_data[y][x] == 3:
                return 0  # Treat as empty space for collision
            return self.map_data[y][x]
        return None
    
    def is_visible(self, player_x, player_y, wall_x, wall_y):
        """Check if there's a clear line of sight from player to wall"""
        dx = wall_x - player_x
        dy = wall_y - player_y
        distance = math.sqrt(dx*dx + dy*dy)
        steps = max(abs(dx), abs(dy)) * 2  # Number of steps to check
        
        for i in range(1, int(steps)):
            test_x = player_x + dx * (i/steps)
            test_y = player_y + dy * (i/steps)
            cell_value = self.get_cell(int(test_x), int(test_y))
            if cell_value == 1:  # Regular wall blocks view
                return False
        return True

class Player(GameObject):
    def __init__(self, x, y):
        # Initialize the player object with position (x, y)
        super().__init__(x, y)  # Call parent class (GameObject) constructor
        self.angle = 0         # Current facing direction (in radians)
        self.speed = 0         # Current movement speed
        self.max_speed = 0.08  # Maximum allowed speed
        self.acceleration = 0.0015  # How quickly the player speeds up
        self.deceleration = 0.001    # How quickly the player slows down naturally
        self.rot_speed = 0.05  # Base rotation speed
        self.momentum = 0      # Momentum factor (currently unused in update_movement)
        self.laps = 1          # Number of laps completed (race mode) - start at 1
        self.lap_times = []    # Times for each lap (race mode)
        self.current_lap_start = 0  # Time when current lap started (race mode)
        self.last_lap_crossing = 0  # Time of last lap crossing (to prevent multiple triggers)
    
    def update_movement(self, game_map):
        # Updates player position based on current movement state
        
        # Apply natural deceleration when moving forward
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        
        # Calculate new position based on current angle and speed
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed
        
        # Only move if the new position is not blocked (cell value 0 means walkable)
        if game_map.get_cell(int(new_x), int(new_y)) == 0:
            self.x = new_x
            self.y = new_y
    
    def accelerate(self):
        # Increase speed up to max_speed when accelerating
        self.speed = min(self.max_speed, self.speed + self.acceleration)
    
    def brake(self):
        # Decrease speed (twice as fast as normal acceleration) when braking
        self.speed = max(0, self.speed - self.acceleration * 2)
    
    def rotate_left(self):
        # Rotate counter-clockwise (left)
        # Rotation speed increases with current movement speed (0.5-1.5x base speed)
        self.angle -= self.rot_speed * (0.5 + self.speed / self.max_speed)
    
    def rotate_right(self):
        # Rotate clockwise (right)
        # Rotation speed increases with current movement speed (0.5-1.5x base speed)
        self.angle += self.rot_speed * (0.5 + self.speed / self.max_speed)
    
    def check_lap_completion(self, game_map, current_time):
        # For time trial mode - check finish wall
        if game_map.mode == GameMode.TIME_TRIAL:
            player_cell_x = int(self.x)
            player_cell_y = int(self.y)
            
            # Check current cell and adjacent cells
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = player_cell_x + dx
                    check_y = player_cell_y + dy
                    if (0 <= check_x < len(game_map.map_data[0])) and (0 <= check_y < len(game_map.map_data)):
                        if game_map.map_data[check_y][check_x] == 2:  # Finish wall
                            # Remove direction check and just check cooldown
                            if current_time - self.last_lap_crossing >= 1.0:  # 1 second cooldown
                                self.last_lap_crossing = current_time
                                return True
            return False
        
        # For race mode - check lap line
        elif game_map.mode == GameMode.RACE:
            # Prevent multiple triggers within 1 second
            if current_time - self.last_lap_crossing < 3.0:
                return False
                
            player_cell_x = int(self.x)
            player_cell_y = int(self.y)
            
            # Check current cell and adjacent cells
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = player_cell_x + dx
                    check_y = player_cell_y + dy
                    if (0 <= check_x < len(game_map.map_data[0])) and (0 <= check_y < len(game_map.map_data)):
                        if game_map.map_data[check_y][check_x] == 3:  # Lap line
                            # Remove direction check and just check cooldown
                            self.last_lap_crossing = current_time
                            if len(self.lap_times) < self.laps - 1:  # New lap
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
        # Animate the car based on speed
        speed_ratio = player_speed / max_speed
        self.animation_offset = math.sin(pygame.time.get_ticks() * self.animation_speed) * 2 * speed_ratio
        self.speed_effect = speed_ratio * 5  # For visual speed effects
    
    def draw(self, screen):
        center_x = WIDTH // 2
        center_y = (HEIGHT - UI_HEIGHT) - 50 + self.animation_offset
        
        # Hover effect parameters
        hover_height = 5 + math.sin(pygame.time.get_ticks() * 0.005) * 2
        glow_intensity = 100 + int(math.sin(pygame.time.get_ticks() * 0.01) * 50)
        engine_glow = (0, glow_intensity, 255, 150)
        
        # Main chassis (sleek, angular design)
        chassis_points = [
            (center_x - self.width//2, center_y - self.height//4),
            (center_x - self.width//3, center_y - self.height//2),
            (center_x + self.width//3, center_y - self.height//2),
            (center_x + self.width//2, center_y - self.height//4),
            (center_x + self.width//2.5, center_y + self.height//3),
            (center_x - self.width//2.5, center_y + self.height//3)
        ]
        pygame.draw.polygon(screen, (200, 50, 50), chassis_points)
        
        # Cockpit canopy (blue glass)
        canopy_points = [
            (center_x - self.width//3, center_y - self.height//2 + 5),
            (center_x - self.width//4, center_y - self.height//3),
            (center_x + self.width//4, center_y - self.height//3),
            (center_x + self.width//3, center_y - self.height//2 + 5)
        ]
        pygame.draw.polygon(screen, (50, 150, 255, 150), canopy_points)
        
        # Engine glow (pulsing blue)
        pygame.draw.circle(screen, engine_glow, 
                         (center_x, center_y + self.height//3), 
                         self.width//4, width=3)
        
        # Hover engines (4 glowing circles)
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
        
        # Speed lines effect (more intense)
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
        
        # Car outline (neon effect)
        pygame.draw.polygon(screen, (0, 255, 255), chassis_points, 2)
        pygame.draw.polygon(screen, (0, 200, 255), canopy_points, 1)

class Renderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Racing Game")
        
        # Field of View settings
        self.FOV = math.pi / 2         # 60 degrees
        self.HALF_FOV = self.FOV / 2
        self.NUM_RAYS = WIDTH
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS
        self.MAX_DEPTH = 20
        
        # Fonts
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 72)
        self.timer_font = pygame.font.Font(None, 48)
        self.speed_font = pygame.font.Font(None, 24)
        self.lap_font = pygame.font.Font(None, 36)
    
    def draw_floor_and_ceiling(self):
        # Draw track (green)
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2, WIDTH, (HEIGHT-UI_HEIGHT)//2))
        
        # Draw sky (blue)
        pygame.draw.rect(self.screen, Color.ROOF.value, (0, 0, WIDTH, (HEIGHT-UI_HEIGHT)//2))
    
    def cast_rays(self, player, game_map):
        visible_special_walls = set()
        
        # First check which special walls are visible
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

            if hit_wall and (game_map.get_cell(test_x, test_y) in [1, 2, 3]):
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001) * 0.95  # 20% of original height
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y) in game_map.walls:
                    if hit_special:
                        game_map.walls[(wall_x, wall_y)].draw(self.screen, ray, proj_height, depth_shade)
                    else:
                        game_map.walls[(wall_x, wall_y)].draw(self.screen, ray, proj_height, depth_shade)
    
    def draw_speedometer(self, speed, max_speed):
        # Position and size
        center_x = WIDTH - 60
        center_y = HEIGHT - 60
        radius = 40
        
        # Calculate speed ratio (0-1) and glow intensity
        speed_ratio = min(1, speed / max_speed)
        glow_intensity = int(100 + speed_ratio * 155)  # 100-255 range
        speed_color = (0, glow_intensity, 255)
        
        # Pulsing effect when at max speed
        if speed_ratio >= 0.99:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))  # Pulsing at 5ms interval
            pulse_radius = int(radius + pulse * 10)  # Pulsing radius expansion
            glow_intensity = 255  # Max brightness when pulsing
        else:
            pulse_radius = radius
        
        # Draw outer glow (more intense at higher speeds)
        for i in range(3, 0, -1):
            glow_radius = pulse_radius + i * 3
            glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            glow_alpha = 30//i
            if speed_ratio >= 0.99:  # More intense glow when pulsing
                glow_alpha = min(60, glow_alpha * 2)
            pygame.draw.circle(glow_surface, (*speed_color, glow_alpha), 
                             (glow_radius, glow_radius), glow_radius)
            self.screen.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius))
        
        # Draw main circle (with pulse effect if at max speed)
        pygame.draw.circle(self.screen, speed_color, (center_x, center_y), pulse_radius)
        pygame.draw.circle(self.screen, (0, 0, 50), (center_x, center_y), pulse_radius, 2)
        
        # Draw speed text (larger when pulsing)
        if speed_ratio >= 0.99:
            speed_font = pygame.font.Font(None, 28)  # Slightly larger font when pulsing
        else:
            speed_font = self.speed_font
            
        speed_text = speed_font.render(f"{int(speed_ratio * 100)}", True, Color.WHITE.value)
        text_rect = speed_text.get_rect(center=(center_x, center_y))
        self.screen.blit(speed_text, text_rect)
        
        # Draw "MPH" label (with slight pulse effect)
        if speed_ratio >= 0.99:
            label_y_offset = 25 + pulse * 2  # Bounce effect
        else:
            label_y_offset = 25
            
        label = self.speed_font.render("MPH", True, Color.WHITE.value)
        label_rect = label.get_rect(center=(center_x, center_y + label_y_offset))
        self.screen.blit(label, label_rect)
    
    def draw_main_menu(self):
        # Gradient background
        for y in range(HEIGHT):
            shade = int(49 + (y / HEIGHT) * 100)
            pygame.draw.line(self.screen, (49, min(184, shade), 37), (0, y), (WIDTH, y))
        
        # Title
        title_text = self.big_font.render("F-ZERO STYLE RACER", True, (200, 200, 255))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        
        # Car illustration
        car_x = WIDTH // 2
        car_y = HEIGHT // 2
        car_width = 120
        car_height = 70
        
        # Car body
        pygame.draw.ellipse(self.screen, (200, 50, 50), 
                          (car_x - car_width//2, car_y - car_height//2, car_width, car_height))
        
        # Cockpit
        pygame.draw.ellipse(self.screen, (50, 150, 255, 150), 
                          (car_x - car_width//3, car_y - car_height//3, car_width//1.5, car_height//2))
        
        # Engine glow
        pygame.draw.circle(self.screen, (0, 200, 255), 
                         (car_x + car_width//3, car_y), 15)
        
        # Start button
        button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
        pygame.draw.rect(self.screen, Color.PURPLE.value, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), button_rect, 3, border_radius=10)
        
        start_text = self.font.render("START", True, Color.WHITE.value)
        self.screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 15))
    
    def draw_mode_select(self):
        # Gradient background
        for y in range(HEIGHT):
            shade = int(49 + (y / HEIGHT) * 100)
            pygame.draw.line(self.screen, (49, min(184, shade), 37), (0, y), (WIDTH, y))
        
        # Title
        title_text = self.big_font.render("SELECT MODE", True, (200, 200, 255))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
        
        # Time Trial button
        time_trial_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 70, 300, 80)
        pygame.draw.rect(self.screen, Color.PURPLE.value, time_trial_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), time_trial_rect, 3, border_radius=10)
        
        time_trial_text = self.font.render("TIME TRIAL", True, Color.WHITE.value)
        time_trial_desc = self.speed_font.render("Race against the clock!", True, Color.WHITE.value)
        self.screen.blit(time_trial_text, (WIDTH//2 - time_trial_text.get_width()//2, HEIGHT//2 - 50))
        self.screen.blit(time_trial_desc, (WIDTH//2 - time_trial_desc.get_width()//2, HEIGHT//2 - 20))
        
        # Race button
        race_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 80)
        pygame.draw.rect(self.screen, Color.PURPLE.value, race_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), race_rect, 3, border_radius=10)
        
        race_text = self.font.render("RACE", True, Color.WHITE.value)
        race_desc = self.speed_font.render("3 laps around the track!", True, Color.WHITE.value)
        self.screen.blit(race_text, (WIDTH//2 - race_text.get_width()//2, HEIGHT//2 + 50))
        self.screen.blit(race_desc, (WIDTH//2 - race_desc.get_width()//2, HEIGHT//2 + 80))
    
    def draw_countdown(self, count):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Countdown text
        count_text = self.big_font.render(str(count), True, (255, 255, 255))
        text_rect = count_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        # Animate size
        size = 100 + (3 - count) * 20
        count_text = pygame.transform.scale(count_text, (size, size))
        text_rect = count_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        self.screen.blit(count_text, text_rect)
    
    def draw_timer(self, time_seconds, mode, current_lap=None, total_laps=None):
        # Format time as MM:SS.mm
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds * 100) % 100)
        time_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        
        # Add lap info for race mode
        if mode == GameMode.RACE and current_lap is not None and total_laps is not None:
            time_text = f"Lap {current_lap}/{total_laps} - {time_text}"
        
        timer_surf = self.timer_font.render(time_text, True, Color.WHITE.value)
        timer_rect = timer_surf.get_rect(topright=(WIDTH - 20, 20))
        
        # Draw semi-transparent background
        bg_rect = timer_rect.inflate(20, 10)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, bg_rect)
        
        self.screen.blit(timer_surf, timer_rect)
    
    def draw_lap_notification(self, lap_number):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Lap text
        lap_text = self.lap_font.render(f"LAP {lap_number}", True, Color.GOLD.value)
        text_rect = lap_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        
        # Animate size (pulse effect)
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))  # Pulsing at 5ms interval
        size = 1.0 + pulse * 0.2  # 20% size variation
        
        # Scale text
        scaled_text = pygame.transform.scale(lap_text, 
                                          (int(lap_text.get_width() * size), 
                                           int(lap_text.get_height() * size)))
        scaled_rect = scaled_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        
        self.screen.blit(scaled_text, scaled_rect)
    
    def draw_end_screen(self, time_seconds, restart_rect, mode):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        if mode == GameMode.TIME_TRIAL:
            title_text = self.big_font.render("FINISHED!", True, Color.GOLD.value)
        else:
            title_text = self.big_font.render("RACE COMPLETE!", True, Color.GOLD.value)
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        
        # Format time as MM:SS.mm
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds * 100) % 100)
        time_text = f"Time: {minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        
        # Draw time
        time_surf = self.big_font.render(time_text, True, Color.WHITE.value)
        self.screen.blit(time_surf, (WIDTH//2 - time_surf.get_width()//2, HEIGHT//2))
        
        # Restart button
        pygame.draw.rect(self.screen, Color.PURPLE.value, restart_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), restart_rect, 3, border_radius=10)
        
        restart_text = self.font.render("Go To Main Menu", True, Color.WHITE.value)
        self.screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 
                                       HEIGHT*2//3 + restart_rect.height//2 - restart_text.get_height()//2))

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
        self.total_laps = 3  # Total laps for race mode
        self.restart_button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
        
        # Initialize player and renderer (maps will be initialized when mode is selected)
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        self.car = Car()
        self.game_map = None
    
    def initialize_time_trial_map(self):
        # Time trial map with a finish wall (2)
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
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,1],  # Wider finish wall
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ], GameMode.TIME_TRIAL)
    
    def initialize_race_map(self):
        # Race map with lap lines (3) - these are passable
        return GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,1],
            [1,3,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # Lap line (passable)
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ], GameMode.RACE)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MAIN_MENU:
                    # Check if start button was clicked
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.state = GameState.MODE_SELECT
                elif self.state == GameState.MODE_SELECT:
                    # Check which mode was selected
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    time_trial_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 70, 300, 80)
                    race_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 80)
                    
                    if time_trial_rect.collidepoint(mouse_x, mouse_y):
                        self.game_mode = GameMode.TIME_TRIAL
                        self.game_map = self.initialize_time_trial_map()
                        self.state = GameState.COUNTDOWN
                        self.countdown_timer = 0
                        self.countdown_value = 3
                        # Reset player position for time trial
                        self.player = Player(1.5, 1.5)
                    elif race_rect.collidepoint(mouse_x, mouse_y):
                        self.game_mode = GameMode.RACE
                        self.game_map = self.initialize_race_map()
                        self.state = GameState.COUNTDOWN
                        self.countdown_timer = 0
                        self.countdown_value = 3
                        # Reset player position and lap counter for race
                        self.player = Player(1.5, 1.5)
                        self.player.laps = 1  # Start on lap 1
                        self.player.lap_times = []
                elif self.state == GameState.WON:
                    # Check if restart button was clicked
                    if self.restart_button_rect.collidepoint(event.pos):
                        self.initialize_game()
    
    def update(self):
        if self.state == GameState.COUNTDOWN:
            self.countdown_timer += 1
            if self.countdown_timer >= 60:  # 1 second per count
                self.countdown_timer = 0
                self.countdown_value -= 1
                if self.countdown_value <= 0:
                    self.state = GameState.PLAYING
                    self.race_start_time = pygame.time.get_ticks() / 1000  # Start race timer
                    if self.game_mode == GameMode.RACE:
                        self.player.current_lap_start = self.race_start_time
        
        if self.state == GameState.PLAYING:
            # Update race timer
            current_time = pygame.time.get_ticks() / 1000
            self.race_time = current_time - self.race_start_time
            
            # Handle player input
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
            
            # Check lap/finish line completion
            if self.player.check_lap_completion(self.game_map, current_time):
                if self.game_mode == GameMode.TIME_TRIAL:
                    self.state = GameState.WON
                elif self.game_mode == GameMode.RACE:
                    self.lap_notification_timer = 120  # Show notification for 2 seconds
                    # Check if race is complete (3 laps)
                    if self.player.laps >= self.total_laps + 1:  # +1 because we start at lap 1
                        self.state = GameState.WON
            
            # Decrement lap notification timer
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
            # Draw the game in the background
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            # Draw countdown on top
            self.renderer.draw_countdown(self.countdown_value)
        elif self.state == GameState.PLAYING:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            # Draw timer with lap info for race mode
            if self.game_mode == GameMode.RACE:
                self.renderer.draw_timer(self.race_time, self.game_mode, 
                                       self.player.laps, self.total_laps)
                # Draw lap notification if needed
                if self.lap_notification_timer > 0 and self.player.laps > 1:
                    self.renderer.draw_lap_notification(self.player.laps - 1)  # -1 because we start at lap 1
            else:
                self.renderer.draw_timer(self.race_time, self.game_mode)
            
            # Draw speedometer
            self.renderer.draw_speedometer(self.player.speed, self.player.max_speed)
        elif self.state == GameState.WON:
            # Draw the game in the background
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            # Draw end screen with time and restart button
            self.renderer.draw_end_screen(self.race_time, self.restart_button_rect, self.game_mode)
        
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