import pygame
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Doom Clone with Black Floor")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)  # Ceiling color

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

# Raycasting settings
FOV = math.pi / 3  # Field of view
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH  # One ray per column for smoother walls
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20

# Floor and ceiling settings
FLOOR_COLOR = BLACK  # Black for the floor
CEILING_COLOR = GRAY  # Gray for the ceiling

# Function to draw the floor and ceiling
def draw_floor_and_ceiling():
    # Draw the floor (solid black)
    pygame.draw.rect(screen, FLOOR_COLOR, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))

    # Draw the ceiling (solid gray)
    pygame.draw.rect(screen, CEILING_COLOR, (0, 0, WIDTH, HEIGHT // 2))

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not projectile_active:  # Shoot projectile
                projectile_active = True
                projectile_distance = 0  # Reset distance
                projectile_pos = [player_pos[0], player_pos[1]]  # Start at player's position
                projectile_angle = player_angle  # Use player's current angle

    # Handle player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:  # Move forward
        new_x = player_pos[0] + math.cos(player_angle) * player_speed
        new_y = player_pos[1] + math.sin(player_angle) * player_speed
        if game_map[int(new_y)][int(new_x)] == 0:
            player_pos[0] = new_x
            player_pos[1] = new_y
    if keys[pygame.K_s]:  # Move backward
        new_x = player_pos[0] - math.cos(player_angle) * player_speed
        new_y = player_pos[1] - math.sin(player_angle) * player_speed
        if game_map[int(new_y)][int(new_x)] == 0:
            player_pos[0] = new_x
            player_pos[1] = new_y
    if keys[pygame.K_a]:  # Rotate left
        player_angle -= player_rot_speed
    if keys[pygame.K_d]:  # Rotate right
        player_angle += player_rot_speed

    # Update projectile position
    if projectile_active:
        projectile_distance += projectile_speed

        # Calculate the projectile's new position in world space
        projectile_pos[0] += math.cos(projectile_angle) * projectile_speed
        projectile_pos[1] += math.sin(projectile_angle) * projectile_speed

        # Check for collision with walls
        map_x, map_y = int(projectile_pos[0]), int(projectile_pos[1])
        if map_x < 0 or map_x >= len(game_map[0]) or map_y < 0 or map_y >= len(game_map):
            projectile_active = False  # Out of bounds
        elif game_map[map_y][map_x] == 1:
            game_map[map_y][map_x] = 2  # Change wall to red
            projectile_active = False  # Stop projectile

    # Clear the screen
    screen.fill(BLACK)

    # Draw the floor and ceiling
    draw_floor_and_ceiling()

    # Raycasting
    for ray in range(NUM_RAYS):
        ray_angle = (player_angle - HALF_FOV) + (ray * DELTA_ANGLE)

        # Distance to the wall
        depth = 0
        hit_wall = False

        while not hit_wall and depth < MAX_DEPTH:
            depth += 0.1
            test_x = int(player_pos[0] + depth * math.cos(ray_angle))
            test_y = int(player_pos[1] + depth * math.sin(ray_angle))

            # Check if ray is out of bounds
            if test_x < 0 or test_x >= len(game_map[0]) or test_y < 0 or test_y >= len(game_map):
                hit_wall = True
                depth = MAX_DEPTH
            elif game_map[test_y][test_x] == 1 or game_map[test_y][test_x] == 2:
                hit_wall = True

        # Calculate projection
        proj_height = HEIGHT / (depth + 0.0001)  # Avoid division by zero

        # Draw walls
        if hit_wall:
            if game_map[test_y][test_x] == 2:  # Red wall
                color = RED
            else:
                color = (255 - int(depth * 10), 255 - int(depth * 10), 255 - int(depth * 10))
            pygame.draw.rect(screen, color, (ray, HEIGHT // 2 - proj_height // 2, 1, proj_height))

    # Draw projectile (in screen space)
    if projectile_active:
        # Calculate the size of the projectile based on its distance
        projectile_size = max(1, int(20 - (projectile_distance / projectile_max_distance) * 18))
        # Projectile appears to come from the center of the screen and move forward
        proj_screen_x = WIDTH // 2
        proj_screen_y = HEIGHT // 2
        pygame.draw.circle(screen, RED, (proj_screen_x, proj_screen_y), projectile_size)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()