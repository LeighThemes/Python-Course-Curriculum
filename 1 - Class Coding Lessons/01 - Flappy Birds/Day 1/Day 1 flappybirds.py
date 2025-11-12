import pygame
import random

# Initialize pygame
pygame.init()

# Constants and Configuration
SCREEN_WIDTH = 600  # Screen width
SCREEN_HEIGHT = 600  # Screen height
BIRD_WIDTH = 40  # Bird width
BIRD_HEIGHT = 40  # Bird height
GRAVITY = 0.95  # Gravity effect on the bird's movement
JUMP_STRENGTH = -9  # Strength of the bird's jump (negative to go up)
SKY = (135, 206, 235)  # Light blue color for the sky background

# Colors
BLUE = (0, 0, 255)  # Color for the bird (blue)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Set up the game window with given width and height
pygame.display.set_caption("Flappy Bird")  # Set the title of the window

# Font setup (not used in this basic version, but prepared for future text rendering)
font = pygame.font.SysFont(None, 36)

# Bird class to represent the player-controlled bird
class Bird:
    def __init__(self):
        self.x = 50  # Starting x position of the bird
        self.y = SCREEN_HEIGHT // 2  # Starting y position of the bird (center of the screen)
        self.vel = 0  # Initial velocity of the bird (0 for no movement)

    def update(self):
        # Apply gravity: increase velocity downward each frame
        self.vel += GRAVITY
        # Update the bird's y position based on velocity
        self.y += self.vel

    def jump(self):
        # When the spacebar is pressed, reset the velocity to make the bird jump upwards
        self.vel = JUMP_STRENGTH

    def draw(self):
        # Draw the bird as a blue rectangle at the current position
        pygame.draw.rect(screen, BLUE, (self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT))

# Main loop for testing the bird's movement and jumping
def game_loop():
    bird = Bird()  # Create a bird object
    clock = pygame.time.Clock()  # Control the frame rate of the game

    running = True  # Game loop flag
    while running:
        clock.tick(30)  # Set frame rate to 30 frames per second

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Quit the game if the user closes the window
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()  # Make the bird jump when spacebar is pressed

        # Update the bird's position based on gravity
        bird.update()

        # Draw everything on the screen
        screen.fill(SKY)  # Fill the screen with the sky color
        bird.draw()  # Draw the bird at its new position

        pygame.display.update()  # Update the display to show the new frame

    pygame.quit()  # Close the game when the loop ends

# Start the main game loop
game_loop()
