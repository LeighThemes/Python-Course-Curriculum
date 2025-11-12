import pygame
import random

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
BIRD_WIDTH = 40
BIRD_HEIGHT = 40
PIPE_WIDTH = 60
PIPE_GAP = 150
GRAVITY = 0.95
JUMP_STRENGTH = -9
SKY = (135, 206, 235)
GREEN = (0, 255, 0)

# Colors
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Font setup
font = pygame.font.SysFont(None, 36)

# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.vel = 0

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

    def jump(self):
        self.vel = JUMP_STRENGTH

    def draw(self):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT))

# Pipe class
class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.height = random.randint(100, SCREEN_HEIGHT - PIPE_GAP)
        self.top = self.height - SCREEN_HEIGHT
        self.bottom = self.height + PIPE_GAP

    def update(self):
        self.x -= 5  # Move pipe to the left

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.top, PIPE_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(screen, GREEN, (self.x, self.bottom, PIPE_WIDTH, SCREEN_HEIGHT))

# Function for handling collisions and game over
def check_collision(bird, pipes):
    if bird.y <= 0 or bird.y >= SCREEN_HEIGHT:  # Bird hits the top or bottom
        return True
    for pipe in pipes:
        if pipe.x < bird.x + BIRD_WIDTH and pipe.x + PIPE_WIDTH > bird.x:
            if bird.y < pipe.height or bird.y + BIRD_HEIGHT > pipe.bottom:
                return True
    return False

# Main game loop
def game_loop():
    bird = Bird()
    pipes = [Pipe()]
    clock = pygame.time.Clock()
    score = 0
    background_x = 0

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
            if pipe.x + PIPE_WIDTH < 0:  # If pipe is out of the screen
                pipes.remove(pipe)
                pipes.append(Pipe())  # Add a new pipe
                score += 1

        if check_collision(bird, pipes):  # Check if bird collides with pipes or boundary
            print(f"Game Over! Score: {score}")
            running = False

        # Draw everything
        screen.fill(SKY)
        bird.draw()
        for pipe in pipes:
            pipe.draw()

        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        pygame.display.update()

    pygame.quit()

# Start the main game loop
game_loop()
