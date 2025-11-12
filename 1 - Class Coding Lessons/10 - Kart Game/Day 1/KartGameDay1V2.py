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
    COUNTDOWN = 1
    PLAYING = 2
    WON = 3
    GAME_OVER = 4

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
    def __init__(self, x, y, is_finish=False):
        super().__init__(x, y)
        self.is_finish = is_finish
        if is_finish:
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
        
        # Add special effect for finish wall
        if self.is_finish:
            # Pulsing gold effect
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            pulse_color = (
                min(255, shaded_color[0] + int(pulse * 50)),
                min(255, shaded_color[1] + int(pulse * 50)),
                min(255, shaded_color[2] + int(pulse * 20))
            )
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
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.finish_walls = []  # Track finish walls separately
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    wall = Wall(x, y)
                    self.walls[(x, y)] = wall
                elif self.map_data[y][x] == 2:  # Finish wall
                    wall = Wall(x, y, is_finish=True)
                    self.walls[(x, y)] = wall
                    self.finish_walls.append((x, y))
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
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
            if self.get_cell(int(test_x), int(test_y)) == 1:  # Regular wall blocks view
                return False
        return True

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0
        self.max_speed = 0.08
        self.acceleration = 0.0015
        self.deceleration = 0.001
        self.rot_speed = 0.05
        self.momentum = 0  # Added momentum factor
    
    def update_movement(self, game_map):
        # Apply momentum
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        
        # Update position based on current speed
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
        self.angle -= self.rot_speed * (0.5 + self.speed / self.max_speed)  # Faster rotation when moving faster
    
    def rotate_right(self):
        self.angle += self.rot_speed * (0.5 + self.speed / self.max_speed)

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
    
    def draw_floor_and_ceiling(self):
        # Draw track (green)
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2, WIDTH, (HEIGHT-UI_HEIGHT)//2))
        
        # Draw sky (blue)
        pygame.draw.rect(self.screen, Color.ROOF.value, (0, 0, WIDTH, (HEIGHT-UI_HEIGHT)//2))
    
    def cast_rays(self, player, game_map):
        visible_finish_walls = set()
        
        # First check which finish walls are visible
        for wall_x, wall_y in game_map.finish_walls:
            if game_map.is_visible(player.x, player.y, wall_x, wall_y):
                visible_finish_walls.add((wall_x, wall_y))
        
        for ray in range(self.NUM_RAYS):
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            depth = 0
            hit_wall = False
            hit_finish = False
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
                elif game_map.get_cell(test_x, test_y) == 2 and (test_x, test_y) in visible_finish_walls:
                    hit_wall = True
                    hit_finish = True
                    wall_x, wall_y = test_x, test_y

            if hit_wall and (game_map.get_cell(test_x, test_y) in [1, 2]):
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001) * 0.95  # 20% of original height
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y) in game_map.walls:
                    if hit_finish:
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
        
        start_text = self.font.render("START RACE", True, Color.WHITE.value)
        self.screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 15))
    
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
    
    def draw_timer(self, time_seconds):
        # Format time as MM:SS.mm
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds * 100) % 100)
        time_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        
        timer_surf = self.timer_font.render(time_text, True, Color.WHITE.value)
        timer_rect = timer_surf.get_rect(topright=(WIDTH - 20, 20))
        
        # Draw semi-transparent background
        bg_rect = timer_rect.inflate(20, 10)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, bg_rect)
        
        self.screen.blit(timer_surf, timer_rect)
    
    def draw_end_screen(self, time_seconds, restart_rect):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_text = self.big_font.render("FINISH LINE!", True, Color.GOLD.value)
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
        self.countdown_timer = 0
        self.countdown_value = 3
        self.race_start_time = 0
        self.race_time = 0
        self.restart_button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
        
        # Modified map with finish wall (2) at the end
        self.game_map = GameMap([
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
        ])
        
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        self.car = Car()
    
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
                        self.state = GameState.COUNTDOWN
                        self.countdown_timer = 0
                        self.countdown_value = 3
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
        
        if self.state == GameState.PLAYING:
            # Update race timer
            self.race_time = pygame.time.get_ticks() / 1000 - self.race_start_time
            
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
            
            # Check if player is near the finish wall (within 0.5 units)
            player_cell_x = int(self.player.x)
            player_cell_y = int(self.player.y)
            
            # Check current cell and adjacent cells
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x = player_cell_x + dx
                    check_y = player_cell_y + dy
                    if (0 <= check_x < len(self.game_map.map_data[0])) and (0 <= check_y < len(self.game_map.map_data)):
                        if self.game_map.map_data[check_y][check_x] == 2:  # Finish wall
                            self.state = GameState.WON
                            break
    
    def render(self):
        if self.state == GameState.MAIN_MENU:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_main_menu()
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
            
            # Draw race timer
            self.renderer.draw_timer(self.race_time)
            
            # Draw speedometer
            self.renderer.draw_speedometer(self.player.speed, self.player.max_speed)
        elif self.state == GameState.WON:
            # Draw the game in the background
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
            
            # Draw end screen with time and restart button
            self.renderer.draw_end_screen(self.race_time, self.restart_button_rect)
        
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