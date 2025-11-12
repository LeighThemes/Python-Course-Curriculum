import pygame
import sys
import math
import random
import time

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
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)

# Fonts
font = pygame.font.Font(None, 36)

# Game states
MAIN_MENU = 0
OPTIONS_MENU = 1
GAME = 2
GAME_OVER = 3
current_state = MAIN_MENU

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
cannon_color = BLACK

# Second cannon settings
second_cannon = None
second_cannon_start_time = 0
second_cannon_duration = 10  # seconds
second_cannon_fire_delay = 0.5  # seconds between shots
last_second_cannon_shot_time = 0

# Projectile settings
projectiles = []
projectile_speed = 10
projectile_radius = 8  # Increased size of cannonball

# Shapes settings
shapes = []
shape_speed = 3
shape_spawn_delay = 120  # Shapes appear less often
shape_spawn_timer = 0

# Special hexagon settings
hexagon_size = 60
hexagon_color = YELLOW
hexagon_glow_timer = 0
hexagon_glow_duration = 1  # seconds
hexagon_spawn_delay = 10  # seconds
hexagon_spawn_timer = 0
hexagon = None

# Menu settings
button_width, button_height = 200, 50
button_color = BLUE
button_hover_color = (0, 100, 200)
text_color = WHITE

# Predefined color options
color_options = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, WHITE, BLACK, SKY_BLUE]

# Initialize options
options = {
    "cannon_color": BLACK,
    "floor_color": GREEN,
    "background_color": SKY_BLUE
}

# Initialize global colors
background_color = options["background_color"]
floor_color = options["floor_color"]
cannon_color = options["cannon_color"]

# Life system
lives = 3
flicker_start_time = 0
flicker_duration = 4  # seconds
flicker_interval = 0.2  # seconds

# Score system
score = 0

def draw_cannon():
    global flicker_start_time
    current_time = time.time()
    if flicker_start_time > 0 and current_time - flicker_start_time < flicker_duration:
        if int((current_time - flicker_start_time) / flicker_interval) % 2 == 0:
            return  # Skip drawing the cannon to create flicker effect
    # Draw cannon body
    pygame.draw.rect(screen, cannon_color, (cannon_x - cannon_width // 2, cannon_y, cannon_width, cannon_height))
    # Draw cannon barrel
    pygame.draw.line(screen, cannon_color, (cannon_x, cannon_y), (cannon_x, cannon_y - 30), 10)
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

def draw_second_cannon():
    if second_cannon:
        # Draw second cannon body
        pygame.draw.rect(screen, GOLD, (second_cannon["x"] - cannon_width // 2, second_cannon["y"], cannon_width, cannon_height))
        # Draw second cannon barrel
        pygame.draw.line(screen, GOLD, (second_cannon["x"], second_cannon["y"]), (second_cannon["x"], second_cannon["y"] - 30), 10)
        # Draw wheels
        for i in range(4):
            wheel_x = second_cannon["x"] - cannon_width // 2 + i * (cannon_width // 3)
            wheel_y = second_cannon["y"] + cannon_height
            pygame.draw.circle(screen, BLACK, (wheel_x, wheel_y), wheel_radius)
            # Draw wheel rotation effect
            angle = wheel_rotation + i * 90
            pygame.draw.line(screen, WHITE, (wheel_x, wheel_y),
                             (wheel_x + wheel_radius * math.cos(math.radians(angle)),
                              wheel_y + wheel_radius * math.sin(math.radians(angle))), 2)

def draw_floor():
    pygame.draw.rect(screen, floor_color, (0, HEIGHT - floor_height, WIDTH, floor_height))

def draw_projectiles():
    for projectile in projectiles:
        pygame.draw.circle(screen, BLACK, (int(projectile["x"]), int(projectile["y"])), projectile_radius)

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
        elif shape["number"] == 8:
            # Draw octagon
            points = [
                (shape["x"] + shape["size"] * 0.3, shape["y"]),
                (shape["x"] + shape["size"] * 0.7, shape["y"]),
                (shape["x"] + shape["size"], shape["y"] + shape["size"] * 0.3),
                (shape["x"] + shape["size"], shape["y"] + shape["size"] * 0.7),
                (shape["x"] + shape["size"] * 0.7, shape["y"] + shape["size"]),
                (shape["x"] + shape["size"] * 0.3, shape["y"] + shape["size"]),
                (shape["x"], shape["y"] + shape["size"] * 0.7),
                (shape["x"], shape["y"] + shape["size"] * 0.3)
            ]
            pygame.draw.polygon(screen, shape["color"], points)
        # Draw number
        text = font.render(str(shape["number"]), True, WHITE)
        screen.blit(text, (shape["x"] + shape["size"] // 2 - text.get_width() // 2,
                           shape["y"] + shape["size"] // 2 - text.get_height() // 2))

def draw_hexagon():
    global hexagon_glow_timer
    if hexagon:
        # Glowing effect
        glow_intensity = abs(math.sin(hexagon_glow_timer * math.pi * 2))
        glow_color = (int(hexagon_color[0] * glow_intensity),
                      int(hexagon_color[1] * glow_intensity),
                      int(hexagon_color[2] * glow_intensity))
        # Draw hexagon
        points = [
            (hexagon["x"] + hexagon_size * 0.5, hexagon["y"]),
            (hexagon["x"] + hexagon_size, hexagon["y"] + hexagon_size * 0.3),
            (hexagon["x"] + hexagon_size, hexagon["y"] + hexagon_size * 0.7),
            (hexagon["x"] + hexagon_size * 0.5, hexagon["y"] + hexagon_size),
            (hexagon["x"], hexagon["y"] + hexagon_size * 0.7),
            (hexagon["x"], hexagon["y"] + hexagon_size * 0.3)
        ]
        pygame.draw.polygon(screen, glow_color, points)
        hexagon_glow_timer += 0.05  # Adjust glow speed

def spawn_shape():
    shape = {
        "x": random.randint(0, WIDTH - 50),
        "y": 0,
        "size": 60,  # Larger shapes
        "number": random.choice([1, 2, 3, 4, 8]),  # Add 8 to possible shapes
        "color": random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE]),
        "dx": random.choice([-3, 3]),  # Faster horizontal movement
        "dy": shape_speed  # Vertical movement
    }
    shapes.append(shape)

def spawn_hexagon():
    global hexagon
    hexagon = {
        "x": random.randint(0, WIDTH - hexagon_size),
        "y": random.randint(0, HEIGHT // 2 - hexagon_size),  # Random y position above the middle of screen
        "size": hexagon_size
    }

def update_shapes():
    for shape in shapes:
        shape["x"] += shape["dx"]
        shape["y"] += shape["dy"]
        # Bounce off screen edges (left and right)
        if shape["x"] <= 0 or shape["x"] + shape["size"] >= WIDTH:
            shape["dx"] *= -1
        # Bounce off the floor
        if shape["y"] + shape["size"] >= HEIGHT - floor_height:
            shape["dy"] *= -1
        # Bounce off the top of the screen
        if shape["y"] <= 0:
            shape["dy"] *= -1
        # Remove shapes that go above the screen (optional, if you want them to disappear)
        if shape["y"] < -shape["size"]:
            shapes.remove(shape)

def check_collisions():
    global lives, flicker_start_time, score, second_cannon, second_cannon_start_time, hexagon
    for shape in shapes[:]:
        if (shape["x"] < cannon_x < shape["x"] + shape["size"] and
            shape["y"] < cannon_y < shape["y"] + shape["size"]):
            # Cannon is hit by a shape
            lives -= 1
            flicker_start_time = time.time()
            shapes.remove(shape)
            if lives <= 0:
                global current_state
                current_state = GAME_OVER
    for projectile in projectiles[:]:
        for shape in shapes[:]:
            if (shape["x"] < projectile["x"] < shape["x"] + shape["size"] and
                shape["y"] < projectile["y"] < shape["y"] + shape["size"]):
                # Hit the shape
                if shape["number"] == 1:
                    score += 1  # Increase score when a "1" shape is destroyed
                if shape["number"] > 1:
                    # Split the shape
                    if shape["number"] == 8:
                        # Split into two "4"s
                        for _ in range(2):
                            shapes.append({
                                "x": shape["x"],
                                "y": shape["y"],
                                "size": shape["size"],
                                "number": 4,
                                "color": shape["color"],
                                "dx": random.choice([-3, 3]),
                                "dy": -shape_speed  # Bounce upward
                            })
                    elif shape["number"] == 4:
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
        if hexagon and (hexagon["x"] < projectile["x"] < hexagon["x"] + hexagon_size and
                        hexagon["y"] < projectile["y"] < hexagon["y"] + hexagon_size):
            # Hit the hexagon
            second_cannon = {
                "x": cannon_x + cannon_width,  # Place second cannon next to the original
                "y": cannon_y,
                "start_time": time.time()
            }
            hexagon = None
            projectiles.remove(projectile)

def update_projectiles():
    for projectile in projectiles[:]:
        projectile["y"] -= projectile_speed
        if projectile["y"] < 0:
            projectiles.remove(projectile)

def draw_button(x, y, width, height, text, color, hover_color, hover):
    color = hover_color if hover else color
    pygame.draw.rect(screen, color, (x, y, width, height))
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)

def draw_main_menu():
    screen.fill(background_color)
    mouse_pos = pygame.mouse.get_pos()
    start_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                          HEIGHT // 2 - button_height - 10 <= mouse_pos[1] <= HEIGHT // 2 - 10)
    options_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                            HEIGHT // 2 + 10 <= mouse_pos[1] <= HEIGHT // 2 + button_height + 10)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height - 10, button_width, button_height, "Start Game", button_color, button_hover_color, start_button_hover)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 10, button_width, button_height, "Options", button_color, button_hover_color, options_button_hover)

def draw_options_menu():
    screen.fill(background_color)
    mouse_pos = pygame.mouse.get_pos()
    cannon_color_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                                 HEIGHT // 2 - 2 * (button_height + 10) <= mouse_pos[1] <= HEIGHT // 2 - (button_height + 10))
    floor_color_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                                HEIGHT // 2 - (button_height + 10) <= mouse_pos[1] <= HEIGHT // 2 - 10)
    background_color_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                                     HEIGHT // 2 <= mouse_pos[1] <= HEIGHT // 2 + button_height)
    done_button_hover = (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                         HEIGHT // 2 + button_height + 10 <= mouse_pos[1] <= HEIGHT // 2 + 2 * (button_height + 10))
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 - 2 * (button_height + 10), button_width, button_height, "Cannon Color", cannon_color, button_hover_color, cannon_color_button_hover)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 - (button_height + 10), button_width, button_height, "Floor Color", floor_color, button_hover_color, floor_color_button_hover)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2, button_width, button_height, "Background Color", background_color, button_hover_color, background_color_button_hover)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 + button_height + 10, button_width, button_height, "Done", button_color, button_hover_color, done_button_hover)

def draw_game_over():
    screen.fill(background_color)
    text = font.render("Game Over", True, RED)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    draw_button(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50, button_width, button_height, "Main Menu", button_color, button_hover_color, False)

def change_color(option):
    current_index = color_options.index(options[option])
    new_index = (current_index + 1) % len(color_options)
    options[option] = color_options[new_index]
    if option == "cannon_color":
        global cannon_color
        cannon_color = options[option]
    elif option == "floor_color":
        global floor_color
        floor_color = options[option]
    elif option == "background_color":
        global background_color
        background_color = options[option]

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    if current_state == MAIN_MENU:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                    HEIGHT // 2 - button_height - 10 <= mouse_pos[1] <= HEIGHT // 2 - 10):
                    current_state = GAME
                    lives = 3  # Reset lives when starting a new game
                    score = 0  # Reset score when starting a new game
                    shapes.clear()  # Clear shapes when restarting
                    hexagon = None  # Reset hexagon
                    second_cannon = None  # Reset second cannon
                elif (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                      HEIGHT // 2 + 10 <= mouse_pos[1] <= HEIGHT // 2 + button_height + 10):
                    current_state = OPTIONS_MENU
    elif current_state == OPTIONS_MENU:
        draw_options_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                    HEIGHT // 2 - 2 * (button_height + 10) <= mouse_pos[1] <= HEIGHT // 2 - (button_height + 10)):
                    change_color("cannon_color")
                elif (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                      HEIGHT // 2 - (button_height + 10) <= mouse_pos[1] <= HEIGHT // 2 - 10):
                    change_color("floor_color")
                elif (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                      HEIGHT // 2 <= mouse_pos[1] <= HEIGHT // 2 + button_height):
                    change_color("background_color")
                elif (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                      HEIGHT // 2 + button_height + 10 <= mouse_pos[1] <= HEIGHT // 2 + 2 * (button_height + 10)):
                    current_state = MAIN_MENU
    elif current_state == GAME:
        screen.fill(background_color)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Fire a projectile on mouse click
                projectiles.append({"x": cannon_x, "y": cannon_y - 30})

        # Move cannon to follow the mouse
        mouse_x, _ = pygame.mouse.get_pos()
        cannon_x = mouse_x
        # Ensure the cannon stays within the screen bounds
        cannon_x = max(cannon_width // 2, min(cannon_x, WIDTH - cannon_width // 2))

        # Spawn shapes
        shape_spawn_timer += 1
        if shape_spawn_timer >= shape_spawn_delay:
            spawn_shape()
            shape_spawn_timer = 0

        # Spawn hexagon
        hexagon_spawn_timer += 1 / 60  # Increment by frame time
        if hexagon_spawn_timer >= hexagon_spawn_delay and not hexagon:
            spawn_hexagon()
            hexagon_spawn_timer = 0

        # Update game objects
        update_shapes()
        update_projectiles()
        check_collisions()

        # Draw game objects
        draw_floor()
        draw_cannon()
        if second_cannon:
            draw_second_cannon()
        draw_projectiles()
        draw_shapes()
        if hexagon:
            draw_hexagon()

        # Draw lives and score
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(lives_text, (10, 10))
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 50))

        # Handle second cannon firing
        if second_cannon:
            current_time = time.time()
            if current_time - second_cannon["start_time"] >= second_cannon_duration:
                second_cannon = None  # Remove second cannon after duration ends
            elif current_time - last_second_cannon_shot_time >= second_cannon_fire_delay:
                # Fire a projectile from the second cannon
                projectiles.append({"x": second_cannon["x"], "y": second_cannon["y"] - 30})
                last_second_cannon_shot_time = current_time

    elif current_state == GAME_OVER:
        draw_game_over()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if (WIDTH // 2 - button_width // 2 <= mouse_pos[0] <= WIDTH // 2 + button_width // 2 and
                    HEIGHT // 2 + 50 <= mouse_pos[1] <= HEIGHT // 2 + 50 + button_height):
                    current_state = MAIN_MENU

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()