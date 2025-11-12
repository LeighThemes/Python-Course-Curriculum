import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometry Dash - Level 1")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
CYAN = (105, 155, 200)
VIOLET = (138, 43, 226)
GRAY = (212, 175, 55)
BLACK = (0, 0, 0)
WAVE_COLOR = (0, 255, 255)  # Cyan color for the wave effect
GLOW_COLOR = (255, 255, 0, 100)  # Semi-transparent CYAN for glowing effect
GREEN = (0, 230, 0)

# Player settings
player_width, player_height = 40, 40
player_x = 100
player_y = HEIGHT - 100 - player_height
player_velocity = 0
gravity = 0.9
jump_strength = -12
on_ground = True

# Obstacles and platforms
obstacles = []
platforms = []
obstacle_timer = 0
platform_timer = 0

# Score
score = 0

# Game over flag
game_over = False
time_up = False  # New flag for timer expiration

# Timer settings
start_time = pygame.time.get_ticks()  # Start time in milliseconds
game_duration = 10  # Game duration in seconds

# Wave settings
wave_amplitude = 50
wave_frequency = 0.06
wave_offset = 0

# Space press tracking outside of game loop
space_pressed = False

def draw_player():
    pygame.draw.rect(screen, GRAY, (player_x, player_y, player_width, player_height))

def draw_obstacles():
    for obstacle in obstacles:
        pygame.draw.polygon(screen, VIOLET, obstacle)

def draw_ground():
    global wave_offset

    # Draw the glowing floor (CYAN)
    glow_rect = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    glow_surface = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
    glow_surface.fill(GLOW_COLOR)  # Apply the glowing effect
    screen.blit(glow_surface, (0, HEIGHT - 100))  # Draw the glow effect under the floor

    # Then draw the regular floor on top of the wave (CYAN)
    pygame.draw.rect(screen, CYAN, glow_rect)

def draw_waves():
    global wave_offset

    # Draw the wave effect in front of the floor (with cyan color)
    for x in range(0, WIDTH, 10):
        y_offset = int(wave_amplitude * math.sin(x * wave_frequency + wave_offset))  # Sine wave formula
        pygame.draw.line(screen, WAVE_COLOR, (x, HEIGHT - 220), (x, HEIGHT - 220 + y_offset), 3)

def draw_timer():
    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000  # Time elapsed in seconds
    remaining_time = max(0, game_duration - elapsed_time)  # Remaining time

    font = pygame.font.Font(None, 36)
    timer_text = font.render(f"Time Left: {remaining_time}s", True, WHITE)
    screen.blit(timer_text, (WIDTH - 200, 10))

    return remaining_time

def draw_score():
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

def draw_game_over(message):
    font = pygame.font.Font(None, 74)
    text = font.render(message, True, WHITE)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))

    font = pygame.font.Font(None, 36)
    restart_text = font.render("Press R to Restart", True, WHITE)
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2))

    # Display the score on the end screen
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 1.5))

def reset_game():
    global player_x, player_y, player_velocity, on_ground, obstacles, platforms, score, game_over, time_up, start_time
    player_x = 100
    player_y = HEIGHT - 100 - player_height
    player_velocity = 0
    on_ground = True
    obstacles = []
    platforms = []
    score = 0
    game_over = False
    time_up = False
    start_time = pygame.time.get_ticks()  # Reset timer

# Main game loop
running = True
while running:
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Jump only when space is pressed and player is on the ground
            if event.key == pygame.K_SPACE and not space_pressed and on_ground:
                player_velocity = jump_strength
                space_pressed = True
        elif event.type == pygame.KEYUP:
            # Release space to reset the space_pressed flag
            if event.key == pygame.K_SPACE:
                space_pressed = False

    # If game over or time's up, show the appropriate screen and wait for R to restart
    if game_over or time_up:
        message = "GAME OVER" if game_over else "YOU WIN"
        draw_game_over(message)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            reset_game()
        pygame.display.flip()
        clock.tick(60)
        continue

    # Gravity and player movement
    player_velocity += gravity
    player_y += player_velocity

    # Obstacle creation
    obstacle_timer += 1
    if obstacle_timer > 60:
        x = WIDTH
        height = random.randint(20, 60)
        obstacle = [
            [x, HEIGHT - 100],
            [x + 20, HEIGHT - 100 - height],
            [x + 40, HEIGHT - 100]
        ]
        obstacles.append(obstacle)
        obstacle_timer = 0

    # Update obstacles
    for obstacle in obstacles:
        for point in obstacle:
            point[0] -= 5
    obstacles = [obs for obs in obstacles if obs[0][0] > 0]

    # Check collision
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    if any(any(pygame.Rect(point[0], point[1], 1, 1).colliderect(player_rect) for point in obstacle) for obstacle in obstacles):
        game_over = True

    # Ensure player stays on ground
    if player_y + player_height >= HEIGHT - 100:
        player_y = HEIGHT - 100 - player_height
        on_ground = True
        player_velocity = 0

    # Scoring
    score += 1

    # Update wave offset to animate the wave
    wave_offset += 0.1

    # Check timer
    remaining_time = draw_timer()
    if remaining_time == 0:
        time_up = True

    # Drawing
    draw_player()
    draw_obstacles()
    draw_ground()
    draw_waves()
    draw_score()

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
