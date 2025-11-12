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
    GRAY = (255,255,255)
    FLOOR_GRAY = (80, 80, 80)
    ROOF = (105,105,105)
    PORTAL_BLUE = (0,101,255)
    PORTAL_ORANGE = (255,93,0)
    UI_BG = (30, 30, 40)
    STAIRS = (150, 100, 50)
    HOLE = (0, 0, 0)  # Black holes in walls
    FORCE_FIELD = (100, 200, 255, 150)

class GameObject:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z  # Floor level (0 = ground floor, 1 = second floor)
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass

class PortalProjectile(GameObject):
    def __init__(self, x, y, z, angle, color):
        super().__init__(x, y, z)
        self.angle = angle
        self.color = color
        self.speed = 0.5
        self.lifetime = 60  # frames
        self.size = 0.2
        self.active = True
    
    def update(self, game_map):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        
        # Check if hit wall (but allow passing through holes)
        cell_x, cell_y = int(self.x), int(self.y)
        cell_val = game_map.get_cell(cell_x, cell_y, self.z)
        
        # MODIFIED: Only stop on solid walls (1), not holes (3)
        if cell_val == 1:  # Solid wall
            self.active = False
            return (self.x, self.y, self.z, self.angle)
        
        if self.lifetime <= 0:
            self.active = False
        
        return None
    
    def draw(self, screen, player, renderer):
        if player.z != self.z:
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
            pygame.draw.circle(screen, self.color.value, 
                              (screen_x, (HEIGHT - UI_HEIGHT)//2), size)

class Portal(GameObject):
    def __init__(self, x, y, z, color, normal_angle):
        super().__init__(x, y, z)
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
        if not self.active or player.z != self.z:
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
    def __init__(self, x, y, z=0, is_stairs=False, has_hole=False):
        super().__init__(x, y, z)
        self.is_stairs = is_stairs
        self.has_hole = has_hole
        self.color = Color.STAIRS.value if is_stairs else Color.GRAY.value
        self.field_pulse = 0  # For animated effect
        self.field_pulse_dir = 1
    
    def update(self):
        if self.has_hole:
            # Animate the force field pulse
            self.field_pulse += 0.05 * self.field_pulse_dir
            if self.field_pulse > 1.0:
                self.field_pulse_dir = -1
            elif self.field_pulse < 0.0:
                self.field_pulse_dir = 1
    
    def draw(self, screen, ray, proj_height, depth_shade):
        if self.has_hole:
            # Draw force field effect
            field_color = (
                Color.FORCE_FIELD.value[0],
                Color.FORCE_FIELD.value[1],
                Color.FORCE_FIELD.value[2],
                int(150 + 50 * math.sin(self.field_pulse * math.pi))  # Pulsing alpha
            )
            
            # Create surface for force field
            field_surface = pygame.Surface((2, proj_height), pygame.SRCALPHA)
            pygame.draw.rect(field_surface, field_color, (0, 0, 2, proj_height))
            
            # Draw grid pattern on force field
            grid_color = (200, 230, 255, 100)
            grid_size = int(proj_height / 8)
            for i in range(0, proj_height, grid_size):
                pygame.draw.line(field_surface, grid_color, (0, i), (2, i), 1)
            for i in range(0, 2, 1):
                pygame.draw.line(field_surface, grid_color, (i, 0), (i, proj_height), 1)
            
            # Draw the force field
            wall_top = (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2
            screen.blit(field_surface, (ray, wall_top))
            
            # Draw edge glow
            glow_surface = pygame.Surface((4, proj_height + 4), pygame.SRCALPHA)
            for i in range(3):
                glow_alpha = 50 - i*15
                glow_color = (150, 220, 255, glow_alpha)
                pygame.draw.rect(glow_surface, glow_color, 
                                (i, i, 4 - i*2, proj_height + 4 - i*2), 1)
            screen.blit(glow_surface, (ray - 1, wall_top - 2))
        else:
            # Original solid wall drawing
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
        self.speed = 0.7
        self.max_speed = 0.1
        self.acceleration = 0.2
        self.deceleration = 0
        self.rot_speed = 0.09  # Rotation speed for A/D keys
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0
        self.teleport_cooldown = 0
        self.projectiles = []
        self.look_angle = 0  # Vertical look angle
        self.max_look_angle = math.pi/4  # 45 degrees up/down
        self.look_speed = 0.35  # Speed for vertical look
    
    def shoot_portal(self, angle, color):
        if self.portal_cooldown > 0:
            return
            
        self.portal_cooldown = 10
        self.projectiles.append(PortalProjectile(self.x, self.y, self.z, angle, color))
    
    def update_projectiles(self, game_map):
        for projectile in self.projectiles[:]:
            result = projectile.update(game_map)
            if result and not projectile.active:
                x, y, z, normal_angle = result
                if projectile.color == Color.PORTAL_BLUE:
                    if self.blue_portal:
                        self.blue_portal.active = False
                    self.blue_portal = Portal(x, y, z, projectile.color, normal_angle)
                    if self.orange_portal and self.orange_portal.active:
                        self.blue_portal.link_to(self.orange_portal)
                else:
                    if self.orange_portal:
                        self.orange_portal.active = False
                    self.orange_portal = Portal(x, y, z, projectile.color, normal_angle)
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
            if portal and portal.active and portal.linked_portal and portal.z == self.z:
                dx = portal.x - self.x
                dy = portal.y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 0.5:  # Close enough to portal
                    # Calculate exit position and angle
                    exit_portal = portal.linked_portal
                    self.x = exit_portal.x + math.cos(exit_portal.exit_angle) * 0.6
                    self.y = exit_portal.y + math.sin(exit_portal.exit_angle) * 0.6
                    self.z = exit_portal.z  # Change floor level if needed
                    self.angle = exit_portal.exit_angle
                    teleported = True
                    break
                
        if teleported:
            self.teleport_cooldown = 10
        return teleported
    
    def update(self, game_map):
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
                
        # Movement controls
        keys = pygame.key.get_pressed()
        move_angle = self.angle
            
        # Rotation controls (A/D for left/right)
        if keys[pygame.K_a]:  # Look left
            self.angle -= self.rot_speed
        if keys[pygame.K_d]:  # Look right
            self.angle += self.rot_speed
                
        # Vertical look controls (Q/E for up/down)
        if keys[pygame.K_q]:  # Look up
            self.look_angle = min(self.max_look_angle, self.look_angle + self.look_speed)
        if keys[pygame.K_e]:  # Look down
            self.look_angle = max(-self.max_look_angle, self.look_angle - self.look_speed)
        
        # Movement (W/S for forward/backward)
        if keys[pygame.K_w]:  # Forward
            move_x = math.cos(move_angle) * self.acceleration
            move_y = math.sin(move_angle) * self.acceleration
        elif keys[pygame.K_s]:  # Backward
            move_x = -math.cos(move_angle) * self.acceleration
            move_y = -math.sin(move_angle) * self.acceleration
        else:
            move_x = move_y = 0
            
        # Apply movement
        if move_x != 0 or move_y != 0:
            new_x = self.x + move_x * self.speed
            new_y = self.y + move_y * self.speed
            
            # Check for stairs and collision
            cell_val = game_map.get_cell(int(new_x), int(new_y), self.z)
            if cell_val == 0 or cell_val == 2:  # Empty or stairs
                if cell_val == 2:  # On stairs
                    # Floor changing logic
                    if keys[pygame.K_SPACE]:  # Move up
                        if game_map.get_cell(int(new_x), int(new_y), self.z + 1) == 0:
                            self.z += 1
                    elif keys[pygame.K_LSHIFT]:  # Move down
                        if self.z > 0 and game_map.get_cell(int(new_x), int(new_y), self.z - 1) == 0:
                            self.z -= 1
                self.x = new_x
                self.y = new_y
    
        # Rest of the update method continues...
        
        # Apply friction
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.deceleration)
        
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
        for z in range(len(self.map_data)):
            for y in range(len(self.map_data[z])):
                for x in range(len(self.map_data[z][y])):
                    if self.map_data[z][y][x] == 1:  # Regular wall
                        self.walls[(x, y, z)] = Wall(x, y, z)
                    elif self.map_data[z][y][x] == 2:  # Stairs
                        self.walls[(x, y, z)] = Wall(x, y, z, is_stairs=True)
                    elif self.map_data[z][y][x] == 3:  # Wall with hole
                        self.walls[(x, y, z)] = Wall(x, y, z, has_hole=True)
    
    def get_cell(self, x, y, z):
        if 0 <= z < len(self.map_data):
            if 0 <= y < len(self.map_data[z]):
                if 0 <= x < len(self.map_data[z][y]):
                    return self.map_data[z][y][x]
        return None
    
    def find_wall_hit(self, start_x, start_y, start_z, angle):
        """Find the wall that would be hit by a ray cast at the given angle"""
        x, y, z = start_x, start_y, start_z
        sin_a, cos_a = math.sin(angle), math.cos(angle)
        normal_angle = angle
        
        # Increased max distance check
        for _ in range(100):
            x += cos_a * 0.1
            y += sin_a * 0.1
            
            cell_x, cell_y = int(x), int(y)
            cell_val = self.get_cell(cell_x, cell_y, z)
            if cell_val == 1 or cell_val == 2:  # Wall or stairs
                # Calculate which wall face we hit
                # Check x-axis wall
                if self.get_cell(cell_x - int(cos_a > 0), cell_y, z) == 0:
                    normal_angle = math.pi if cos_a > 0 else 0
                # Check y-axis wall
                elif self.get_cell(cell_x, cell_y - int(sin_a > 0), z) == 0:
                    normal_angle = 3*math.pi/2 if sin_a > 0 else math.pi/2
                
                return (x, y, z, normal_angle)
        
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
        
        # MODIFIED: Wall height multiplier
        self.WALL_HEIGHT_MULTIPLIER = 1.5  # Makes walls appear taller
        
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 72)
        
        # Show mouse cursor
        pygame.mouse.set_visible(True)
    
    def draw_floor_and_ceiling(self, player):
        # MODIFIED: Reduced look angle influence
        floor_height = (HEIGHT - UI_HEIGHT) // 2
        floor_height += int((HEIGHT - UI_HEIGHT) * 0.2 * math.sin(player.look_angle))  # Changed from 0.3
        
        # Draw floor
        pygame.draw.rect(self.screen, Color.FLOOR_GRAY.value, 
                        (0, floor_height, WIDTH, HEIGHT - UI_HEIGHT - floor_height))
        
        # Draw ceiling
        pygame.draw.rect(self.screen, Color.ROOF.value, 
                        (0, 0, WIDTH, floor_height))
    
    def cast_rays(self, player, game_map):
        for ray in range(self.NUM_RAYS):
            ray_angle = (player.angle - self.HALF_FOV) + (ray * self.DELTA_ANGLE)
            
            depth = 0
            hit_wall = False
            wall_z = player.z

            while not hit_wall and depth < self.MAX_DEPTH:
                depth += 0.1
                
                test_x = int(player.x + depth * math.cos(ray_angle))
                test_y = int(player.y + depth * math.sin(ray_angle))
                test_z = wall_z

                cell_val = game_map.get_cell(test_x, test_y, test_z)
                if cell_val == 1 or cell_val == 2:  # Wall or stairs
                    hit_wall = True
                    wall_x, wall_y = test_x, test_y
                elif cell_val is None:
                    hit_wall = True
                    depth = self.MAX_DEPTH

            if hit_wall and game_map.get_cell(test_x, test_y, wall_z) in (1, 2):
                # MODIFIED: Apply wall height multiplier and reduce look angle effect
                proj_height = (HEIGHT - UI_HEIGHT) / (depth + 0.0001) * self.WALL_HEIGHT_MULTIPLIER
                proj_height *= (1 - math.sin(player.look_angle) * 0.2)  # Reduced from 0.5
                
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y, wall_z) in game_map.walls:
                    wall = game_map.walls[(wall_x, wall_y, wall_z)]
                    
                    # MODIFIED: Adjusted vertical position
                    wall_top = (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2
                    wall_top += int((HEIGHT - UI_HEIGHT) * 0.2 * math.sin(player.look_angle))  # Reduced from 0.3
                    
                    pygame.draw.rect(self.screen, depth_shade, 
                                   (ray*2, wall_top, 
                                    1, proj_height))
    
    def draw_projectiles(self, screen, player):
        for projectile in player.projectiles:
            projectile.draw(screen, player, self)
    
    def draw_ui(self, player):
        # Draw UI background
        pygame.draw.rect(self.screen, Color.UI_BG.value, (0, HEIGHT-UI_HEIGHT, WIDTH, UI_HEIGHT))
        
        # Draw portal indicators (stacked vertically)
        portal_indicator_size = 15  # Smaller size
        vertical_spacing = 36  # Space between indicators
        glow_thickness = 1.5  # Thickness of the glow effect
        
        # Blue portal indicator (top)
        if player.blue_portal and player.blue_portal.active:
            # Draw glow effect if linked
            if player.blue_portal.linked_portal:
                pygame.draw.circle(self.screen, (200, 200, 255),  # Glow color
                                 (50, HEIGHT-70), 
                                 portal_indicator_size + glow_thickness)
            # Draw main portal indicator
            pygame.draw.circle(self.screen, Color.PORTAL_BLUE.value, 
                              (50, HEIGHT-70), 
                              portal_indicator_size)
        else:
            # Inactive state
            pygame.draw.circle(self.screen, (50, 50, 100), 
                              (50, HEIGHT-70), 
                              portal_indicator_size)
        
        # Orange portal indicator (bottom)
        if player.orange_portal and player.orange_portal.active:
            # Draw glow effect if linked
            if player.orange_portal.linked_portal:
                pygame.draw.circle(self.screen, (200, 200, 255),  # Glow color
                                 (50, HEIGHT-70 + vertical_spacing), 
                                 portal_indicator_size + glow_thickness)
            # Draw main portal indicator
            pygame.draw.circle(self.screen, Color.PORTAL_ORANGE.value, 
                              (50, HEIGHT-70 + vertical_spacing), 
                              portal_indicator_size)
        else:
            # Inactive state
            pygame.draw.circle(self.screen, (100, 50, 0), 
                              (50, HEIGHT-70 + vertical_spacing), 
                              portal_indicator_size)
        
        # Draw instructions
        instructions = self.font.render(
            "WASD: Movement | "
            "Q/E: Look Up/Down", 
            True, Color.WHITE.value
        )
        self.screen.blit(instructions, (150, HEIGHT-60))
        
        # Draw floor indicator
        floor_text = self.font.render(f"Floor: {player.z + 1}", True, Color.WHITE.value)
        self.screen.blit(floor_text, (WIDTH - 150, HEIGHT-60))
    
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
        
        # 3D map data (z, y, x)
        self.game_map = GameMap([
            # Ground floor (z=0)
            [
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,3,0,0,0,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,3,0,0,0,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,3,0,0,0,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,1,0,2,1,0,1,0,1,0,1,0,1],  # Stairs here
                [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
                [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
                [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            ],
            # Second floor (z=1)
            [
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
                [1,0,1,0,1,0,1,0,1,0,2,1,0,1,0,1,0,1,0,1],  # Stairs here
                [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
                [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],
                [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            ]
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
                        pygame.mouse.set_visible(True)
                
                elif self.state == GameState.PLAYING:
                    if event.button == 1:  # Left click - blue portal
                        ray_angle = self.player.angle
                        self.player.shoot_portal(ray_angle, Color.PORTAL_BLUE)
                    elif event.button == 3:  # Right click - orange portal
                        ray_angle = self.player.angle
                        self.player.shoot_portal(ray_angle, Color.PORTAL_ORANGE)
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.player.update(self.game_map)
            # Update all walls (for force field animation)
            for wall in self.game_map.walls.values():
                wall.update()
    
    def render(self):
        if self.state == GameState.MAIN_MENU:
            self.renderer.draw_main_menu()
        
        elif self.state == GameState.PLAYING:
            self.renderer.draw_floor_and_ceiling(self.player)
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