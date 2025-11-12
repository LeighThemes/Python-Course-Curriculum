import pygame
import random
import sys
import time

# Initialize pygame
pygame.init()

# Set up the display
width, height = 600, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Number Guessing Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 100, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Font
font = pygame.font.SysFont('Arial', 24)
large_font = pygame.font.SysFont('Arial', 36)

# Game variables
numbers = []
correct_number = 0
selected = None
message = ""
game_over = False
game_start_time = 0
game_duration = 25  # 25 seconds

def new_game():
    global numbers, correct_number, message, game_over, game_start_time
    numbers = random.sample(range(1, 101), 5)  # 5 unique numbers
    correct_number = random.choice(numbers)
    message = "Click the correct number: " + str(correct_number)
    game_over = False
    game_start_time = time.time()

# Start first game
new_game()

# Main game loop
clock = pygame.time.Clock()
while True:
    screen.fill(WHITE)
    
    # Calculate remaining time
    current_time = time.time()
    elapsed = current_time - game_start_time
    remaining_time = max(0, game_duration - elapsed)
    
    # End game if time runs out
    if remaining_time <= 0 and not game_over:
        game_over = True
        message = "Time's up! The number was " + str(correct_number)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over and remaining_time > 0:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if any number was clicked
            for i, num in enumerate(numbers):
                num_rect = pygame.Rect(50 + i*100, 150, 80, 80)
                if num_rect.collidepoint(mouse_pos):
                    if num == correct_number:
                        message = "Correct! Click to play again"
                        game_over = True
                    else:
                        message = "Wrong! Try again"
        
        # Click anywhere to start new game after game ends
        if event.type == pygame.MOUSEBUTTONDOWN and game_over:
            new_game()
    
    # Draw instructions
    text = font.render(message, True, BLACK)
    screen.blit(text, (50, 50))
    
    # Draw the numbers
    for i, num in enumerate(numbers):
        color = GREEN if game_over and num == correct_number else BLUE
        if game_over and num != correct_number:
            color = WHITE
        
        num_rect = pygame.Rect(50 + i*100, 150, 80, 80)
        
        pygame.draw.rect(screen, color, num_rect)
        pygame.draw.rect(screen, BLACK, num_rect, 2)
        
        num_text = large_font.render(str(num), True, BLACK)
        text_rect = num_text.get_rect(center=num_rect.center)
        screen.blit(num_text, text_rect)
    
    # Draw timer
    timer_color = RED if remaining_time < 5 else BLACK  # Turns red when 5 seconds left
    timer_text = font.render(f"Time left: {int(remaining_time)}s", True, timer_color)
    screen.blit(timer_text, (width//2 - 70, height - 50))
    
    # Draw progress bar
    progress_width = (remaining_time / game_duration) * (width - 100)
    pygame.draw.rect(screen, BLACK, (50, height - 30, width - 100, 10), 1)
    pygame.draw.rect(screen, YELLOW, (50, height - 30, progress_width, 10))
    
    pygame.display.flip()
    clock.tick(30)  # Limit to 30 FPS

pygame.quit()