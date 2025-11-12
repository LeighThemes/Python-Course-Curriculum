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
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Fonts
font = pygame.font.Font(None, 36)

# Game states
MAIN_MENU = 0
OPTIONS_MENU = 1
GAME = 2
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

# Projectile settings
projectiles = []
projectile_speed = 10
projectile_radius = 8  # Increased size of cannonball

# Shapes settings
shapes = []
shape_speed = 3
shape_spawn_delay = 120  # Shapes appear less often
shape_spawn_timer = 0

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

def draw_cannon():
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
    for projectile in projectiles[:]:
        for shape in shapes[:]:
            if (shape["x"] < projectile["x"] < shape["x"] + shape["size"] and
                shape["y"] < projectile["y"] < shape["y"] + shape["size"]):
                # Hit the shape
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