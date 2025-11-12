import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cannon Game")

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Fonts
font = pygame.font.Font(None, 36)

# Floor settings
floor_height = 20
floor_color = GREEN

# Cannon settings
cannon_width, cannon_height = 60, 40
cannon_x = WIDTH // 2
cannon_y = HEIGHT - floor_height - cannon_height  # Place cannon on the floor
cannon_speed = 5
wheel_radius = 10
wheel_rotation = 0

# Projectile settings
projectiles = []
projectile_speed = 10

# Shapes settings
shapes = []
shape_speed = 3
shape_spawn_delay = 120  # Shapes appear less often
shape_spawn_timer = 0


def draw_cannon():
    # Draw cannon body
    pygame.draw.rect(screen, BLACK, (cannon_x - cannon_width // 2, cannon_y, cannon_width, cannon_height))
    # Draw cannon barrel
    pygame.draw.line(screen, BLACK, (cannon_x, cannon_y), (cannon_x, cannon_y - 30), 10)
    # Draw wheels
    global wheel_rotation
    for i in range(4):
        wheel_x = cannon_x - cannon_width // 2 + i * (cannon_width // 3)
        wheel_y = cannon_y + cannon_height
        pygame.draw.circle(screen, BLACK, (wheel_x, wheel_y), wheel_radius)
        # Draw wheel rotation effect
        angle = wheel_rotation + i * 90
        pygame.draw.line(screen, WHITE, (wheel_x, wheel_y),
                         (wheel_x + wheel_radius * math.cos(math.radians(angle)),
                          wheel_y + wheel_radius * math.sin(math.radians(angle))), 2)
    wheel_rotation += cannon_speed  # Rotate wheels as the cannon moves

def draw_floor():
    pygame.draw.rect(screen, floor_color, (0, HEIGHT - floor_height, WIDTH, floor_height))

def draw_projectiles():
    for projectile in projectiles:
        pygame.draw.circle(screen, RED, (int(projectile["x"]), int(projectile["y"])), 5)

def draw_shapes():
    for shape in shapes:
        if shape["number"] == 4 or shape["number"] == 2:
            # Draw squares
            pygame.draw.rect(screen, shape["color"], (shape["x"], shape["y"], shape["size"], shape["size"]))
        elif shape["number"] == 3:
            # Draw triangles
            points = [
                (shape["x"] + shape["size"] // 2, shape["y"]),
                (shape["x"], shape["y"] + shape["size"]),
                (shape["x"] + shape["size"], shape["y"] + shape["size"])
            ]
            pygame.draw.polygon(screen, shape["color"], points)
        elif shape["number"] == 1:
            # Draw circles
            pygame.draw.circle(screen, shape["color"], (shape["x"] + shape["size"] // 2, shape["y"] + shape["size"] // 2), shape["size"] // 2)
        # Draw number
        text = font.render(str(shape["number"]), True, WHITE)
        screen.blit(text, (shape["x"] + shape["size"] // 2 - text.get_width() // 2,
                           shape["y"] + shape["size"] // 2 - text.get_height() // 2))

def spawn_shape():
    shape = {
        "x": random.randint(0, WIDTH - 50),
        "y": 0,
        "size": 60,  # Larger shapes
        "number": random.randint(1, 4),
        "color": random.choice([RED, BLUE, GREEN]),
        "dx": random.choice([-3, 3]),  # Faster horizontal movement
        "dy": shape_speed  # Vertical movement
    }
    shapes.append(shape)

def update_shapes():
    for shape in shapes:
        shape["x"] += shape["dx"]
        shape["y"] += shape["dy"]
        # Bounce off screen edges
        if shape["x"] <= 0 or shape["x"] + shape["size"] >= WIDTH:
            shape["dx"] *= -1
        if shape["y"] <= 0:
            shape["dy"] *= -1
        # Remove shapes that fall below the screen
        if shape["y"] > HEIGHT:
            shapes.remove(shape)

def check_collisions():
    for projectile in projectiles[:]:
        for shape in shapes[:]:
            if (shape["x"] < projectile["x"] < shape["x"] + shape["size"] and
                shape["y"] < projectile["y"] < shape["y"] + shape["size"]):
                # Hit the shape
                if shape["number"] > 1:
                    # Split the shape
                    if shape["number"] == 4:
                        # Split into two "2"s
                        for _ in range(2):
                            shapes.append({
                                "x": shape["x"],
                                "y": shape["y"],
                                "size": shape["size"],
                                "number": 2,
                                "color": shape["color"],
                                "dx": random.choice([-3, 3]),
                                "dy": -shape_speed  # Bounce upward
                            })
                    elif shape["number"] == 3:
                        # Split into three "1"s
                        for _ in range(3):
                            shapes.append({
                                "x": shape["x"],
                                "y": shape["y"],
                                "size": shape["size"],
                                "number": 1,
                                "color": shape["color"],
                                "dx": random.choice([-3, 3]),
                                "dy": -shape_speed  # Bounce upward
                            })
                    elif shape["number"] == 2:
                        # Split into two "1"s
                        for _ in range(2):
                            shapes.append({
                                "x": shape["x"],
                                "y": shape["y"],
                                "size": shape["size"],
                                "number": 1,
                                "color": shape["color"],
                                "dx": random.choice([-3, 3]),
                                "dy": -shape_speed  # Bounce upward
                            })
                # Remove the original shape
                shapes.remove(shape)
                projectiles.remove(projectile)
                break

def update_projectiles():
    for projectile in projectiles[:]:
        projectile["y"] -= projectile_speed
        if projectile["y"] < 0:
            projectiles.remove(projectile)

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    screen.fill(SKY_BLUE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Fire a projectile
                projectiles.append({"x": cannon_x, "y": cannon_y - 30})

    # Move cannon
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and cannon_x > cannon_width // 2:
        cannon_x -= cannon_speed
    if keys[pygame.K_RIGHT] and cannon_x < WIDTH - cannon_width // 2:
        cannon_x += cannon_speed

    # Spawn shapes
    shape_spawn_timer += 1
    if shape_spawn_timer >= shape_spawn_delay:
        spawn_shape()
        shape_spawn_timer = 0

    # Update game objects
    update_shapes()
    update_projectiles()
    check_collisions()

    # Draw game objects
    draw_floor()
    draw_cannon()
    draw_projectiles()
    draw_shapes()

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()