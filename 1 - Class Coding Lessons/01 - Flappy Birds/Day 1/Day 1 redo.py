import pygame
import random

#start the pygame library
pygame.init()

#Game variables
screen_width = 600
screen_height = 600
bird_width = 40
bird_height = 40
gravity = 0.95
jump_speed = -9
sky_color = (135, 206, 235)
bird_color = (0,0, 255)

#set up game screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Flappy Birds")

#set font
font = pygame.font.SysFont(None, 36)

#Bird class code
#A class is a blueprint for our bird that helps us make our birds
class Bird:
    #This is what happends when we make a new bird
    def __init__(self):
        self.x = 50 #bird starting postion
        self.y = screen_height // 2 #give bird middle screen position
        self.velocity = 0 #bird's speed
        
    #bird postion based on gravity
    def update(self):
        self.velocity += gravity #adds gravity as bird falls
        self.y += self.velocity #move bird down by how fast its falling
        
    #bird jump when space pressed
    def jump(self):
        self.velocity = jump_speed #change bird speed to make it go up
        
    #this draws bird
    def draw(self):
      #This give bird its shape
        pygame.draw.rect(screen, bird_color, (self.x, self.y, bird_width, bird_height))
        
  # The game loop is where the game happens! This is the main part of the game
def game_loop():
    bird = Bird()  # Create a new bird object to control
    clock = pygame.time.Clock()  # Control how fast the game runs (frame rate)

    is_running = True  # Keep the game running until we decide to stop
    while is_running:
        clock.tick(30)  # Make the game run at 30 frames per second (slows it down)

        # Check for actions that the player wants to do
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False  # If we close the window, the game stops
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()  # If we press the spacebar, the bird jumps

        # Update the bird's position based on gravity and jumping
        bird.update()

        # Draw everything on the screen
        screen.fill(sky_color)  # First, fill the screen with the sky color (blue)
        bird.draw()  # Draw the bird in its new position

        # Show everything we've drawn on the screen
        pygame.display.update()

    pygame.quit()  # Close the game when we are done

# Start the game by calling the game loop
game_loop()

