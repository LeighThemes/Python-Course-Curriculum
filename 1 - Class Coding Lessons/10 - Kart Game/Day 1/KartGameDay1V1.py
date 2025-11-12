import pygame
import math
import sys
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
UI_HEIGHT = 50  # Height for the UI panel at the bottom

class GameState(Enum):
    PLAYING = 0
    WON = 1
    GAME_OVER = 2

class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (100, 100, 100)  # Wall color
    FLOOR_GRAY = (3, 252, 28)  # Track color
    ROOF = (3, 223, 252)    # Sky color
    CAR_RED = (200, 0, 0)
    CAR_DARK_RED = (150, 0, 0)
    CAR_ACCENT = (255, 100, 100)

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass

class Wall(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
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
        pygame.draw.rect(screen, shaded_color, 
                        (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                         1, proj_height))

class GameMap:
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    wall = Wall(x, y)
                    self.walls[(x, y)] = wall
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            return self.map_data[y][x]
        return None

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0
        self.max_speed = 0.3
        self.acceleration = 0.002
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
        
        # Main car body
        body_rect = pygame.Rect(center_x - self.width//2, center_y - self.height//2, self.width, self.height)
        pygame.draw.rect(screen, Color.CAR_RED.value, body_rect, border_radius=10)
        
        # Hood
        hood_rect = pygame.Rect(center_x - self.width//2, center_y - self.height//2 - self.hood_height//2, 
                               self.width, self.hood_height)
        pygame.draw.rect(screen, Color.CAR_DARK_RED.value, hood_rect, border_radius=5)
        
        # Windshield
        windshield_rect = pygame.Rect(center_x - self.width//3, center_y - self.height//2 - self.hood_height//2, 
                                    self.width//1.5, self.hood_height//2)
        pygame.draw.rect(screen, (100, 100, 200, 150), windshield_rect, border_radius=3)
        
        # Wheels
        wheel_y_offset = math.sin(pygame.time.get_ticks() * 0.02) * 2 * (self.speed_effect / 5)
        pygame.draw.circle(screen, Color.BLACK.value, 
                         (center_x - self.width//3, center_y + self.height//2 - 5 + wheel_y_offset), self.wheel_size)
        pygame.draw.circle(screen, Color.BLACK.value, 
                         (center_x + self.width//3, center_y + self.height//2 - 5 + wheel_y_offset), self.wheel_size)
        
        # Speed lines effect
        if self.speed_effect > 0.5:
            for i in range(int(self.speed_effect)):
                offset = random.randint(0, 50)
                pygame.draw.line(screen, (255, 255, 255, random.randint(50, 200)),
                               (center_x - self.width//2 - offset, center_y - self.height//2 - offset),
                               (center_x - self.width//2 - offset - 20, center_y - self.height//2 - offset - 20), 1)
                pygame.draw.line(screen, (255, 255, 255, random.randint(50, 200)),
                               (center_x + self.width//2 + offset, center_y - self.height//2 - offset),
                               (center_x + self.width//2 + offset + 20, center_y - self.height//2 - offset - 20), 1)

class Renderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Racing Game")
        
        # Field of View settings
        self.FOV = math.pi / 3           # 60 degrees
        self.HALF_FOV = self.FOV / 2
        self.NUM_RAYS = WIDTH
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS
        self.MAX_DEPTH = 20
    
    def draw_floor_and_ceiling(self):
        # Draw track (darker gray)
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2, WIDTH, (HEIGHT-UI_HEIGHT)//2))
        
        # Draw sky (lighter gray)
        pygame.draw.rect(self.screen, Color.ROOF.value, (0, 0, WIDTH, (HEIGHT-UI_HEIGHT)//2))
    
    def cast_rays(self, player, game_map):
        for ray in range(self.NUM_RAYS):
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            depth = 0
            hit_wall = False
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

            if hit_wall and game_map.get_cell(test_x, test_y) == 1:
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001) * 0.95  # 20% of original height
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y) in game_map.walls:
                    game_map.walls[(wall_x, wall_y)].draw(self.screen, ray, proj_height, depth_shade)

class Game:
    def __init__(self):
        self.initialize_game()
    
    def initialize_game(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.PLAYING
        
        # Simple race track map
        self.game_map = GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
            [1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ])
        
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        self.car = Car()
    
    def show_end_screen(self, won):
        self.screen.fill(Color.BLUE.value)
        font = pygame.font.Font(None, 100)
        text = font.render("FINISH LINE!", True, Color.WHITE.value)
        self.screen.blit(text, (WIDTH//2 - 180, HEIGHT//2 - 50))
        pygame.display.flip()
        pygame.time.wait(3000)
        self.initialize_game()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
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
        
        # Check if player reached the end of the track
        if self.player.x > 18 and self.player.y > 18:
            self.state = GameState.WON
            self.show_end_screen(True)
    
    def render(self):
        if self.state == GameState.PLAYING:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            self.car.draw(self.screen)
        
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