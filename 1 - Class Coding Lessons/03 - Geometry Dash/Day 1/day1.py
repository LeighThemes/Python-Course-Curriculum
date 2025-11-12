import pygame
import sys
import random

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometry Dash Clone")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Clock
clock = pygame.time.Clock()

# Player settings
player_size = 30
player_x = 100
player_y = HEIGHT - player_size - 50
player_jump = 15
gravity = 1
player_velocity_y = 0
on_ground = True

# Ground settings
ground_height = 50
ground = pygame.Rect(0, HEIGHT - ground_height, WIDTH, ground_height)

# Obstacle settings
obstacle_width = 30
obstacle_height = 50
obstacle_speed = 5
obstacles = []

# Game variables
game_speed = 60
score = 0
running = True

# Fonts
font = pygame.font.Font(None, 36)

# Add obstacles
def add_obstacle():
    x_pos = WIDTH + random.randint(100, 300)
    obstacle = pygame.Rect(x_pos, HEIGHT - obstacle_height - ground_height, obstacle_width, obstacle_height)
    obstacles.append(obstacle)

# Draw the player
def draw_player(x, y):
    pygame.draw.rect(screen, BLUE, (x, y, player_size, player_size))

# Draw ground
def draw_ground():
    pygame.draw.rect(screen, GREEN, ground)

# Draw obstacles
def draw_obstacles():
    for obstacle in obstacles:
        pygame.draw.rect(screen, RED, obstacle)

# Display score
def draw_score(score):
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

# Main game loop
def main():
    global player_y, player_velocity_y, on_ground, running, score

    # Initial obstacle spawn
    add_obstacle()

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Handle player jumping
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and on_ground:
            player_velocity_y = -player_jump
            on_ground = False

        # Update player position
        player_y += player_velocity_y
        if not on_ground:
            player_velocity_y += gravity

        # Check if player is on the ground
        if player_y + player_size >= HEIGHT - ground_height:
            player_y = HEIGHT - ground_height - player_size
            on_ground = True
            player_velocity_y = 0

        # Update obstacles
        for obstacle in obstacles:
            obstacle.x -= obstacle_speed

        # Remove obstacles that are off-screen
        obstacles[:] = [obstacle for obstacle in obstacles if obstacle.x + obstacle_width > 0]

        # Add new obstacles
        if len(obstacles) == 0 or obstacles[-1].x < WIDTH - 300:
            add_obstacle()

        # Collision detection
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        for obstacle in obstacles:
            if player_rect.colliderect(obstacle):
                running = False  # End the game on collision

        # Update score
        score += 1

        # Draw everything
        screen.fill(BLACK)
        draw_ground()
        draw_player(player_x, player_y)
        draw_obstacles()
        draw_score(score)

        # Update the display
        pygame.display.update()

        # Frame rate
        clock.tick(game_speed)

    # Game over screen
    game_over()

# Game over screen
def game_over():
    screen.fill(BLACK)
    game_over_text = font.render("Game Over", True, RED)
    restart_text = font.render("Press R to Restart", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2))
    pygame.display.update()

    # Wait for restart or quit
    global running, player_y, player_velocity_y, on_ground, score, obstacles
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            # Reset game variables
            player_y = HEIGHT - player_size - 50
            player_velocity_y = 0
            on_ground = True
            score = 0
            obstacles = []
            running = True
            main()

# Start the game
if __name__ == "__main__":
    main()
