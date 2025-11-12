import pygame
import sys

#initiate pygame
pygame.init()

#set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super block - level 1")

#color variables
WHITE = (255,255,255)
GREEN = (0, 255, 0)
BLUE = (0,0,255)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)

# player variables
player_width = 50
player_height = 80
player_x = 300
player_y = HEIGHT - player_height - 100
player_velocity = 5
player_jump = 15
fall_speed = 0
on_ground = False

#floor variables
ground_height = 50
ground = pygame.Rect(0, HEIGHT - ground_height, WIDTH, ground_height)

#platform
platforms = [
    pygame.Rect(50, HEIGHT - 150, 200, 20),
    pygame.Rect(300, HEIGHT - 250, 200, 20),
    pygame.Rect(550, HEIGHT - 350, 200, 20)
]

#background
def draw_background():
    screen.fill(SKY_BLUE)
    
#player
def draw_player(x,y):
    pygame.draw.rect(screen, BLUE, (x,y,player_width,player_height))
    
#ground
def draw_ground():
    pygame.draw.rect(screen, BROWN, ground)
    
#draw platforms
def draw_platforms():
    for plat in platforms:
        pygame.draw.rect(screen, GREEN, plat)
    
#collision detection
def check_collisions(player_rect):
    global fall_speed, on_ground
    on_ground = False
    
    #check if the player is on the ground
    if player_rect.colliderect(ground):
        fall_speed = 0
        player_rect.bottom = ground.top
        on_ground = True
        
    #check if player is on the platforms
    for plat in platforms:
        if player_rect.colliderect(plat) and fall_speed > 0:
            fall_speed = -0.55
            player_rect.bottom = plat.top
            on_ground = True
            break
          
# Game loop
def main():
    global player_x, player_y, fall_speed, on_ground

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
            player_x = 0  # Player bounces back to the left edge
        elif player_x + player_width > WIDTH:
            player_x = WIDTH - player_width  # Player bounces back to the right edge

        # Apply gravity
        player_y += fall_speed
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

        # Check for collisions with the ground and platforms
        check_collisions(player_rect)

        # Apply gravity effect if the player is not on the ground
        if not on_ground:
            fall_speed += 1  # Increase fall speed if not on ground

        # Draw the player
        draw_player(player_x, player_y)

        # Update the display
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()