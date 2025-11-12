import pygame
import random

# Start the pygame library
pygame.init()

# Game variables
screen_width = 600
screen_height = 600
bird_width = 40
bird_height = 40
gravity = 0.95
jump_speed = -9
sky_color = (135, 206, 235)
bird_color = (0, 0, 255)
BLACK = (0, 0, 0)

# Week 2 variables
pipe_gap = 150
pipe_width = 60

# Set up game screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Flappy Birds")

# Set font
font = pygame.font.SysFont(None, 36)

# Bird class code
class Bird:
    def __init__(self):
        self.x = 50  # Bird starting position
        self.y = screen_height // 2  # Give bird middle screen position
        self.velocity = 0  # Bird's speed

    # Update bird position based on gravity
    def update(self):
        self.velocity += gravity  # Adds gravity as bird falls
        self.y += self.velocity  # Move bird down by how fast it's falling

    # Bird jump when space is pressed
    def jump(self):
        self.velocity = jump_speed  # Change bird speed to make it go up

    # Draw the bird
    def draw(self):
        pygame.draw.rect(screen, bird_color, (self.x, self.y, bird_width, bird_height))


# Pipe class
class Pipe:
    def __init__(self):
        self.x = screen_width
        self.height = random.randint(100, screen_height - pipe_gap)
        self.top = self.height - screen_height
        self.bottom = self.height + pipe_gap
        self.color = self.random_color()

    @staticmethod
    def random_color():
        # Generate random colors
        return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

    def update(self):
        self.x -= 5  # Move pipes to the left

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.top, pipe_width, screen_height))
        pygame.draw.rect(screen, self.color, (self.x, self.bottom, pipe_width, screen_height))


# Function for handling collisions and game over
def check_collision(bird, pipes):
    if bird.y <= 0 or bird.y >= screen_height:  # Bird hits the top or bottom
        return True
    for pipe in pipes:
        if pipe.x < bird.x + bird_width and pipe.x + pipe_width > bird.x:
            if bird.y < pipe.height or bird.y + bird_height > pipe.bottom:
                return True
    return False


# Main game loop
def game_loop():
    bird = Bird()
    pipes = [Pipe()]
    clock = pygame.time.Clock()
    score = 0

    running = True
    while running:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

        # Update bird and pipes
        bird.update()

        for pipe in pipes:
            pipe.update()
            if pipe.x + pipe_width < 0:  # If pipe is out of the screen
                pipes.remove(pipe)
                pipes.append(Pipe())  # Add a new pipe
                score += 1

        if check_collision(bird, pipes):  # Check if bird collides with pipes or boundary
            print(f"Game Over! Score: {score}")
            running = False

        # Draw everything
        screen.fill(sky_color)
        bird.draw()
        for pipe in pipes:
            pipe.draw()

        # Display score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        pygame.display.update()

    pygame.quit()


# Start the main game loop
game_loop()