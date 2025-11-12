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
    GRAY = (247, 199, 67)  # Changed to darker gray for walls
    FLOOR_GRAY = (247, 218, 139)
    ROOF = (214, 189, 122)
    UI_BACKGROUND = (30, 30, 30)
    STAR = (255, 255, 100)
    STAR_DARK = (200, 200, 50)

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
        self.color = Color.GRAY  # Set default color to gray
    
    def set_color(self, color):
        self.color = color
    
    def draw(self, screen, ray, proj_height, depth_shade):
        # Use the wall's color but apply depth shading
        base_color = self.color.value if self.color else depth_shade
        # Blend with depth shading
        shaded_color = (
            max(0, min(255, base_color[0] * (depth_shade[0]/255))),
            max(0, min(255, base_color[1] * (depth_shade[1]/255))),
            max(0, min(255, base_color[2] * (depth_shade[2]/255)))
        )
        pygame.draw.rect(screen, shaded_color, 
                        (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                         1, proj_height))

class StarObject(GameObject):
    def __init__(self, x, y):
        super().__init__(x + 0.5, y + 0.5)  # Center in the cell
        self.size = 0.4
        self.visible_distance = 5
        self.collected = False
        self.pulse = 0
        self.pulse_speed = 0.05
        self.y_offset = 0.4  # Additional offset to make it sit lower
        
    def draw(self, screen, player, renderer):
        if self.collected:
            return
            
        # Calculate distance to player
        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.sqrt(dx**2 + dy**2)
        
        # Only draw if player is close enough
        if dist > self.visible_distance:
            return
            
        # Calculate angle and ensure it's within FOV
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            # Calculate projection
            proj_height = (HEIGHT-UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            # Animate pulsing effect
            self.pulse += self.pulse_speed
            pulse_offset = math.sin(self.pulse) * 2
            
            # Base size with pulse effect
            base_size = int(proj_height * self.size) + pulse_offset
            
            # Calculate position on ground - lowered by adding more to base_y
            base_y = (HEIGHT-UI_HEIGHT)//2 + base_size//2 + int(proj_height * self.y_offset)
            
            # Create star points (5-point star)
            outer_radius = base_size
            inner_radius = outer_radius // 2
            points = []
            
            for i in range(10):
                angle = math.pi * 2 * i / 10 - math.pi/2
                radius = inner_radius if i % 2 else outer_radius
                x = screen_x + radius * math.cos(angle)
                y = base_y - outer_radius + radius * math.sin(angle) - base_size//2
                points.append((x, y))
            
            # Draw dark shadow first (for 3D effect)
            shadow_points = [(x, y+3) for x,y in points]
            pygame.draw.polygon(screen, Color.STAR_DARK.value, shadow_points)
            
            # Draw main star
            pygame.draw.polygon(screen, Color.STAR.value, points)
            
            # Add highlight
            highlight_points = []
            for i in range(0, 10, 2):
                x = screen_x + (outer_radius * 0.7) * math.cos(math.pi * 2 * i / 10 - math.pi/2)
                y = base_y - outer_radius + (outer_radius * 0.7) * math.sin(math.pi * 2 * i / 10 - math.pi/2) - base_size//2
                highlight_points.append((x, y))
            
            highlight_color = (min(255, Color.STAR.value[0]+50), 
                             min(255, Color.STAR.value[1]+50), 
                             min(255, Color.STAR.value[2]+50))
            pygame.draw.polygon(screen, highlight_color, highlight_points)

class GameMap:
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.star_object = None
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    wall = Wall(x, y)
                    wall.set_color(Color.GRAY)  # Explicitly set color
                    self.walls[(x, y)] = wall
                elif self.map_data[y][x] == 2:
                    self.star_object = StarObject(x, y)
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            return self.map_data[y][x]
        return None
    
    def color_wall(self, x, y, color):
        if (x, y) in self.walls:
            self.walls[(x, y)].set_color(color)
    
    def check_collectible(self, player):
        if self.star_object and not self.star_object.collected:
            dist = math.sqrt((player.x - self.star_object.x)**2 + 
                           (player.y - self.star_object.y)**2)
            if dist < 0.7:  # Collection radius
                self.star_object.collected = True
                return True
        return False

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0.08
        self.rot_speed = 0.08
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
        # Set up the game window with specified dimensions
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Shooter")  # Window title
        
        # Field of View (FOV) settings - controls how wide the player can see
        self.FOV = math.pi / 3           # 60 degrees in radians (wide angle view)
        self.HALF_FOV = self.FOV / 2     # Half of the FOV for left/right calculations
        self.NUM_RAYS = WIDTH            # One ray cast for each vertical screen column
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS  # Angle between adjacent rays
        self.MAX_DEPTH = 20              # Maximum distance rays can travel
    
    def draw_floor_and_ceiling(self):
        """
        Draws the floor and ceiling as simple colored rectangles.
        The screen is split horizontally with ceiling on top and floor on bottom.
        """
        # Draw floor (bottom half of screen below UI)
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT-UI_HEIGHT)//2,  # Start at middle of screen
                         WIDTH, (HEIGHT-UI_HEIGHT)//2))  # Cover bottom half
        
        # Draw ceiling (top half of screen)
        pygame.draw.rect(self.screen, Color.ROOF.value,
                        (0, 0,  # Start at top-left corner
                         WIDTH, (HEIGHT-UI_HEIGHT)//2))  # Cover top half
    
    def cast_rays(self, player, game_map):
        """
        Implements raycasting to create the 3D perspective:
        1. Shoots rays in a fan-shaped pattern from the player
        2. Checks for wall collisions
        3. Draws vertical wall slices based on distance
        """
        # Cast one ray for each vertical screen column
        for ray in range(self.NUM_RAYS):
            # Calculate angle of this ray (spread across the FOV)
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            # Initialize ray tracking variables
            depth = 0           # How far the ray has traveled
            hit_wall = False    # Whether we've hit a wall
            wall_x, wall_y = 0, 0  # Stores position of wall hits

            # March the ray forward until we hit something or reach max distance
            while not hit_wall and depth < self.MAX_DEPTH:
                depth += 0.1  # Move ray forward in small increments
                
                # Calculate current ray position
                test_x = int(player.x + depth * math.cos(ray_angle))
                test_y = int(player.y + depth * math.sin(ray_angle))

                # Check if ray went out of bounds
                if game_map.get_cell(test_x, test_y) is None:
                    hit_wall = True
                    depth = self.MAX_DEPTH  # Treat as very far away
                
                # Check if ray hit a wall (cell value 1)
                elif game_map.get_cell(test_x, test_y) == 1:
                    hit_wall = True
                    wall_x, wall_y = test_x, test_y  # Remember hit position

            # If we hit a wall, draw its vertical slice
            if hit_wall and game_map.get_cell(test_x, test_y) == 1:
                # Calculate wall height (inverse of distance - closer walls appear taller)
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001)  # +0.0001 avoids division by zero
                
                # Calculate shading (farther walls are darker)
                depth_shade = (255 - int(depth * 10),) * 3  # Creates (gray, gray, gray) tuple
                
                # Draw the wall slice if it exists in our wall dictionary
                if (wall_x, wall_y) in game_map.walls:
                    game_map.walls[(wall_x, wall_y)].draw(
                        self.screen, 
                        ray,           # x-position on screen
                        proj_height,   # height of wall slice
                        depth_shade    # color with distance shading
                    )

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
            [1,0,1,0,1,0,1,1,1,0,1,1,0,1,1,1,0,1,0,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,1,1,1,1,1,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,0,1,1,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1],
            [1,2,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1],
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
        self.screen.fill(Color.CYAN.value)
        
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
        
        if self.game_map.star_object:
            self.game_map.star_object.update()
        
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
            
            # Draw star object if it exists and isn't collected
            if self.game_map.star_object and not self.game_map.star_object.collected:
                self.game_map.star_object.draw(self.screen, self.player, self.renderer)
            
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