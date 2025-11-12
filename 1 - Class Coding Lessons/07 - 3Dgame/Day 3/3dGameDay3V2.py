import pygame
import math
import sys
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
UI_HEIGHT = 100  # Height for the UI panel at the bottom

class GameState(Enum):
    MAIN_MENU = 0
    PLAYING = 1
    GAME_OVER = 2

class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (100, 100, 100)
    FLOOR_GRAY = (80, 80, 80)
    ROOF = (50, 50, 50)
    PORTAL_BLUE = (0, 162, 232)
    PORTAL_ORANGE = (255, 128, 0)
    UI_BG = (30, 30, 40)

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass

class PortalProjectile(GameObject):
    def __init__(self, x, y, angle, color):
        super().__init__(x, y)
        self.angle = angle
        self.color = color
        self.speed = 0.3
        self.lifetime = 60  # frames
        self.size = 0.2
        self.active = True
    
    def update(self, game_map):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        
        # Check if hit wall
        if game_map.get_cell(int(self.x), int(self.y)) == 1:
            self.active = False
            return (self.x, self.y, self.angle)
        
        if self.lifetime <= 0:
            self.active = False
        
        return None
    
    def draw(self, screen, player, renderer):
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        if dist_sq > (renderer.MAX_DEPTH * 0.7) ** 2:
            return
            
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT - UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            size = int(proj_height * self.size)
            pygame.draw.circle(screen, self.color.value, 
                              (screen_x, (HEIGHT - UI_HEIGHT)//2), size)

class Portal(GameObject):
    def __init__(self, x, y, color, normal_angle):
        super().__init__(x, y)
        self.color = color
        self.normal_angle = normal_angle
        self.exit_angle = (normal_angle + math.pi) % (2 * math.pi)
        self.size = 0.5
        self.active = True
        self.pulse = 0
        self.pulse_direction = 1
        self.linked_portal = None
    
    def update(self):
        self.pulse += 0.05 * self.pulse_direction
        if self.pulse > 1.0:
            self.pulse_direction = -1
        elif self.pulse < 0.0:
            self.pulse_direction = 1
    
    def link_to(self, other_portal):
        self.linked_portal = other_portal
        other_portal.linked_portal = self
    
    def draw(self, screen, player, renderer):
        if not self.active:
            return
            
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        if dist_sq > (renderer.MAX_DEPTH * 0.7) ** 2:
            return
            
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT - UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            size = int(proj_height * self.size)
            pulse_size = int(size * (1 + self.pulse * 0.1))
            portal_color = self.color.value
            
            portal_surface = pygame.Surface((pulse_size*2, pulse_size*2), pygame.SRCALPHA)
            pygame.draw.circle(portal_surface, (*portal_color, 200), 
                             (pulse_size, pulse_size), pulse_size)
            pygame.draw.circle(portal_surface, (*portal_color, 100), 
                             (pulse_size, pulse_size), int(pulse_size * 0.7))
            pygame.draw.circle(portal_surface, (*portal_color, 150), 
                             (pulse_size, pulse_size), int(pulse_size * 0.3))
            
            screen.blit(portal_surface, 
                       (screen_x - pulse_size, 
                        (HEIGHT - UI_HEIGHT)//2 - pulse_size))

class Wall(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = Color.GRAY.value
    
    def draw(self, screen, ray, proj_height, depth_shade):
        base_color = self.color
        shaded_color = (
            max(0, min(255, base_color[0] * (depth_shade[0]/255))),
            max(0, min(255, base_color[1] * (depth_shade[1]/255))),
            max(0, min(255, base_color[2] * (depth_shade[2]/255)))
        )
        
        pygame.draw.rect(screen, shaded_color, 
                        (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                         1, proj_height))

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0
        self.max_speed = 0.08
        self.acceleration = 0.0015
        self.deceleration = 0.001
        self.rot_speed = 0.05
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0
        self.teleport_cooldown = 0
        self.projectiles = []
    
    def shoot_portal(self, angle, color):
        if self.portal_cooldown > 0:
            return
            
        self.portal_cooldown = 10
        self.projectiles.append(PortalProjectile(self.x, self.y, angle, color))
    
    def update_projectiles(self, game_map):
        for projectile in self.projectiles[:]:
            result = projectile.update(game_map)
            if result and not projectile.active:
                x, y, normal_angle = result
                if projectile.color == Color.PORTAL_BLUE:
                    if self.blue_portal:
                        self.blue_portal.active = False
                    self.blue_portal = Portal(x, y, projectile.color, normal_angle)
                    if self.orange_portal and self.orange_portal.active:
                        self.blue_portal.link_to(self.orange_portal)
                else:
                    if self.orange_portal:
                        self.orange_portal.active = False
                    self.orange_portal = Portal(x, y, projectile.color, normal_angle)
                    if self.blue_portal and self.blue_portal.active:
                        self.orange_portal.link_to(self.blue_portal)
            
            if not projectile.active:
                self.projectiles.remove(projectile)
    
    def try_teleport(self):
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
            return False
            
        teleported = False
        
        # Check both portals in either direction
        for portal in [self.blue_portal, self.orange_portal]:
            if portal and portal.active and portal.linked_portal:
                dx = portal.x - self.x
                dy = portal.y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 0.5:  # Close enough to portal
                    # Calculate exit position and angle
                    exit_portal = portal.linked_portal
                    self.x = exit_portal.x + math.cos(exit_portal.exit_angle) * 0.6
                    self.y = exit_portal.y + math.sin(exit_portal.exit_angle) * 0.6
                    self.angle = exit_portal.exit_angle
                    teleported = True
                    break
                
        if teleported:
            self.teleport_cooldown = 10
        return teleported
    
    def update(self, game_map):
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(self.max_speed, self.speed + self.acceleration)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(-self.max_speed/2, self.speed - self.acceleration)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= self.rot_speed * (0.5 + abs(self.speed) / self.max_speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += self.rot_speed * (0.5 + abs(self.speed) / self.max_speed)
        
        # Apply friction
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.deceleration)
        
        # Try to move
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed
        
        if game_map.get_cell(int(new_x), int(new_y)) == 0:
            self.x = new_x
            self.y = new_y
        
        # Update projectiles
        self.update_projectiles(game_map)
        
        # Check for teleportation
        self.try_teleport()
        
        # Update portals
        if self.blue_portal:
            self.blue_portal.update()
        if self.orange_portal:
            self.orange_portal.update()

class GameMap:
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.initialize_walls()
    
    def initialize_walls(self):
        for y in range(len(self.map_data)):
            for x in range(len(self.map_data[0])):
                if self.map_data[y][x] == 1:
                    self.walls[(x, y)] = Wall(x, y)
    
    def get_cell(self, x, y):
        if 0 <= x < len(self.map_data[0]) and 0 <= y < len(self.map_data):
            return self.map_data[y][x]
        return None
    
    def find_wall_hit(self, start_x, start_y, angle):
        """Find the wall that would be hit by a ray cast at the given angle"""
        x, y = start_x, start_y
        sin_a, cos_a = math.sin(angle), math.cos(angle)
        normal_angle = angle
        
        # Increased max distance check
        for _ in range(100):
            x += cos_a * 0.1
            y += sin_a * 0.1
            
            cell_x, cell_y = int(x), int(y)
            if self.get_cell(cell_x, cell_y) == 1:
                # Calculate which wall face we hit
                # Check x-axis wall
                if self.get_cell(cell_x - int(cos_a > 0), cell_y) == 0:
                    normal_angle = math.pi if cos_a > 0 else 0
                # Check y-axis wall
                elif self.get_cell(cell_x, cell_y - int(sin_a > 0)) == 0:
                    normal_angle = 3*math.pi/2 if sin_a > 0 else math.pi/2
                
                return (x, y, normal_angle)
        
        return None

class Renderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Portal Game")
        
        # Performance optimizations
        self.FOV = math.pi / 2
        self.HALF_FOV = self.FOV / 2
        self.NUM_RAYS = WIDTH // 2
        self.DELTA_ANGLE = self.FOV / self.NUM_RAYS
        self.MAX_DEPTH = 20
        
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 72)
    
    def draw_floor_and_ceiling(self):
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, (HEIGHT - UI_HEIGHT)//2, WIDTH, (HEIGHT - UI_HEIGHT)//2))
        pygame.draw.rect(self.screen, Color.ROOF.value, (0, 0, WIDTH, (HEIGHT - UI_HEIGHT)//2))
    
    def cast_rays(self, player, game_map):
        for ray in range(self.NUM_RAYS):
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            depth = 0
            hit_wall = False

            while not hit_wall and depth < self.MAX_DEPTH:
                depth += 0.1
                
                test_x = int(player.x + depth * math.cos(ray_angle))
                test_y = int(player.y + depth * math.sin(ray_angle))

                if game_map.get_cell(test_x, test_y) == 1:
                    hit_wall = True
                    wall_x, wall_y = test_x, test_y
                elif game_map.get_cell(test_x, test_y) is None:
                    hit_wall = True
                    depth = self.MAX_DEPTH

            if hit_wall and game_map.get_cell(test_x, test_y) == 1:
                proj_height = (HEIGHT-UI_HEIGHT) / (depth + 0.0001)
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y) in game_map.walls:
                    game_map.walls[(wall_x, wall_y)].draw(self.screen, ray*2, proj_height, depth_shade)
    
    def draw_projectiles(self, screen, player):
        for projectile in player.projectiles:
            projectile.draw(screen, player, self)
    
    def draw_ui(self, player):
        # Draw UI background
        pygame.draw.rect(self.screen, Color.UI_BG.value, (0, HEIGHT-UI_HEIGHT, WIDTH, UI_HEIGHT))
        
        # Draw portal indicators
        if player.blue_portal and player.blue_portal.active:
            pygame.draw.circle(self.screen, Color.PORTAL_BLUE.value, (50, HEIGHT-50), 20)
            if player.blue_portal.linked_portal:
                pygame.draw.circle(self.screen, (200, 200, 255), (50, HEIGHT-50), 5)
        else:
            pygame.draw.circle(self.screen, (50, 50, 100), (50, HEIGHT-50), 20)
        
        if player.orange_portal and player.orange_portal.active:
            pygame.draw.circle(self.screen, Color.PORTAL_ORANGE.value, (100, HEIGHT-50), 20)
            if player.orange_portal.linked_portal:
                pygame.draw.circle(self.screen, (200, 200, 255), (100, HEIGHT-50), 5)
        else:
            pygame.draw.circle(self.screen, (100, 50, 0), (100, HEIGHT-50), 20)
        
        # Draw instructions
        instructions = self.font.render("LMB: Blue Portal | RMB: Orange Portal | WASD: Move", True, Color.WHITE.value)
        self.screen.blit(instructions, (150, HEIGHT-60))
    
    def draw_main_menu(self):
        for y in range(HEIGHT):
            shade = int(50 + (y / HEIGHT) * 50)
            pygame.draw.line(self.screen, (shade, shade, shade), (0, y), (WIDTH, y))
        
        title_text = self.big_font.render("PORTAL GAME", True, (200, 200, 255))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        
        button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
        pygame.draw.rect(self.screen, (70, 70, 100), button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 255), button_rect, 3, border_radius=10)
        
        start_text = self.font.render("START", True, Color.WHITE.value)
        self.screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 15))

class Game:
    def __init__(self):
        self.initialize_game()
    
    def initialize_game(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU
        
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        self.game_map = GameMap([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ])
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MAIN_MENU:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.state = GameState.PLAYING
                
                elif self.state == GameState.PLAYING:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    ray_angle = self.player.angle - self.renderer.HALF_FOV + (mouse_x / WIDTH) * self.renderer.FOV
                    
                    if event.button == 1:  # Left click - blue portal
                        self.player.shoot_portal(ray_angle, Color.PORTAL_BLUE)
                    elif event.button == 3:  # Right click - orange portal
                        self.player.shoot_portal(ray_angle, Color.PORTAL_ORANGE)
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.player.update(self.game_map)
    
    def render(self):
        if self.state == GameState.MAIN_MENU:
            self.renderer.draw_main_menu()
        
        elif self.state == GameState.PLAYING:
            self.renderer.draw_floor_and_ceiling()
            self.renderer.cast_rays(self.player, self.game_map)
            
            # Draw projectiles first (behind portals)
            self.renderer.draw_projectiles(self.renderer.screen, self.player)
            
            # Draw portals
            if self.player.blue_portal:
                self.player.blue_portal.draw(self.renderer.screen, self.player, self.renderer)
            if self.player.orange_portal:
                self.player.orange_portal.draw(self.renderer.screen, self.player, self.renderer)
            
            self.renderer.draw_ui(self.player)
        
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