import pygame
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Doom Clone with Persistent Wall Colors")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)  # Ceiling color
FLOOR_GRAY = (50, 50, 50)  # Darker gray for floor

# Available projectile colors in fixed order
COLOR_ORDER = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN]
current_color_index = 0
projectile_color = COLOR_ORDER[current_color_index]
color_change_timer = 0
color_change_duration = 30  # frames to show color change notification

# Larger map (1 = wall, 0 = empty space)
game_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# Wall color storage - stores color for each wall cell
wall_colors = {}
for y in range(len(game_map)):
    for x in range(len(game_map[0])):
        if game_map[y][x] == 1:
            wall_colors[(x, y)] = None  # Initialize with no color

# Player settings
player_pos = [2, 2]  # Starting position
player_angle = 0  # Starting angle
player_speed = 0.05  # Movement speed
player_rot_speed = 0.05  # Rotation speed

# Projectile settings
projectile_pos = None  # Current position of the projectile
projectile_speed = 0.5  # Speed of the projectile
projectile_angle = 0  # Direction of the projectile
projectile_active = False  # Whether the projectile is active
projectile_distance = 0  # Distance traveled by the projectile
projectile_max_distance = 20  # Maximum distance the projectile can travel

# Raycasting settings
FOV = math.pi / 3  # Field of view
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH  # One ray per column for smoother walls
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20

# Floor and ceiling settings
FLOOR_COLOR = FLOOR_GRAY  # Gray for the floor
CEILING_COLOR = GRAY  # Gray for the ceiling

def draw_floor_and_ceiling():
    pygame.draw.rect(screen, FLOOR_COLOR, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    pygame.draw.rect(screen, CEILING_COLOR, (0, 0, WIDTH, HEIGHT // 2))

def draw_color_notification():
    if color_change_timer > 0:
        alpha = min(255, color_change_timer * 8)  # Fade effect
        color_name = {
            RED: "RED",
            GREEN: "GREEN", 
            BLUE: "BLUE",
            YELLOW: "YELLOW",
            PURPLE: "PURPLE",
            CYAN: "CYAN"
        }.get(projectile_color, "UNKNOWN")
        
        font = pygame.font.Font(None, 72)
        text_surface = font.render(f"Color: {color_name}", True, projectile_color)
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)

def change_color(direction=1):
    global current_color_index, projectile_color, color_change_timer
    current_color_index = (current_color_index + direction) % len(COLOR_ORDER)
    projectile_color = COLOR_ORDER[current_color_index]
    color_change_timer = color_change_duration

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not projectile_active:
                projectile_active = True
                projectile_distance = 0
                projectile_pos = [player_pos[0], player_pos[1]]
                projectile_angle = player_angle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                change_color()  # Cycle forward through colors
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        new_x = player_pos[0] + math.cos(player_angle) * player_speed
        new_y = player_pos[1] + math.sin(player_angle) * player_speed
        if game_map[int(new_y)][int(new_x)] == 0:
            player_pos[0] = new_x
            player_pos[1] = new_y
    if keys[pygame.K_s]:
        new_x = player_pos[0] - math.cos(player_angle) * player_speed
        new_y = player_pos[1] - math.sin(player_angle) * player_speed
        if game_map[int(new_y)][int(new_x)] == 0:
            player_pos[0] = new_x
            player_pos[1] = new_y
    if keys[pygame.K_a]:
        player_angle -= player_rot_speed
    if keys[pygame.K_d]:
        player_angle += player_rot_speed

    if projectile_active:
        projectile_distance += projectile_speed
        projectile_pos[0] += math.cos(projectile_angle) * projectile_speed
        projectile_pos[1] += math.sin(projectile_angle) * projectile_speed

        map_x, map_y = int(projectile_pos[0]), int(projectile_pos[1])
        if map_x < 0 or map_x >= len(game_map[0]) or map_y < 0 or map_y >= len(game_map):
            projectile_active = False
        elif game_map[map_y][map_x] == 1:
            # Store the current projectile color for this wall
            wall_colors[(map_x, map_y)] = projectile_color
            projectile_active = False

    screen.fill(BLACK)
    draw_floor_and_ceiling()

    for ray in range(NUM_RAYS):
        ray_angle = (player_angle - HALF_FOV) + (ray * DELTA_ANGLE)
        depth = 0
        hit_wall = False
        wall_x, wall_y = 0, 0

        while not hit_wall and depth < MAX_DEPTH:
            depth += 0.1
            test_x = int(player_pos[0] + depth * math.cos(ray_angle))
            test_y = int(player_pos[1] + depth * math.sin(ray_angle))

            if test_x < 0 or test_x >= len(game_map[0]) or test_y < 0 or test_y >= len(game_map):
                hit_wall = True
                depth = MAX_DEPTH
            elif game_map[test_y][test_x] == 1:
                hit_wall = True
                wall_x, wall_y = test_x, test_y

        proj_height = HEIGHT / (depth + 0.0001)

        if hit_wall and game_map[test_y][test_x] == 1:
            # Check if this wall has a stored color
            wall_color = wall_colors.get((wall_x, wall_y))
            if wall_color:
                color = wall_color
            else:
                # Default shading for uncolored walls
                color = (255 - int(depth * 10), 255 - int(depth * 10), 255 - int(depth * 10))
            pygame.draw.rect(screen, color, (ray, HEIGHT // 2 - proj_height // 2, 1, proj_height))

    if projectile_active:
        projectile_size = max(1, int(20 - (projectile_distance / projectile_max_distance) * 18))
        pygame.draw.circle(screen, projectile_color, (WIDTH // 2, HEIGHT // 2), projectile_size)

    if color_change_timer > 0:
        color_change_timer -= 1
    draw_color_notification()

    pygame.display.flip()

pygame.quit()