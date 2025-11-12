import pygame
import sys
import random

# Initiate pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Block - Infinite Climb")

# Color variables
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
NEW_BG_COLOR = (0, 128, 128)  # New background color for the next level

# Player variables
player_width = 50
player_height = 80
player_x = 300
player_y = HEIGHT - player_height - 100
player_velocity = 5
player_jump = 15
spring_jump = 25  # Jump boost for springs
fall_speed = 0
on_ground = False

# Floor variables
ground_height = 50
ground = pygame.Rect(0, HEIGHT - ground_height, WIDTH, ground_height)

# Platforms (initial level)
platforms = [
    pygame.Rect(50, HEIGHT - 150, 200, 20),
    pygame.Rect(300, HEIGHT - 250, 200, 20),
    pygame.Rect(550, HEIGHT - 350, 200, 20),
    pygame.Rect(300, HEIGHT - 450, 180, 20),
    pygame.Rect(50, HEIGHT - 550, 170, 20),
    pygame.Rect(300, HEIGHT - 650, 160, 20),
    pygame.Rect(550, HEIGHT - 750, 150, 20),
    pygame.Rect(50, HEIGHT - 850, 140, 20),
    pygame.Rect(300, HEIGHT - 950, 100, 20),
    pygame.Rect(550, HEIGHT - 1050, 130, 20),
    pygame.Rect(50, HEIGHT - 1150, 140, 20),
    pygame.Rect(300, HEIGHT - 1250, 100, 20),
    pygame.Rect(550, HEIGHT - 1350, 150, 20),
    pygame.Rect(300, -940, 80, 80)  # "Win" platform at the top
]

# Platforms with springs (indices correspond to platforms)
springs = [1, 4, 7, 10]  # Add springs to specific platforms

# Scroll offset
scroll_offset = 0

# Game over flag
game_over = False
won_game = False  # Flag to track if the player wins
current_level = 1  # Flag to track current level

# Background
def draw_background():
    global current_level
    if current_level == 1:
        screen.fill(SKY_BLUE)
    elif current_level == 2:
        screen.fill(NEW_BG_COLOR)

# Player
def draw_player(x, y):
    pygame.draw.rect(screen, BLUE, (x, y, player_width, player_height))

# Ground
def draw_ground():
    pygame.draw.rect(screen, BROWN, ground.move(0, scroll_offset))

# Draw platforms and springs
def draw_platforms():
    for i, plat in enumerate(platforms):
        # Check if the platform is the "win" platform (the last one in the list)
        if plat == platforms[-1]:
            pygame.draw.rect(screen, RED, plat.move(0, scroll_offset))  # Draw the win platform in red
        else:
            pygame.draw.rect(screen, GREEN, plat.move(0, scroll_offset))  # Draw other platforms in green

        # Draw a spring on platforms with springs
        if i in springs:
            spring_rect = plat.move(0, scroll_offset)
            spring_width = 130
            spring_height = 15
            pygame.draw.rect(screen, YELLOW, (spring_rect.x + spring_rect.width // 2 - spring_width // 2, spring_rect.y - spring_height, spring_width, spring_height))

# Collision detection
def check_collisions(player_rect):
    global fall_speed, on_ground, won_game
    on_ground = False

    # Check if the player is on the ground
    if player_rect.colliderect(ground.move(0, scroll_offset)):
        fall_speed = 0
        player_rect.bottom = ground.move(0, scroll_offset).top
        on_ground = True

    # Check if player is on the platforms
    for i, plat in enumerate(platforms):
        if player_rect.colliderect(plat.move(0, scroll_offset)) and fall_speed > 0:
            if i in springs:
                fall_speed = -spring_jump  # Boost the player up if they land on a spring
            else:
                fall_speed = -0.55
            player_rect.bottom = plat.move(0, scroll_offset).top
            on_ground = True

            # Check if the player hits the "win" platform
            if plat == platforms[-1]:  # The last platform is the "win" platform
                won_game = True
            break

# Display game over message
def display_game_over():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over", True, RED)
    text_space = font.render("Press 1 to Restart", True, RED)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    screen.blit(text_space, (WIDTH // 2.5 - text.get_width() // 2, HEIGHT // 1.5 - text.get_height() // 2))

# Display win message
def display_win():
    font = pygame.font.Font(None, 74)
    text = font.render("You Win!", True, RED)
    text_space = font.render("Press 1 to Restart", True, RED)
    text_next = font.render("Press 2 for Next Level", True, RED)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    screen.blit(text_space, (WIDTH // 2.65 - text.get_width() // 2, HEIGHT // 1.5 - text.get_height() // 2))
    screen.blit(text_next, (WIDTH // 2.95 - text.get_width() // 2, HEIGHT // 1.25 - text.get_height() // 2))

# Reset the game state
def reset_game():
    global player_x, player_y, fall_speed, on_ground, scroll_offset, game_over, won_game, current_level
    player_x = 300
    player_y = HEIGHT - player_height - 100
    fall_speed = 0
    on_ground = False
    scroll_offset = 0
    game_over = False
    won_game = False
    current_level = 1  # Reset to level 1

#Generates new level for game
def generate_new_level():
    global platforms, springs, won_game, scroll_offset, SKY_BLUE

    # Clear existing platforms and springs for the new level
    platforms = []
    springs = []

    # Define new platform layout for the second level
    platforms = [
        pygame.Rect(100, HEIGHT - 200, 200, 20),
        pygame.Rect(350, HEIGHT - 300, 250, 20),
        pygame.Rect(600, HEIGHT - 400, 150, 20),
        pygame.Rect(150, HEIGHT - 500, 180, 20),
        pygame.Rect(400, HEIGHT - 600, 220, 20),
        pygame.Rect(650, HEIGHT - 700, 250, 20),
        pygame.Rect(250, HEIGHT - 800, 200, 20),
        pygame.Rect(500, HEIGHT - 900, 180, 20),
        pygame.Rect(50, HEIGHT - 1000, 170, 20),
        pygame.Rect(300, HEIGHT - 1100, 100, 20),
        pygame.Rect(550, HEIGHT - 1200, 140, 20),
        pygame.Rect(150, HEIGHT - 1300, 140, 20),
        pygame.Rect(400, HEIGHT - 1400, 120, 20),
        pygame.Rect(250, HEIGHT - 1600, 200, 20),
        pygame.Rect(500, HEIGHT - 1700, 180, 20),
        pygame.Rect(50, HEIGHT - 1800, 170, 20),
        pygame.Rect(400, HEIGHT - 1900, 170, 20),
        pygame.Rect(50, HEIGHT - 1970, 100, 20),
        pygame.Rect(300, -1770, 80, 80)  # "Win" platform at the top
    ]

    # Add springs to specific platforms
    springs = [2, 7, 10, 16]  # New springs for the second level

    # Change background color for the new level
    SKY_BLUE = (170, 150, 255)  # New color for the second level

    # Reset variables for the new level
    scroll_offset = 0
    won_game = False


# Game loop
def main():
    global player_x, player_y, fall_speed, on_ground, scroll_offset, game_over, won_game, current_level

    clock = pygame.time.Clock()

    # Game loop
    while True:
        draw_background()
        draw_ground()
        draw_platforms()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # If game over, display message and wait for 1 key press to restart
        if game_over:
            display_game_over()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_1]:
                reset_game()
            pygame.display.update()
            continue

        # If the player wins, display the win message and wait for 1 key press to restart
        if won_game:
            display_win()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_1]:
                reset_game()  # Reset the game back to level 1
            elif keys[pygame.K_2]:  # When '2' is pressed, go to the next level
                generate_new_level()  # Transition to the next level
            pygame.display.update()
            continue

        # Key press handling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_velocity
        if keys[pygame.K_RIGHT]:
            player_x += player_velocity
        if keys[pygame.K_SPACE] and on_ground:
            fall_speed = -player_jump
            on_ground = False

        # Prevent the player from going out of the screen on the left or right
        if player_x < 0:
            player_x = 0
        elif player_x + player_width > WIDTH:
            player_x = WIDTH - player_width

        # Apply gravity
        player_y += fall_speed
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

        # Check for collisions with the ground and platforms
        check_collisions(player_rect)

        # Apply gravity effect if the player is not on the ground
        if not on_ground:
            fall_speed += 1

        # Scrolling logic
        if player_y < HEIGHT // 4:
            scroll_amount = (HEIGHT // 4) - player_y
            scroll_offset += scroll_amount
            player_y += scroll_amount

        # Check if the bottom of the player touches the bottom of the screen
        if player_y + player_height > HEIGHT:
            game_over = True

        # Draw the player
        draw_player(player_x, player_y)

        # Update the display
        pygame.display.update()

        # Limit the frame rate to 60 frames per second
        clock.tick(60)

if __name__ == "__main__":
    main()
