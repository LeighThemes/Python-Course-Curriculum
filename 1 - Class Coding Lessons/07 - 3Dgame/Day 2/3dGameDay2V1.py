import pygame
import math
import sys
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
    YELLOW = (255, 255, 0)
    PURPLE = (128, 0, 128)
    CYAN = (0, 255, 255)
    GRAY = (30, 208, 235)
    FLOOR_GRAY = (30, 235, 99)
    UI_BACKGROUND = (30, 30, 30)
    EXIT = (255, 215, 0)  # Gold color for exit
    EXIT_DARK = (200, 170, 0)  # Darker gold for 3D effect

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
        self.color = None
    
    def set_color(self, color):
        self.color = color
    
    def draw(self, screen, ray, proj_height, depth_shade):
        color = self.color.value if self.color else depth_shade
        pygame.draw.rect(screen, color, (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 1, proj_height))

class ExitObject(GameObject):
    def __init__(self, x, y):
        super().__init__(x + 0.5, y + 0.5)  # Center in the cell
        self.base_size = 0.5
        self.visible_distance = 5  # Only show when player is this close
        self.collected = False
        
    def draw(self, screen, player, renderer):
        if self.collected:
            return
            
        # Calculate distance to player
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        
        # Only draw if player is close enough
        if dist > self.visible_distance:
            return
            
        # Calculate relative position
        rel_x = self.x - player.x
        rel_y = self.y - player.y
        
        # Calculate angle and ensure it's within FOV
        angle = math.atan2(rel_y, rel_x) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            # Calculate projection
            proj_height = (HEIGHT-UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            size = int(proj_height * self.base_size)
            
            # Draw 3D cube effect
            front_size = size
            back_size = max(1, int(size * 0.8))
            offset = max(1, int(size * 0.2))
            
            # Back face (darker)
            pygame.draw.rect(screen, Color.EXIT_DARK.value,
                           (screen_x - back_size//2 - offset, 
                            (HEIGHT-UI_HEIGHT)//2 - proj_height//2 - offset,
                            back_size, back_size))
            
            # Front face (brighter)
            pygame.draw.rect(screen, Color.EXIT.value,
                           (screen_x - front_size//2, 
                            (HEIGHT-UI_HEIGHT)//2 - proj_height//2,
                            front_size, front_size))

class GameMap:
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.exit_object = None
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    self.walls[(x, y)] = Wall(x, y)
                elif self.map_data[y][x] == 2:
                    self.exit_object = ExitObject(x, y)
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            return self.map_data[y][x]
        return None
    
    def color_wall(self, x, y, color):
        if (x, y) in self.walls:
            self.walls[(x, y)].set_color(color)
    
    def check_collectible(self, player):
        if self.exit_object and not self.exit_object.collected:
            dist = math.sqrt((player.x - self.exit_object.x)**2 + 
                           (player.y - self.exit_object.y)**2)
            if dist < 0.7:  # Collection radius
                self.exit_object.collected = True
                return True
        return False

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0.05
        self.rot_speed = 0.05
        self.projectile = None
    
    def move_forward(self, game_map):
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed
        
        if game_map.get_cell(int(new_x), int(new_y)) == 0:
            self.x = new_x
            self.y = new_y
    
    def move_backward(self, game_map):
        new_x = self.x - math.cos(self.angle) * self.speed
        new_y = self.y - math.sin(self.angle) * self.speed
        
        if game_map.get_cell(int(new_x), int(new_y)) == 0:
            self.x = new_x
            self.y = new_y
    
    def rotate_left(self):
        self.angle -= self.rot_speed
    
    def rotate_right(self):
        self.angle += self.rot_speed
    
    def shoot(self, color_selector):
        if not self.projectile.active and color_selector.ammo[color_selector.current_color] > 0:
            self.projectile.x = self.x
            self.projectile.y = self.y
            self.projectile.angle = self.angle
            self.projectile.distance = 0
            self.projectile.color = color_selector.current_color
            self.projectile.active = True
            color_selector.ammo[color_selector.current_color] -= 1
            return True
        return False

class Projectile(GameObject):
    def __init__(self, x, y, angle, color):
        super().__init__(x, y)
        self.angle = angle
        self.color = color
        self.speed = 0.5
        self.distance = 0
        self.max_distance = 20
        self.active = False
    
    def update(self):
        if not self.active:
            return
        
        self.distance += self.speed
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        if self.distance >= self.max_distance:
            self.active = False
    
    def draw(self, screen):
        if not self.active:
            return
            
        size = max(1, int(20 - (self.distance / self.max_distance) * 18))
        pygame.draw.circle(screen, self.color.value, (WIDTH // 2, (HEIGHT - UI_HEIGHT) // 2), size)

class ColorSelector:
    def __init__(self):
        self.colors = [Color.RED, Color.GREEN, Color.BLUE, 
                      Color.YELLOW, Color.PURPLE, Color.CYAN]
        self.current_index = 0
        self.timer = 0
        self.duration = 30
        self.ammo = {color: 6 for color in self.colors}
    
    @property
    def current_color(self):
        return self.colors[self.current_index]
    
    def next_color(self):
        self.current_index = (self.current_index + 1) % len(self.colors)
        self.timer = self.duration
    
    def update(self):
        if self.timer > 0:
            self.timer -= 1
    
    def draw_notification(self, screen):
        if self.timer > 0:
            alpha = min(255, self.timer * 8)
            color_name = self.current_color.name
            font = pygame.font.Font(None, 72)
            text_surface = font.render(f"Color: {color_name}", True, self.current_color.value)
            text_surface.set_alpha(alpha)
            text_rect = text_surface.get_rect(center=(WIDTH//2, (HEIGHT-UI_HEIGHT)//2))
            screen.blit(text_surface, text_rect)

class UIPanel:
    def __init__(self, color_selector):
        self.color_selector = color_selector
        self.font = pygame.font.Font(None, 24)
        self.panel_rect = pygame.Rect(0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT)
    
    def draw(self, screen):
        pygame.draw.rect(screen, Color.UI_BACKGROUND.value, self.panel_rect)
        x_pos = 20
        for color in self.color_selector.colors:
            pygame.draw.rect(screen, color.value, (x_pos, HEIGHT-UI_HEIGHT+10, 30, 30))
            ammo_text = f"{self.color_selector.ammo[color]}"
            text_surface = self.font.render(ammo_text, True, Color.WHITE.value)
            screen.blit(text_surface, (x_pos + 35, HEIGHT-UI_HEIGHT+15))
            if color == self.color_selector.current_color:
                pygame.draw.rect(screen, Color.WHITE.value, (x_pos-2, HEIGHT-UI_HEIGHT+8, 34, 34), 2)
            x_pos += 80

class Reticle:
    def __init__(self):
        self.size = 10
        self.thickness = 2
    
    def draw(self, screen, color):
        center_x, center_y = WIDTH // 2, (HEIGHT - UI_HEIGHT) // 2
        inverted_color = (255 - color.value[0], 255 - color.value[1], 255 - color.value[2])
        
        pygame.draw.line(screen, inverted_color, (center_x - self.size, center_y), 
                        (center_x + self.size, center_y), self.thickness)
        pygame.draw.line(screen, inverted_color, (center_x, center_y - self.size), 
                        (center_x, center_y + self.size), self.thickness)
        pygame.draw.circle(screen, inverted_color, (center_x, center_y), self.size, self.thickness)

class Renderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Shooter")
        self.FOV = math.pi / 3
        self.HALF_FOV = self.FOV / 2
        self.NUM_RAYS = WIDTH
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS
        self.MAX_DEPTH = 20
    
    def draw_floor_and_ceiling(self):
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2, WIDTH, (HEIGHT-UI_HEIGHT)//2))
        pygame.draw.rect(self.screen, Color.GRAY.value, 
                        (0, 0, WIDTH, (HEIGHT-UI_HEIGHT)//2))
    
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
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001)
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
        
        self.game_map = GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ])
        
        self.player = Player(1, 1)
        self.color_selector = ColorSelector()
        self.renderer = Renderer()
        self.reticle = Reticle()
        self.ui_panel = UIPanel(self.color_selector)
        self.player.projectile = Projectile(
            self.player.x, self.player.y, 
            self.player.angle, self.color_selector.current_color
        )

    def show_end_screen(self, won):
        self.screen.fill(Color.BLACK.value)
        
        # Title text
        font_large = pygame.font.Font(None, 100)
        title_text = "YOU WIN!" if won else "GAME OVER"
        title_color = Color.GREEN.value if won else Color.RED.value
        title_surface = font_large.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        self.screen.blit(title_surface, title_rect)
        
        # Reset button
        reset_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 50)
        pygame.draw.rect(self.screen, Color.GREEN.value, reset_button)
        
        # Button text
        font_small = pygame.font.Font(None, 36)
        button_text = font_small.render("Play Again", True, Color.BLACK.value)
        button_text_rect = button_text.get_rect(center=reset_button.center)
        self.screen.blit(button_text, button_text_rect)
        
        pygame.display.flip()
        
        waiting = True
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        self.initialize_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if reset_button.collidepoint(event.pos):
                        waiting = False
                        self.initialize_game()
            self.clock.tick(60)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.player.shoot(self.color_selector)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.color_selector.next_color()
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.player.move_forward(self.game_map)
        if keys[pygame.K_s]:
            self.player.move_backward(self.game_map)
        if keys[pygame.K_a]:
            self.player.rotate_left()
        if keys[pygame.K_d]:
            self.player.rotate_right()
        
        self.player.projectile.update()
        self.color_selector.update()
        
        if self.game_map.exit_object:
            self.game_map.exit_object.update()
        
        if self.player.projectile.active:
            map_x, map_y = int(self.player.projectile.x), int(self.player.projectile.y)
            cell = self.game_map.get_cell(map_x, map_y)
            if cell == 1:
                self.game_map.color_wall(map_x, map_y, self.player.projectile.color)
                self.player.projectile.active = False
        
        if self.game_map.check_collectible(self.player):
            self.state = GameState.WON
            self.show_end_screen(True)
    
    def render(self):
        if self.state == GameState.PLAYING:
            self.screen.fill(Color.BLACK.value)
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            
            # Draw exit object if it exists and isn't collected
            if self.game_map.exit_object and not self.game_map.exit_object.collected:
                self.game_map.exit_object.draw(self.screen, self.player, self.renderer)
            
            self.player.projectile.draw(self.screen)
            self.color_selector.draw_notification(self.screen)
            self.ui_panel.draw(self.screen)
            self.reticle.draw(self.screen, self.player.projectile.color)
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