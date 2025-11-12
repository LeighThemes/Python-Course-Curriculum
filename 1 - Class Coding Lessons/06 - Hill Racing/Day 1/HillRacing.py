import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hill Climb Racing")

# Colors
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Fonts
font = pygame.font.Font(None, 36)

# Game states
MAIN_MENU = 0
GAME = 1
GAME_OVER = 2
current_state = MAIN_MENU

# Car settings
car_width, car_height = 80, 50
car_x = WIDTH // 2 - car_width // 2
car_y = HEIGHT // 2
car_speed_x = 0
car_speed_y = 0
car_acceleration = 0.1
car_deceleration = 0.05
car_brake = 0.5
car_max_speed = 10
car_fuel = 100
car_fuel_consumption = 0.1
car_angle = 0
wheel_radius = 10

# Ground settings
ground_y = HEIGHT - 100
ground_amplitude = 100
ground_wavelength = 800
ground_offset = 0

# Coin settings
coin_radius = 20
coins = []
coin_spawn_delay = 100
coin_spawn_timer = 0

# Fuel can settings
fuel_can_width, fuel_can_height = 30, 60
fuel_cans = []
fuel_spawn_delay = 500
fuel_spawn_timer = 0

# Score
score = 0

def draw_car():
    # Create a surface for the car body
    car_surface = pygame.Surface((car_width, car_height), pygame.SRCALPHA)
    pygame.draw.rect(car_surface, RED, (0, 0, car_width, car_height))

    # Rotate the car body
    rotated_car = pygame.transform.rotate(car_surface, car_angle)
    car_rect = rotated_car.get_rect(center=(car_x, car_y))
    screen.blit(rotated_car, car_rect.topleft)

    # Wheel positions relative to the car's center
    wheel_offset_x = car_width // 4
    wheel_offset_y = car_height // 2

    # Calculate wheel positions after reverse rotation
    angle_rad = math.radians(-car_angle)  # Reverse the angle
    wheel1_x = car_x + wheel_offset_x * math.cos(angle_rad) - wheel_offset_y * math.sin(angle_rad)
    wheel1_y = car_y + wheel_offset_x * math.sin(angle_rad) + wheel_offset_y * math.cos(angle_rad)
    wheel2_x = car_x - wheel_offset_x * math.cos(angle_rad) - wheel_offset_y * math.sin(angle_rad)
    wheel2_y = car_y - wheel_offset_x * math.sin(angle_rad) + wheel_offset_y * math.cos(angle_rad)

    # Draw wheels
    pygame.draw.circle(screen, BLACK, (int(wheel1_x), int(wheel1_y)), wheel_radius)
    pygame.draw.circle(screen, BLACK, (int(wheel2_x), int(wheel2_y)), wheel_radius)

def draw_ground():
    for x in range(0, WIDTH, 10):
        y = ground_y + ground_amplitude * math.sin((x + ground_offset) / ground_wavelength * 2 * math.pi)
        pygame.draw.rect(screen, BROWN, (x, y, 10, HEIGHT - y))
        pygame.draw.rect(screen, GREEN, (x, y - 10, 10, 10))

def draw_coins():
    for coin in coins:
        pygame.draw.circle(screen, GOLD, (int(coin["x"]), int(coin["y"])), coin_radius)

def draw_fuel_cans():
    for fuel_can in fuel_cans:
        pygame.draw.rect(screen, GREEN, (int(fuel_can["x"]), int(fuel_can["y"]), fuel_can_width, fuel_can_height))

def draw_hud():
    pygame.draw.rect(screen, GREEN, (10, 10, car_fuel, 20))
    pygame.draw.rect(screen, WHITE, (10, 10, 100, 20), 2)

    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH - 150, 10))

def spawn_coin():
    y = ground_y + ground_amplitude * math.sin((WIDTH + ground_offset) / ground_wavelength * 2 * math.pi) - coin_radius
    coins.append({"x": WIDTH, "y": y})

def spawn_fuel_can():
    y = ground_y + ground_amplitude * math.sin((WIDTH + ground_offset) / ground_wavelength * 2 * math.pi) - fuel_can_height
    fuel_cans.append({"x": WIDTH, "y": y})

def update_car():
    global car_y, car_speed_x, car_speed_y, car_angle, car_fuel, score

    car_speed_y += 0.2
    car_y += car_speed_y

    ground_height = ground_y + ground_amplitude * math.sin((car_x + ground_offset) / ground_wavelength * 2 * math.pi)

    if car_y + car_height // 2 > ground_height:
        car_y = ground_height - car_height // 2
        car_speed_y = 0

        slope = math.cos((car_x + ground_offset) / ground_wavelength * 2 * math.pi)
        car_angle = -math.degrees(math.atan(slope))

    car_fuel -= car_fuel_consumption
    if car_fuel <= 0:
        car_fuel = 0
        car_speed_x = 0
        global current_state
        current_state = GAME_OVER

def update_coins():
    global score
    for coin in coins[:]:
        coin["x"] -= car_speed_x
        if coin["x"] + coin_radius < 0:
            coins.remove(coin)
        if (car_x - car_width // 2 < coin["x"] < car_x + car_width // 2 and
            car_y - car_height // 2 < coin["y"] < car_y + car_height // 2):
            coins.remove(coin)
            score += 1

def update_fuel_cans():
    global car_fuel
    for fuel_can in fuel_cans[:]:
        fuel_can["x"] -= car_speed_x
        if fuel_can["x"] + fuel_can_width < 0:
            fuel_cans.remove(fuel_can)
        if (car_x - car_width // 2 < fuel_can["x"] < car_x + car_width // 2 and
            car_y - car_height // 2 < fuel_can["y"] < car_y + car_height // 2):
            fuel_cans.remove(fuel_can)
            car_fuel = min(100, car_fuel + 25)

def update_ground():
    global ground_offset
    ground_offset += car_speed_x

def draw_button(x, y, width, height, text, color, hover_color, hover):
    color = hover_color if hover else color
    pygame.draw.rect(screen, color, (x, y, width, height))
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)

def draw_main_menu():
    screen.fill(SKY_BLUE)
    mouse_pos = pygame.mouse.get_pos()
    start_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                          HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25)
    draw_button(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50, "Start Game", GREEN, (0, 200, 0), start_button_hover)

def draw_game_over():
    screen.fill(SKY_BLUE)
    game_over_text = font.render("Game Over", True, RED)
    screen.blit(game_over_text, (WIDTH // 2 - 70, HEIGHT // 2 - 50))
    mouse_pos = pygame.mouse.get_pos()
    restart_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                           HEIGHT // 2 + 25 <= mouse_pos[1] <= HEIGHT // 2 + 75)
    draw_button(WIDTH // 2 - 100, HEIGHT // 2 + 25, 200, 50, "Restart", GREEN, (0, 200, 0), restart_button_hover)

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
                if (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                    HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25):
                    current_state = GAME
                    car_fuel = 100
                    score = 0
                    coins.clear()
                    fuel_cans.clear()
                    ground_offset = 0
    elif current_state == GAME:
        screen.fill(SKY_BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            car_speed_x = min(car_max_speed, car_speed_x + car_acceleration)
        elif keys[pygame.K_LEFT]:
            car_speed_x = max(0, car_speed_x - car_brake)
        else:
            if car_speed_x > 0:
                car_speed_x = max(0, car_speed_x - car_deceleration)
            elif car_speed_x < 0:
                car_speed_x = min(0, car_speed_x + car_deceleration)

        update_car()
        update_coins()
        update_fuel_cans()
        update_ground()

        coin_spawn_timer += 1
        if coin_spawn_timer >= coin_spawn_delay:
            spawn_coin()
            coin_spawn_timer = 0

        fuel_spawn_timer += 1
        if fuel_spawn_timer >= fuel_spawn_delay:
            spawn_fuel_can()
            fuel_spawn_timer = 0

        draw_ground()
        draw_car()
        draw_coins()
        draw_fuel_cans()
        draw_hud()
    elif current_state == GAME_OVER:
        draw_game_over()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                    HEIGHT // 2 + 25 <= mouse_pos[1] <= HEIGHT // 2 + 75):
                    current_state = GAME
                    car_fuel = 100
                    score = 0
                    coins.clear()
                    fuel_cans.clear()
                    ground_offset = 0

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()