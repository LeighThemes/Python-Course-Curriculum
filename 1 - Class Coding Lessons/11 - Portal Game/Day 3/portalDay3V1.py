import pygame
import math
import sys
import random
from enum import Enum
import colorsys
import time

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
    GRAY = (255, 255, 255)
    FLOOR_GRAY = (125, 120, 120)
    ROOF = (125, 120, 120)
    PORTAL_BLUE = (0,101,255)
    PORTAL_ORANGE = (255,93,0)
    UI_BG = (30, 30, 40)
    STAIRS = (252, 0, 0)
    BUTTON_GREEN = (0, 200, 0)
    BUTTON_RED = (200, 0, 0)
    TIMED_WALL = (150, 150, 255)

class GameObject:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z  # Floor level (0 = ground floor, 1 = second floor)
    
    def update(self):
        pass
    
    def draw(self, screen):
        pass

class Collectable(GameObject):
    def __init__(self, x, y, z=0):
        # Initialize the collectable at the center of the grid cell
        super().__init__(x + 0.5, y + 0.5, z)
        
        # Visual and game mechanic properties
        self.size = 0.15                     # Visual size of the collectable
        self.collected = False               # Whether the collectable is currently collected
        self.respawn_timer = 0               # Timestamp of when it was collected
        self.respawn_delay = 5               # Time (in seconds) before it respawns
        self.boost_amount = 3                # Speed boost given to the player
        self.boost_duration = 3              # Duration of the speed boost in seconds
        self.glow_intensity = 0              # For pulsing glow effect
        self.glow_direction = 1              # Direction of glow intensity change (+1 or -1)
        
    def update(self, player, current_time):
        # Skip if on a different floor or already collected
        if self.collected or player.z != self.z:
            if self.collected and current_time - self.respawn_timer >= self.respawn_delay:
                self.collected = False
            return False
            
        # Animate pulsing glow
        self.glow_intensity += 0.05 * self.glow_direction
        if self.glow_intensity >= 1.0:
            self.glow_direction = -1
        elif self.glow_intensity <= 0.2:
            self.glow_direction = 1
                
        # Collision detection
        dx = self.x - player.x
        dy = self.y - player.y
        if dx*dx + dy*dy < 0.25:  # 0.5^2 for collision distance
            self.collected = True
            self.respawn_timer = current_time
            return True
        return False
    
    def draw(self, screen, player, renderer):
        if self.collected or player.z != self.z:
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
            hue = (pygame.time.get_ticks() * 0.002) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, self.glow_intensity)
            rainbow_color = (int(r*255), int(g*255), int(b*255))
            
            # Main collectable
            pygame.draw.rect(screen, rainbow_color, 
                           (screen_x - size//2, (HEIGHT - UI_HEIGHT)//2 - size//2, size, size))
            
            # Glow effect
            for i in range(3, 0, -1):
                glow_size = size + i * 3
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*rainbow_color, 30//i), (0, 0, glow_size, glow_size))
                screen.blit(glow_surface, (screen_x - glow_size//2, (HEIGHT - UI_HEIGHT)//2 - glow_size//2))

class FloorTransportCollectable(Collectable):
    def __init__(self, x, y, z=0):
        super().__init__(x, y, z)
        self.size = 0.2  # Slightly larger than regular collectables
        self.color = (255, 215, 0)  # Gold color
    
    def update(self, player, current_time):
        if self.collected or player.z != self.z:
            return False
            
        dx = self.x - player.x
        dy = self.y - player.y
        if dx*dx + dy*dy < 0.25:  # Collision check
            # Transport player to second floor at same x,y position
            player.z = 1  # Second floor
            self.collected = True
            self.respawn_timer = current_time
            return True
        return False
    
    def draw(self, screen, player, renderer):
        if self.collected or player.z != self.z:
            return
            
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        if dist_sq > (renderer.MAX_DEPTH * 0.3) ** 2:
            return
            
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT - UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            size = int(proj_height * self.size)
            # Draw gold diamond shape
            points = [
                (screen_x, (HEIGHT - UI_HEIGHT)//2 - size),
                (screen_x + size, (HEIGHT - UI_HEIGHT)//2),
                (screen_x, (HEIGHT - UI_HEIGHT)//2 + size),
                (screen_x - size, (HEIGHT - UI_HEIGHT)//2)
            ]
            pygame.draw.polygon(screen, self.color, points)
            
            # Glow effect
            for i in range(3, 0, -1):
                glow_size = size + i * 3
                glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                glow_points = [
                    (glow_size, glow_size - glow_size//2),
                    (glow_size + glow_size//2, glow_size),
                    (glow_size, glow_size + glow_size//2),
                    (glow_size - glow_size//2, glow_size)
                ]
                pygame.draw.polygon(glow_surface, (*self.color, 30//i), glow_points)
                screen.blit(glow_surface, (screen_x - glow_size, (HEIGHT - UI_HEIGHT)//2 - glow_size))

class PortalProjectile(GameObject):
    def __init__(self, x, y, z, angle, color):
        super().__init__(x, y, z)
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
        
        # Check if hit wall (including timed walls)
        cell_val = game_map.get_cell(int(self.x), int(self.y), self.z)
        if cell_val in (1, 2, 3):  # Wall, stairs, or timed wall
            # Only allow portal placement on regular walls (1) or stairs (2)
            if cell_val in (1, 2):
                self.active = False
                return (self.x, self.y, self.z, self.angle)
            else:
                # Hit a timed wall - just disappear without creating portal
                self.active = False
                return None
        
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
    def __init__(self, x, y, z=0, is_stairs=False, is_timed=False):
        super().__init__(x, y, z)
        self.is_stairs = is_stairs
        self.is_timed = is_timed
        self.timer_active = False
        self.timer_duration = 5  # seconds
        self.time_remaining = 0
        
        if is_stairs:
            self.color = Color.STAIRS.value
        elif is_timed:
            self.color = Color.TIMED_WALL.value
        else:
            self.color = Color.GRAY.value
    
    def update(self):
        if self.timer_active:
            self.time_remaining -= 1/60
            if self.time_remaining <= 0:
                self.timer_active = False
    
    def activate_timer(self):
        self.timer_active = True
        self.time_remaining = self.timer_duration
    
    def draw(self, screen, ray, proj_height, depth_shade):
        if self.is_timed and self.timer_active:
            return  # Don't draw when timer is active
        
        base_color = self.color
        if self.is_timed and not self.timer_active:
            # Pulsing effect for timed walls
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) * 30)
            base_color = (
                min(255, max(0, base_color[0] + pulse)),
                min(255, max(0, base_color[1] + pulse)),
                min(255, max(0, base_color[2] + pulse))
            )
        
        shaded_color = (
            max(0, min(255, base_color[0] * (depth_shade[0]/255))),
            max(0, min(255, base_color[1] * (depth_shade[1]/255))),
            max(0, min(255, base_color[2] * (depth_shade[2]/255)))
        )
        
        pygame.draw.rect(screen, shaded_color, 
                        (ray, (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2, 
                         1, proj_height))

class Button(GameObject):
    def __init__(self, x, y, z, target_wall_positions):
        super().__init__(x, y, z)
        self.target_walls = target_wall_positions  # List of (x,y,z) tuples
        self.active = False
        self.cooldown = 0
        self.size = 0.3
    
    def update(self, game_map, player):
        if self.cooldown > 0:
            self.cooldown -= 1/60
        
        # First check if any target walls are still active
        any_wall_active = False
        for wall_pos in self.target_walls:
            wall = game_map.walls.get(wall_pos)
            if wall and isinstance(wall, Wall) and wall.is_timed and wall.timer_active:
                any_wall_active = True
                break
        
        # Update button state based on wall states
        self.active = any_wall_active
        
        # Then check for player interaction
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_f] and 
            abs(player.x - self.x) < 1.5 and 
            abs(player.y - self.y) < 1.5 and 
            player.z == self.z and
            self.cooldown <= 0):
            
            self.activate(game_map)
            self.cooldown = 1  # 1 second cooldown
    
    def activate(self, game_map):
        self.active = True
        for wall_pos in self.target_walls:
            wall = game_map.walls.get(wall_pos)
            if wall and isinstance(wall, Wall) and wall.is_timed:
                wall.activate_timer()
    
    def draw(self, screen, player, renderer):
        if player.z != self.z:
            return
            
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx**2 + dy**2
        
        if dist_sq > (renderer.MAX_DEPTH * 0.18) ** 2:
            return
            
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        
        if -renderer.HALF_FOV <= angle <= renderer.HALF_FOV:
            dist = math.sqrt(dist_sq)
            proj_height = (HEIGHT - UI_HEIGHT) / (dist + 0.0001)
            screen_x = int((angle + renderer.HALF_FOV) / renderer.FOV * WIDTH)
            
            size = int(proj_height * self.size)
            color = Color.BUTTON_GREEN.value if self.active else Color.BUTTON_RED.value
            
            button_surface = pygame.Surface((size*1.1, size), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (*color, 200), 
                            (0, 0, size*1.1, size), border_radius=size//4)
            
            screen.blit(button_surface, 
                       (screen_x - size, 
                        (HEIGHT - UI_HEIGHT)//2 - size//2))

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.angle = 0
        self.speed = 0.4
        self.base_speed = 0.4
        self.max_speed = 10
        self.acceleration = 0.1
        self.deceleration = 0
        self.rot_speed = 0.05  # Rotation speed for Q/E keys
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0
        self.teleport_cooldown = 0
        self.projectiles = []
        self.look_angle = 0  # Vertical look angle
        self.max_look_angle = math.pi/4  # 45 degrees up/down
        self.look_speed = 0.3  # Speed for vertical look
        self.speed_boost_end = 0  # Track when boost expires
        self.floor_timers = {}  # Dictionary to store floor times {floor_number: time}
        self.current_floor_start_time = time.time()
        self.last_floor = 0
        
    def update_floor_timer(self):
        current_time = time.time()
        if self.z != self.last_floor:
            # Record time spent on previous floor
            time_spent = current_time - self.current_floor_start_time
            self.floor_timers[self.last_floor] = time_spent
            # Reset timer for new floor
            self.current_floor_start_time = current_time
            self.last_floor = self.z
    
    def apply_speed_boost(self, duration):
        self.speed = min(self.base_speed + 1.5, self.max_speed)
        self.speed_boost_end = time.time() + duration
    
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
        
        for portal in [self.blue_portal, self.orange_portal]:
            if portal and portal.active and portal.linked_portal and portal.z == self.z:
                dx = portal.x - self.x
                dy = portal.y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 0.5:  # If close enough to portal
                    exit_portal = portal.linked_portal
                    
                    # Calculate exit position with small offset to prevent immediate re-entry
                    offset = 0.3  # Push player slightly forward after exit
                    self.x = exit_portal.x + math.cos(exit_portal.exit_angle) * offset
                    self.y = exit_portal.y + math.sin(exit_portal.exit_angle) * offset
                    self.z = exit_portal.z
                    
                    # Adjust player angle to exit portal's normal
                    self.angle = exit_portal.exit_angle
                    
                    # Longer cooldown to prevent immediate re-teleportation
                    self.teleport_cooldown = 20  # frames (~0.33 seconds at 60 FPS)
                    teleported = True
                    break
        
        return teleported
                  
    
    def update(self, game_map):
        # Check if speed boost expired
        if time.time() > self.speed_boost_end:
            self.speed = self.base_speed
            
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
            wall = game_map.walls.get((int(new_x), int(new_y), self.z))
    
            # Allow movement through empty space, stairs, or active timed walls
            if (cell_val == 0 or cell_val == 2 or 
                (cell_val == 3 and wall and wall.timer_active)):
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
    
        # Apply friction
        if self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.deceleration)
        
        # Update projectiles
        self.update_projectiles(game_map)
        
        self.update_floor_timer()
        
        # Check for teleportation
        self.try_teleport()
        
        # Update portals
        if self.blue_portal:
            self.blue_portal.update()
        if self.orange_portal:
            self.orange_portal.update()
        
        # Update buttons
        for button in game_map.buttons:
            button.update(game_map, self)
        
        # Update walls (for timers)
        for wall in game_map.walls.values():
            if isinstance(wall, Wall):
                wall.update()

class GameMap:
    def __init__(self, map_data):
        self.map_data = map_data
        self.walls = {}
        self.buttons = []  # List to store buttons
        self.collectables = []  # List to store collectables
        self.initialize_walls()
        self.initialize_buttons()
        self.initialize_collectables()
    
    def initialize_walls(self):
        for z in range(len(self.map_data)):
            for y in range(len(self.map_data[z])):
                for x in range(len(self.map_data[z][y])):
                    if self.map_data[z][y][x] == 1:  # Regular wall
                        self.walls[(x, y, z)] = Wall(x, y, z)
                    elif self.map_data[z][y][x] == 2:  # Stairs
                        self.walls[(x, y, z)] = Wall(x, y, z, is_stairs=True)
                    elif self.map_data[z][y][x] == 3:  # Timed wall
                        self.walls[(x, y, z)] = Wall(x, y, z, is_timed=True)
    
    def initialize_buttons(self):
        # Button at (3,3,0) that controls timed walls at (5,5,0) and (6,5,0)
        self.buttons.append(Button(3, 3, 0, [
            (3,7,0),
            (6,1,0),  # First timed wall column (x=6, y=1)
            (17,3,0),  # Second timed wall (x=6, y=2)
            (8,9,0),
            (4,7,0),
        ]))
        # Add more buttons as needed
        self.buttons.append(Button(19, 10, 0, [
            (4,7,0),
            (8,9,0)
        ]))
    
    def initialize_collectables(self):
        # Add collectables at specific positions (x, y, z)
        self.collectables.append(Collectable(7, 1, 0))  # Ground floor
        #self.collectables.append(Collectable(17, 8, 0))  # Ground floor
        self.collectables.append(Collectable(15, 16, 0))  # Ground floor
        self.collectables.append(Collectable(8, 2, 1))  # Second floor
        self.collectables.append(Collectable(5, 15, 1)) # Another on second floor
        
        # Add floor transport collectables
        self.collectables.append(FloorTransportCollectable(10, 10, 0))  # Ground floor
        self.collectables.append(FloorTransportCollectable(3, 15, 1)) 
    
    def get_cell(self, x, y, z):
        if 0 <= z < len(self.map_data):
            if 0 <= y < len(self.map_data[z]):
                if 0 <= x < len(self.map_data[z][y]):
                    # Check if this is a timed wall with active timer
                    if self.map_data[z][y][x] == 3:
                        wall = self.walls.get((x, y, z))
                        if wall and wall.timer_active:
                            return 0  # Treat as empty space when timer is active
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
            
            # Only allow portals on regular walls (1) or stairs (2), not timed walls (3)
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
        
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 72)
        
        # Show mouse cursor
        pygame.mouse.set_visible(True)
    
    def draw_floor_and_ceiling(self, player):
        # Draw floor with perspective based on look angle
        floor_height = (HEIGHT - UI_HEIGHT) // 2
        floor_height += int((HEIGHT - UI_HEIGHT) * 0.3 * math.sin(player.look_angle))
        
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
                if cell_val == 1 or cell_val == 2 or cell_val == 3:  # Wall or stairs or timed wall
                    hit_wall = True
                    wall_x, wall_y = test_x, test_y
                elif cell_val is None:
                    hit_wall = True
                    depth = self.MAX_DEPTH

            if hit_wall and game_map.get_cell(test_x, test_y, wall_z) in (1, 2, 3):
                # Skip rendering if it's a timed wall with active timer
                if game_map.get_cell(test_x, test_y, wall_z) == 3:
                    wall = game_map.walls.get((test_x, test_y, wall_z))
                    if wall and wall.timer_active:
                        continue
                
                # Adjust height based on look angle
                proj_height = (HEIGHT - UI_HEIGHT) / (depth + 0.0001)
                proj_height *= (1 - math.sin(player.look_angle) * 0.5)
                
                depth_shade = (255 - int(depth * 10),) * 3
                
                if (wall_x, wall_y, wall_z) in game_map.walls:
                    wall = game_map.walls[(wall_x, wall_y, wall_z)]
                    
                    # Adjust vertical position based on look angle
                    wall_top = (HEIGHT - UI_HEIGHT) // 2 - proj_height // 2
                    wall_top += int((HEIGHT - UI_HEIGHT) * 0.3 * math.sin(player.look_angle))
                    
                    wall.draw(self.screen, ray*2, proj_height, depth_shade)
    
    def draw_projectiles(self, screen, player):
        for projectile in player.projectiles:
            projectile.draw(screen, player, self)
    
    def draw_buttons(self, screen, game_map, player):
        for button in game_map.buttons:
            button.draw(screen, player, self)
    
    def draw_collectables(self, screen, game_map, player):
        for collectable in game_map.collectables:
            collectable.draw(screen, player, self)
    
    def draw_ui(self, player):
        # Draw UI background
        pygame.draw.rect(self.screen, Color.UI_BG.value, (0, HEIGHT-UI_HEIGHT, WIDTH, UI_HEIGHT))
        
        # Draw floor timers at the top of the screen
        current_time = time.time()
        active_time = current_time - player.current_floor_start_time
        
        # Previous floor times (top left, orange)
        y_offset = 10
        for floor, time_spent in player.floor_timers.items():
            time_text = self.font.render(f"Floor {floor+1}: {time_spent:.1f}s", True, Color.PORTAL_ORANGE.value)
            self.screen.blit(time_text, (10, y_offset))
            y_offset += 30
        
        # Current floor time (top right, blue)
        current_time_text = self.font.render(f"Floor {player.z+1}: {active_time:.1f}s", True, Color.PORTAL_BLUE.value)
        self.screen.blit(current_time_text, (WIDTH - current_time_text.get_width() - 10, 10))
        
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
        
        # Draw speed boost indicator if active
        if time.time() < player.speed_boost_end:
            boost_text = self.font.render("SPEED BOOST!", True, (0, 255, 0))
            self.screen.blit(boost_text, (WIDTH - 150, HEIGHT - 30))
        
        # Draw instructions
        instructions = self.font.render(
            "WASD: Movement | "
            "F: Button | "
            "R: reset", 
            True, Color.WHITE.value
        )
        self.screen.blit(instructions, (150, HEIGHT-60))
        
        # Draw floor indicator
        floor_text = self.font.render(f"Floor: {player.z + 1}", True, Color.WHITE.value)
        self.screen.blit(floor_text, (WIDTH - 150, HEIGHT-60))
    
    def draw_main_menu(self):
        # Darker gradient background for better portal visibility
        for y in range(HEIGHT):
            shade = int(10 + (y / HEIGHT) * 20)
            pygame.draw.line(self.screen, (shade, shade, shade + 10), (0, y), (WIDTH, y))
        
        # Title with stronger glow effect
        title_text = self.big_font.render("PORTAL GAME", True, (200, 200, 255))
        for i in range(5, 0, -1):
            glow_text = self.big_font.render("PORTAL GAME", True, (100, 100, 150, 50//i))
            glow_surface = pygame.Surface((title_text.get_width()+i*10, title_text.get_height()+i*10), pygame.SRCALPHA)
            glow_surface.blit(glow_text, (i*5, i*5))
            self.screen.blit(glow_surface, (WIDTH//2 - glow_surface.get_width()//2, HEIGHT//4 - i*2))
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
        
        # Portal spinning animation parameters
        current_time = pygame.time.get_ticks()
        rotation_speed = 0.003
        blue_angle = current_time * rotation_speed
        orange_angle = -current_time * rotation_speed * 1.2  # Slightly faster reverse rotation
        
        # Draw blue spinning portal
        portal_radius = 80
        portal_center = (WIDTH//2, HEIGHT//2 - 50)
        self.draw_spinning_portal(portal_center, portal_radius, Color.PORTAL_BLUE.value, blue_angle)
        
        # Draw orange spinning portal (smaller, opposite rotation)
        portal_center = (WIDTH//2, HEIGHT//2 + 100)
        self.draw_spinning_portal(portal_center, portal_radius * 0.8, Color.PORTAL_ORANGE.value, orange_angle)
        
        # Start button with improved hover effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 60)
        hover = button_rect.collidepoint(mouse_x, mouse_y)
        
        # Button with animated gradient
        button_surface = pygame.Surface((300, 60), pygame.SRCALPHA)
        for y in range(60):
            alpha = 200 if hover else 150
            shade = int(70 + (math.sin(current_time*0.005 + y*0.1) * 20))
            pygame.draw.line(button_surface, (shade, shade, shade + 30, alpha), (0, y), (300, y))
        
        pygame.draw.rect(button_surface, (200, 200, 255, 100), (0, 0, 300, 60), 3, border_radius=15)
        self.screen.blit(button_surface, (WIDTH//2 - 150, HEIGHT*2//3))
        
        # Button text with subtle animation
        text_offset = int(math.sin(current_time * 0.01) * 2) if hover else 0
        start_text = self.font.render("ENTER THE PORTAL", True, (255, 255, 255))
        self.screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 20 + text_offset))
    
    def draw_spinning_portal(self, center, radius, color, angle):
        """Helper method to draw a spinning portal effect"""
        portal_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        
        # Draw the spinning rings
        ring_count = 5
        for i in range(ring_count):
            ring_radius = radius * (1 - i/ring_count)
            ring_width = max(3, radius * 0.1)
            
            # Calculate points for the spinning segment
            segment_angle = angle + i * math.pi/ring_count
            start_angle = segment_angle
            end_angle = segment_angle + math.pi * 1.5/ring_count
            
            # Draw the spinning segment
            pygame.draw.arc(portal_surface, color, 
                           (radius - ring_radius, radius - ring_radius, 
                            ring_radius*2, ring_radius*2),
                           start_angle, end_angle, int(ring_width))
        
        # Draw the stable center
        center_radius = radius * 0.3
        pygame.draw.circle(portal_surface, (*color, 150), (radius, radius), center_radius)
        
        # Add pulsing glow
        pulse = (math.sin(pygame.time.get_ticks() * 0.003) * 0.2) + 0.8
        glow_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*color, 30), (radius, radius), int(radius * pulse))
        
        # Combine and draw
        portal_surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        self.screen.blit(portal_surface, (center[0] - radius, center[1] - radius))

class Game:
    def __init__(self):
        self.initialize_game()
        
    def reset_game(self):
        self.player = Player(1.5, 1.5)
        self.player.floor_timers = {}
        self.player.current_floor_start_time = time.time()
        self.player.last_floor = 0
    
    def initialize_game(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU
        
        self.player = Player(1.5, 1.5)
        self.renderer = Renderer()
        
        # Fade-in effect variables
        self.fade_alpha = 255  # Start fully opaque (black)
        self.fade_surface = pygame.Surface((WIDTH, HEIGHT))
        self.fade_surface.fill((0, 0, 0))  # Black fade
        self.fade_duration = 2.0  # Duration in seconds
        self.fade_start_time = 0
        self.is_fading_in = False
        
        # 3D map data (z, y, x)
        self.game_map = GameMap([
            # Ground floor (z=0)
            [
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,0,0,1],
                [1,0,2,0,3,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,3,0,0,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
                [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            ],
            # Second floor (z=1)
            [
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,2,0,0,0,1],
                [1,0,0,0,3,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,2,0,0,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1],
                [1,0,1,0,1,0,1,0,0,0,0,0,0,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,0,0,1],
                [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1],
                [1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
                [1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
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
                        self.is_fading_in = True
                        self.fade_start_time = time.time()
                        pygame.mouse.set_visible(True)
                
                elif self.state == GameState.PLAYING:
                    if event.button == 1:  # Left click - blue portal
                        ray_angle = self.player.angle
                        self.player.shoot_portal(ray_angle, Color.PORTAL_BLUE)
                    elif event.button == 3:  # Right click - orange portal
                        ray_angle = self.player.angle
                        self.player.shoot_portal(ray_angle, Color.PORTAL_ORANGE)

    def update(self):
        if self.state == GameState.MAIN_MENU:
            pass
        
        elif self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.reset_game()
            
            # Update fade effect if active
            if self.is_fading_in:
                elapsed = time.time() - self.fade_start_time
                progress = min(elapsed / self.fade_duration, 1.0)
                self.fade_alpha = int(255 * (1 - progress))
                if progress >= 1.0:
                    self.is_fading_in = False
            
            current_time = time.time()
            for collectable in self.game_map.collectables[:]:
                if isinstance(collectable, FloorTransportCollectable):
                    if collectable.update(self.player, current_time):
                        pass
                else:
                    if collectable.update(self.player, current_time):
                        self.player.apply_speed_boost(collectable.boost_duration)
            
            self.player.update(self.game_map)
        
        elif self.state == GameState.GAME_OVER:
            pass

    def render(self):
        if self.state == GameState.MAIN_MENU:
            self.renderer.draw_main_menu()
        
        elif self.state == GameState.PLAYING:
            self.renderer.draw_floor_and_ceiling(self.player)
            self.renderer.cast_rays(self.player, self.game_map)
            self.renderer.draw_projectiles(self.renderer.screen, self.player)
            self.renderer.draw_buttons(self.renderer.screen, self.game_map, self.player)
            self.renderer.draw_collectables(self.renderer.screen, self.game_map, self.player)
            
            if self.player.blue_portal:
                self.player.blue_portal.draw(self.renderer.screen, self.player, self.renderer)
            if self.player.orange_portal:
                self.player.orange_portal.draw(self.renderer.screen, self.player, self.renderer)
            
            self.renderer.draw_ui(self.player)
            
            # Draw fade effect if active
            if self.is_fading_in:
                self.fade_surface.set_alpha(self.fade_alpha)
                self.screen.blit(self.fade_surface, (0, 0))
        
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