import pygame
import random

# Initialize Pygame
pygame.init()

# Set screen dimensions
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Jumping Block Game")

# Colors
WHITE = (255, 255, 255)
BLUE = (135, 206, 235)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)

# Game variables
block_width = 50
block_height = 50
block_x = 100
block_y = screen_height - block_height - 50
block_vel = 5
jumping = False
jump_count = 10
gravity = 0.5

# Platform variables
platforms = [(200, 500, 200, 20), (400, 400, 200, 20), (600, 300, 200, 20)]
platform_color = BROWN

# Cloud background variables
clouds = []
cloud_speed = 1
for i in range(5):
    clouds.append([random.randint(i * 200, i * 200 + 400), random.randint(50, 150)])

# Initialize clock
clock = pygame.time.Clock()

# Game loop
run = True
while run:
    clock.tick(60)  # FPS set to 60
    screen.fill(BLUE)  # Fill the screen with sky blue color

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Cloud movement (loops from right to left)
    for cloud in clouds:
        cloud[0] -= cloud_speed
        if cloud[0] < -100:
            cloud[0] = screen_width + 100  # Reset cloud to the right side
            cloud[1] = random.randint(50, 150)  # Random height for the cloud

    # Draw clouds
    for cloud in clouds:
        pygame.draw.ellipse(screen, WHITE, (cloud[0], cloud[1], 100, 60))

    # Handle block movement
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] and block_x > 0:
        block_x -= block_vel - block_vel
    if keys[pygame.K_RIGHT] and block_x < screen_width - block_width:
        block_x += block_vel - block_vel
        # Move platforms when the right arrow key is pressed
        for i, platform in enumerate(platforms):
            platforms[i] = (platform[0] - block_vel, platform[1], platform[2], platform[3])

            # Reappear platforms from the right when they go off-screen
            if platforms[i][0] < -platforms[i][2]:
                platforms[i] = (screen_width, random.randint(100, screen_height - 150), platforms[i][2], platforms[i][3])

    if keys[pygame.K_SPACE] and not jumping:
        jumping = True

    if jumping:
        block_y -= jump_count * 2
        jump_count -= 1
        if jump_count < -10:
            jumping = False
            jump_count = 10

    # Gravity
    if block_y < screen_height - block_height - 50:
        block_y += gravity
    else:
        block_y = screen_height - block_height - 50

    # Draw the floor (ground)
    pygame.draw.rect(screen, BLACK, (0, screen_height - 50, screen_width, 50))

    # Draw platforms
    for platform in platforms:
        pygame.draw.rect(screen, platform_color, platform)

    # Draw the block
    pygame.draw.rect(screen, GREEN, (block_x, block_y, block_width, block_height))

    # Update the display
    pygame.display.update()

# Quit Pygame
pygame.quit()
