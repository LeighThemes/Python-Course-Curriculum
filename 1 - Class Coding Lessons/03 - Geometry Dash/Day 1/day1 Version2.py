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
on_roof = False

# Floor settings (where the player can land and jump from)
floor_height = 50
floor = pygame.Rect(0, HEIGHT - floor_height, WIDTH, floor_height)

# Roof settings (where the player can land and jump from)
roof_height = 50
roof = pygame.Rect(0, 0, WIDTH, roof_height)

# Obstacle settings
obstacle_speed = 5
obstacles = []

# Background settings
background_speed = 2
background_color = (135, 206, 250)  # Light Blue background color

# Game variables
game_speed = 60
score = 0
running = True

# Fonts
font = pygame.font.Font(None, 36)

# Add obstacles with different shapes and sizes (on both roof and floor)
def add_obstacle():
    # Randomly select the type of obstacle
    shape_type = random.choice(['rect', 'triangle', 'roof_obstacle', 'floor_obstacle'])

    if shape_type == 'rect':
        # Random size and position for rectangular obstacles
        width = random.randint(30, 70)
        height = random.randint(40, 100)
        x_pos = WIDTH + random.randint(100, 300)
        obstacle = {'shape': 'rect', 'rect': pygame.Rect(x_pos, floor.y - height, width, height)}
    elif shape_type == 'triangle':
        # Random size and position for triangular obstacles
        width = random.randint(30, 70)
        height = random.randint(40, 100)
        x_pos = WIDTH + random.randint(100, 300)
        points = [
            (x_pos, floor.y - height),  # Top vertex
            (x_pos + width, floor.y),  # Bottom-right vertex
            (x_pos - width, floor.y)  # Bottom-left vertex
        ]
        obstacle = {'shape': 'triangle', 'points': points}
    elif shape_type == 'roof_obstacle':
        # Random size and position for obstacles on the roof
        width = random.randint(60, 100)
        height = 20  # Fixed height for roof obstacles
        x_pos = WIDTH + random.randint(100, 300)
        y_pos = random.randint(roof_height, roof_height + 50)  # Positioning the obstacle in the roof space
        obstacle = {'shape': 'roof_obstacle', 'rect': pygame.Rect(x_pos, y_pos, width, height)}
    elif shape_type == 'floor_obstacle':
        # Random size and position for obstacles on the floor
        width = random.randint(60, 100)
        height = 20  # Fixed height for floor obstacles
        x_pos = WIDTH + random.randint(100, 300)
        y_pos = floor.y - height  # Positioning the obstacle just above the floor
        obstacle = {'shape': 'floor_obstacle', 'rect': pygame.Rect(x_pos, y_pos, width, height)}

    obstacles.append(obstacle)

# Draw the player
def draw_player(x, y):
    pygame.draw.rect(screen, BLUE, (x, y, player_size, player_size))

# Draw roof
def draw_roof():
    pygame.draw.rect(screen, GREEN, roof)

# Draw floor
def draw_floor():
    pygame.draw.rect(screen, GREEN, floor)

# Draw obstacles (both rectangles, triangles, roof and floor obstacles)
def draw_obstacles():
    for obstacle in obstacles:
        if obstacle['shape'] == 'rect':
            pygame.draw.rect(screen, RED, obstacle['rect'])
        elif obstacle['shape'] == 'triangle':
            pygame.draw.polygon(screen, RED, obstacle['points'])
        elif obstacle['shape'] == 'roof_obstacle':
            pygame.draw.rect(screen, RED, obstacle['rect'])
        elif obstacle['shape'] == 'floor_obstacle':
            pygame.draw.rect(screen, RED, obstacle['rect'])

# Draw score
def draw_score(score):
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

# Main game loop
def main():
    global player_y, player_velocity_y, on_ground, on_roof, running, score

    # Initial obstacle spawn
    add_obstacle()

    # Background scrolling variables
    background_x = 0

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Handle player jumping
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            if on_ground:
                player_velocity_y = -player_jump
                on_ground = False
            elif on_roof:
                player_velocity_y = player_jump
                on_roof = False

        # Update player position
        player_y += player_velocity_y
        if not on_ground and not on_roof:
            player_velocity_y += gravity

        # Check if player is on the ground
        if player_y + player_size >= HEIGHT - floor_height:
            player_y = HEIGHT - player_size - floor_height
            on_ground = True
            player_velocity_y = 0

        # Check if player is on the roof
        if player_y <= roof_height:
            player_y = roof_height
            on_roof = True
            player_velocity_y = 0

        # Update obstacles
        for obstacle in obstacles:
            if obstacle['shape'] == 'rect':
                obstacle['rect'].x -= obstacle_speed
            elif obstacle['shape'] == 'triangle':
                # Move the entire triangle
                obstacle['points'] = [(x - obstacle_speed, y) for x, y in obstacle['points']]
            elif obstacle['shape'] == 'roof_obstacle':
                obstacle['rect'].x -= obstacle_speed
            elif obstacle['shape'] == 'floor_obstacle':
                obstacle['rect'].x -= obstacle_speed

        # Remove obstacles that are off-screen
        obstacles[:] = [obstacle for obstacle in obstacles if (obstacle['shape'] == 'rect' and obstacle['rect'].x + obstacle['rect'].width > 0) or
                        (obstacle['shape'] == 'triangle' and obstacle['points'][0][0] > 0) or
                        (obstacle['shape'] == 'roof_obstacle' and obstacle['rect'].x + obstacle['rect'].width > 0) or
                        (obstacle['shape'] == 'floor_obstacle' and obstacle['rect'].x + obstacle['rect'].width > 0)]

        # Add new obstacles
        if len(obstacles) == 0 or (obstacles[-1]['shape'] == 'rect' and obstacles[-1]['rect'].x < WIDTH - 300) or \
           (obstacles[-1]['shape'] == 'triangle' and obstacle['points'][0][0] < WIDTH - 300) or \
           (obstacles[-1]['shape'] == 'roof_obstacle' and obstacles[-1]['rect'].x < WIDTH - 300) or \
           (obstacles[-1]['shape'] == 'floor_obstacle' and obstacles[-1]['rect'].x < WIDTH - 300):
            add_obstacle()

        # Collision detection
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        for obstacle in obstacles:
            if obstacle['shape'] == 'rect' and player_rect.colliderect(obstacle['rect']):
                running = False  # End the game on collision
            elif obstacle['shape'] == 'triangle':
                # Check if the player collides with any of the triangle's points
                if player_rect.colliderect(pygame.Rect(obstacle['points'][0][0], obstacle['points'][0][1], obstacle['points'][1][0] - obstacle['points'][0][0], obstacle['points'][2][1] - obstacle['points'][0][1])):
                    running = False  # End the game on collision with a triangle
            elif obstacle['shape'] == 'roof_obstacle' and player_rect.colliderect(obstacle['rect']):
                # End the game if colliding with a roof obstacle
                running = False
            elif obstacle['shape'] == 'floor_obstacle' and player_rect.colliderect(obstacle['rect']):
                # End the game if colliding with a floor obstacle
                running = False

        # Update score
        score += 1

        # Scroll the background
        background_x -= background_speed
        if background_x <= -WIDTH:
            background_x = 0

        # Draw everything
        screen.fill(BLACK)  # Clear the screen

        # Draw the scrolling background
        screen.fill(background_color)  # Draw the background color
        screen.blit(screen, (background_x, 0))  # Draw the background once at the new position
        screen.blit(screen, (background_x + WIDTH, 0))  # Repeat the background for infinite scroll

        draw_roof()
        draw_floor()
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
            on_roof = False
            score = 0
            obstacles = []
            running = True
            main()

# Start the game
if __name__ == "__main__":
    main()
