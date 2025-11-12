import pygame
import random
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Dropper")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)

# Button settings
button_rect = pygame.Rect(WIDTH - 780, 20, 100, 50)

class GameObject: #TODO
    

class Ball(GameObject):
    def __init__(self, x, y):
        # TODO - Get access to the parent method
        self.radius = 15
        self.y_velocity = 0
        self.gravity = 0.5
        self.bounce_factor = 0.7
        self.energy_loss = 0.9
        self.bounces = 0
        self.max_bounces = 8
    
    def update(self):
        if not self.active:
            return
            
        # Apply gravity
        self.y_velocity += self.gravity
        self.y += self.y_velocity
        
        # Check for ground collision
        if self.y + self.radius >= HEIGHT:
            self.y = HEIGHT - self.radius
            self.y_velocity = -self.y_velocity * self.bounce_factor
            self.bounce_factor *= self.energy_loss
            self.bounces += 1
            
            # Deactivate after enough bounces
            if self.bounces >= self.max_bounces:
                self.active = False
    
    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius)

class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        self.balls = []
        self.font = pygame.font.Font(None, 36)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    # Create new ball at random x position
                    x = random.randint(50, WIDTH - 50)
                    self.balls.append(Ball(x, 50))
    
    def update(self):
        # Update all active balls
        for ball in self.balls[:]:
            ball.update()
            if not ball.active:
                self.balls.remove(ball)
    
    def draw_button(self):
        pygame.draw.rect(screen, RED, button_rect)
        text = self.font.render("Drop", True, WHITE)
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
    
    def draw(self):
        screen.fill(WHITE)
        
        # Draw ground
        pygame.draw.rect(screen, GRAY, (0, HEIGHT - 10, WIDTH, 10))
        
        # Draw all active balls
        for ball in self.balls:
            ball.draw(screen)
        
        # Draw button
        self.draw_button()
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()