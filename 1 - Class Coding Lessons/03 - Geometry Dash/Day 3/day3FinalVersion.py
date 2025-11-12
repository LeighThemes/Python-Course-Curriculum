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
RED = (255, 0, 0)  # Color for the line obstacle
BLUE = (0, 0, 255)

# Player settings
player_width, player_height = 40, 40
player_x = 100
player_y = HEIGHT - 100 - player_height
player_velocity = 0
gravity = 0.8
jump_strength = -15
on_ground = True
can_jump = True  # Flag to track if the player can jump
space_pressed = False  # Track space bar state

# Obstacles and platforms
obstacles = []
platforms = []
line_obstacle = None  # New line obstacle variable
obstacle_timer = 0
platform_timer = 0

# Score
score = 0

# Game over flag
game_over = False
time_up = False  # New flag for timer expiration

# Timer settings
start_time = pygame.time.get_ticks()  # Start time in milliseconds
game_duration = 15  # Game duration in seconds

# Wave settings
wave_amplitude = 50
wave_frequency = 0.06
wave_offset = 0

# Space press tracking outside of game loop
space_pressed = False

# New variables for the yellow ball
yellow_ball = None
ball_lifted = False
ball_lift_time = 0

def create_obstacle():
    x = WIDTH
    height = random.randint(20, 60)
    shape_type = random.choice(["triangle", "square"])  # Randomly choose between triangle and square
    if shape_type == "triangle":
        # Create a triangle obstacle
        obstacle = [
            [x, HEIGHT - 100],
            [x + 20, HEIGHT - 100 - height],
            [x + 40, HEIGHT - 100]
        ]
    else:
        # Create a square obstacle
        side = random.randint(20, 40)  # Random side length for square
        obstacle = [
            [x, HEIGHT - 100 - side],
            [x + side, HEIGHT - 100 - side],
            [x + side, HEIGHT - 100],
            [x, HEIGHT - 100]
        ]
    
    return obstacle, shape_type

def create_line_obstacle():
    # Create a vertical line obstacle at a random x-position near the right side of the screen
    x_pos = WIDTH  # Start from the right edge
    return [(x_pos, 0), (x_pos, HEIGHT)]  # Line from top to bottom

def create_yellow_ball():
    # Create a yellow ball at a random position
    x = 900
    y = random.randint(HEIGHT - 170, HEIGHT - 150)
    return pygame.Rect(x, y, 30, 30)  # Size of the yellow ball is 30x30

def draw_player():
    pygame.draw.rect(screen, GRAY, (player_x, player_y, player_width, player_height))

def draw_obstacles():
    current_time = pygame.time.get_ticks() / 1000  # Time in seconds for smooth animation
    for obstacle, shape_type in obstacles:
        # Fluctuate size of the obstacle
        fluctuation = 10 * math.sin(current_time * 2)  # Speed up the fluctuation

        if shape_type == "triangle":
            # Modify the triangle's height
            modified_obstacle = [
                [obstacle[0][0], obstacle[0][1]],
                [obstacle[1][0], obstacle[1][1] - fluctuation],
                [obstacle[2][0], obstacle[2][1]]
            ]
            pygame.draw.polygon(screen, VIOLET, modified_obstacle)
        elif shape_type == "square":
            # Modify the square's position and size
            side = obstacle[1][0] - obstacle[0][0]  # Calculate the side length of square
            modified_obstacle = [
                [obstacle[0][0], obstacle[0][1] - fluctuation],
                [obstacle[1][0], obstacle[1][1] - fluctuation],
                [obstacle[2][0], obstacle[2][1] - fluctuation],
                [obstacle[3][0], obstacle[3][1] - fluctuation]
            ]
            pygame.draw.polygon(screen, GREEN, modified_obstacle)

def draw_line_obstacle():
    global line_obstacle, game_over
    obstacle_speed = 5  # Same speed as the obstacles

    # Move the line obstacle horizontally from right to left at the same speed as the obstacles
    if line_obstacle:
        line_obstacle[0] = (line_obstacle[0][0] - obstacle_speed, line_obstacle[0][1])  # Move the line's starting point left
        line_obstacle[1] = (line_obstacle[1][0] - obstacle_speed, line_obstacle[1][1])  # Move the line's ending point left

        # Check if the line passes the player
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        line_rect = pygame.Rect(line_obstacle[0][0], line_obstacle[0][1], 10, HEIGHT)  # Line as a vertical rectangle
        
        # Check if the player is on the ground by comparing the player's y-position
        if player_y + player_height >= HEIGHT - 100:
            # Player is on the ground
            if line_rect.colliderect(player_rect):
                game_over = True  # Game over if on the ground and the line hits the player
        else:
            # Player is not on the ground (in the air)
            if line_rect.colliderect(player_rect):
                game_over = False  # Allow passing through the line while in the air

        # Reset the line obstacle once it goes off the screen on the left
        if line_obstacle[0][0] < 0:
            line_obstacle = create_line_obstacle()  # Reset the line to start at the right edge

        pygame.draw.line(screen, BLUE, line_obstacle[0], line_obstacle[1], 10)

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

    # Fluctuate wave amplitude over time
    fluctuation_amplitude = wave_amplitude + 10 * math.sin(pygame.time.get_ticks() / 500)  # Adjust amplitude fluctuation
    for x in range(0, WIDTH, 10):
        y_offset = int(fluctuation_amplitude * math.sin(x * wave_frequency + wave_offset))  # Apply fluctuation
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

def draw_yellow_ball():
    if yellow_ball:
        pygame.draw.circle(screen, (255, 255, 0), yellow_ball.center, 15)  # Draw yellow ball

def check_player_grab_ball():
    global player_y, ball_lifted, ball_lift_time, yellow_ball

    if yellow_ball and player_rect.colliderect(yellow_ball):
        ball_lifted = True
        ball_lift_time = pygame.time.get_ticks()
        # Remove yellow ball once it's collected
        yellow_ball.x = -50  # Move it off-screen

def lift_player():
    global player_y, ball_lifted, ball_lift_time
    if ball_lifted:
        # Lift player above the floor for 5 seconds
        lift_duration = 5000  # 5 seconds
        elapsed_time = pygame.time.get_ticks() - ball_lift_time
        if elapsed_time < lift_duration:
            player_y = 20  # Lift the player
        else:
            ball_lifted = False  # Stop lifting after 5 seconds
            
def update_yellow_ball():
    global yellow_ball, ball_lifted, ball_lift_time

    # If the ball was collected, check for the respawn delay
    if ball_lifted:
        elapsed_time = pygame.time.get_ticks() - ball_lift_time
        if elapsed_time >= 5000:  # 5 seconds after being collected
            # Respawn the yellow ball on the right side of the screen
            yellow_ball = create_yellow_ball()
            ball_lifted = False  # Reset the lifted flag
            ball_lift_time = 0  # Reset the collection time
    else:
        # Move the yellow ball from left to right
        if yellow_ball:
            yellow_ball.x -= 2.75  # Move 3 pixels per frame

            # If the yellow ball goes off the right side, respawn it
            if yellow_ball.x < 0:
                yellow_ball = create_yellow_ball()  # Respawn the yellow ball on the right side

def reset_game():
    global player_x, player_y, player_velocity, on_ground, obstacles, platforms, score, game_over, time_up, start_time, line_obstacle, yellow_ball
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
    line_obstacle = create_line_obstacle()  # Reset the line obstacle
    yellow_ball = create_yellow_ball()  # Reset the yellow ball


# Game level variable
level = 1  # Start at level 1

# Main game loop
running = True
line_obstacle = create_line_obstacle()  # Create the line obstacle at the start
yellow_ball = create_yellow_ball()  # Create the yellow ball at the start

while running:
    screen.fill(BLACK)

    # Event handling (as before)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not space_pressed and on_ground and can_jump:
                player_velocity = jump_strength
                space_pressed = True
                can_jump = False  # Prevent jumping again until landing
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_pressed = False

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

    # Obstacle creation and movement
    obstacle_timer += 1
    if obstacle_timer > 60:
        new_obstacle, shape_type = create_obstacle()
        obstacles.append((new_obstacle, shape_type))
        obstacle_timer = 0

    for obstacle, _ in obstacles:
        for point in obstacle:
            point[0] -= 5
    obstacles = [(obs, shape) for obs, shape in obstacles if obs[0][0] > 0]

    # Check collision with obstacles
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    if any(any(pygame.Rect(point[0], point[1], 1, 1).colliderect(player_rect) for point in obstacle) for obstacle, _ in obstacles):
        game_over = True
        ball_lifted = False

    # Check collision with line obstacle if we are in level 2
    if level == 2 and line_obstacle and player_rect.colliderect(pygame.Rect(line_obstacle[0][0], line_obstacle[0][1] - 10, 100, 10)):
        if player_velocity < 0:
            game_over = True
            ball_lifted = False

    if player_y + player_height >= HEIGHT - 100:
        player_y = HEIGHT - 100 - player_height
        on_ground = True
        player_velocity = 0
        can_jump = True  # Allow jumping again once on the ground

    # Scoring
    score += 1

    # Timer and wave effect
    wave_offset += 0.1
    remaining_time = draw_timer()
    if remaining_time == 0:
        time_up = True

    # Update the yellow ball's position
    update_yellow_ball()

    # Draw player, obstacles, ground, waves, etc.
    draw_player()
    draw_obstacles()
    
    if level == 2:  # Only draw the line obstacle in Level 2
        draw_line_obstacle()

    draw_ground()
    draw_waves()
    draw_score()

    # Draw and handle yellow ball
    draw_yellow_ball()
    check_player_grab_ball()

    # Lift player if ball is collected
    lift_player()

    # Update display
    pygame.display.flip()
    clock.tick(60)

    # Switch to level 2 when time is up (for example)
    if remaining_time == 0 and level == 1:
        level = 2  # Transition to Level 2

pygame.quit()
sys.exit()
