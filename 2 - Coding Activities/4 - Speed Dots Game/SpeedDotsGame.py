import pygame
import random
import time

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Multi-Level Collector Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

## Game Object Classes
class GameObject:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(x, y, width, height)
    
    def update(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, BLUE)
        self.speed = 5
        self.score = 0
        self.inventory = {}
    
    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(0, min(self.x, 750))
        self.y = max(0, min(self.y, 550))
        self.update()
    
    def add_to_inventory(self, item_name):
        self.inventory[item_name] = self.inventory.get(item_name, 0) + 1

class Collectable(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 30, GREEN)
        self.collected = False
    
    def check_collision(self, player):
        if not self.collected and self.rect.colliderect(player.rect):
            self.collected = True
            return True
        return False

class SpeedBoost(Collectable):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = YELLOW
        self.boost_amount = 2
    
    def apply_boost(self, player):
        player.speed += self.boost_amount
        player.add_to_inventory("Speed Boost")

# Game States
class GameState:
    MENU = 0
    PLAYING = 1
    WIN = 2
    LEVEL_COMPLETE = 3

# Level Designs
def setup_level(level_num):
    player = Player(400, 300)
    collectables = []
    
    if level_num == 1:
        # Level 1 - Easy (5 items)
        positions = [(100, 100), (700, 100), (400, 300), (100, 500), (700, 500)]
        for x, y in positions:
            collectables.append(Collectable(x, y))
    
    elif level_num == 2:
        # Level 2 - Medium (8 items)
        positions = [
            (200, 150), (600, 150), 
            (150, 300), (650, 300),
            (200, 450), (600, 450),
            (400, 200), (400, 400)
        ]
        for i, (x, y) in enumerate(positions):
            if i % 3 == 0:  # Every 3rd is a speed boost
                collectables.append(SpeedBoost(x, y))
            else:
                collectables.append(Collectable(x, y))
    
    elif level_num == 3:
        # Level 3 - Hard (10 items)
        for i in range(10):
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            if i % 4 == 0:  # Every 4th is a speed boost
                collectables.append(SpeedBoost(x, y))
            else:
                collectables.append(Collectable(x, y))
    
    return player, collectables

# Menu Screen
def draw_menu(screen):
    screen.fill(BLACK)
    
    title = big_font.render("COLLECTOR GAME", True, BLUE)
    instruction1 = font.render("Collect all items in each level", True, WHITE)
    instruction2 = font.render("Press 1, 2, or 3 to select level", True, WHITE)
    instruction3 = font.render("Press ESC to quit", True, WHITE)
    
    level1 = font.render("1 - Easy Level", True, GREEN)
    level2 = font.render("2 - Medium Level", True, YELLOW)
    level3 = font.render("3 - Hard Level", True, RED)
    
    screen.blit(title, (400 - title.get_width()//2, 100))
    screen.blit(instruction1, (400 - instruction1.get_width()//2, 200))
    screen.blit(instruction2, (400 - instruction2.get_width()//2, 250))
    screen.blit(instruction3, (400 - instruction3.get_width()//2, 300))
    
    screen.blit(level1, (400 - level1.get_width()//2, 350))
    screen.blit(level2, (400 - level2.get_width()//2, 400))
    screen.blit(level3, (400 - level3.get_width()//2, 450))

# Win Screen
def draw_win_screen(screen, score, time_taken):
    screen.fill(PURPLE)
    
    win_text = big_font.render("YOU WIN!", True, WHITE)
    score_text = font.render(f"Final Score: {score}", True, WHITE)
    time_text = font.render(f"Total Time: {time_taken:.1f} seconds", True, WHITE)
    restart_text = font.render("Press R to return to menu", True, WHITE)
    
    screen.blit(win_text, (400 - win_text.get_width()//2, 150))
    screen.blit(score_text, (400 - score_text.get_width()//2, 250))
    screen.blit(time_text, (400 - time_text.get_width()//2, 300))
    screen.blit(restart_text, (400 - restart_text.get_width()//2, 400))

# Level Complete Screen
def draw_level_complete(screen, level, score, time_taken):
    screen.fill(ORANGE)
    
    complete_text = big_font.render(f"Level {level} Complete!", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    time_text = font.render(f"Time: {time_taken:.1f} seconds", True, WHITE)
    continue_text = font.render("Press N for next level", True, WHITE)
    menu_text = font.render("Press M for menu", True, WHITE)
    
    screen.blit(complete_text, (400 - complete_text.get_width()//2, 150))
    screen.blit(score_text, (400 - score_text.get_width()//2, 250))
    screen.blit(time_text, (400 - time_text.get_width()//2, 300))
    screen.blit(continue_text, (400 - continue_text.get_width()//2, 400))
    screen.blit(menu_text, (400 - menu_text.get_width()//2, 450))

# Main Game Loop
def main():
    running = True
    game_state = GameState.MENU
    current_level = 1
    max_levels = 3
    player = None
    collectables = []
    start_time = 0
    level_time = 0
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == GameState.MENU:
                    if event.key == pygame.K_1:
                        current_level = 1
                        player, collectables = setup_level(current_level)
                        game_state = GameState.PLAYING
                        start_time = time.time()
                    elif event.key == pygame.K_2:
                        current_level = 2
                        player, collectables = setup_level(current_level)
                        game_state = GameState.PLAYING
                        start_time = time.time()
                    elif event.key == pygame.K_3:
                        current_level = 3
                        player, collectables = setup_level(current_level)
                        game_state = GameState.PLAYING
                        start_time = time.time()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                
                elif game_state == GameState.WIN and event.key == pygame.K_r:
                    game_state = GameState.MENU
                
                elif game_state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_n and current_level < max_levels:
                        current_level += 1
                        player, collectables = setup_level(current_level)
                        game_state = GameState.PLAYING
                        start_time = time.time()
                    elif event.key == pygame.K_m:
                        game_state = GameState.MENU
        
        # Game logic
        if game_state == GameState.PLAYING:
            # Handle player input
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
            
            player.move(dx, dy)
            
            # Check for collisions
            for item in collectables[:]:
                if item.check_collision(player):
                    if isinstance(item, SpeedBoost):
                        item.apply_boost(player)
                    player.score += 10
                    collectables.remove(item)
            
            # Check level completion
            if len(collectables) == 0:
                level_time = time.time() - start_time
                if current_level == max_levels:
                    game_state = GameState.WIN
                else:
                    game_state = GameState.LEVEL_COMPLETE
        
        # Drawing
        screen.fill(BLACK)
        
        if game_state == GameState.MENU:
            draw_menu(screen)
        
        elif game_state == GameState.PLAYING:
            # Draw collectables
            for item in collectables:
                item.draw(screen)
            
            # Draw player
            player.draw(screen)
            
            # Draw UI
            current_time = time.time() - start_time
            time_text = font.render(f"Time: {current_time:.1f}s", True, WHITE)
            score_text = font.render(f"Score: {player.score}", True, WHITE)
            level_text = font.render(f"Level: {current_level}/{max_levels}", True, WHITE)
            remaining_text = font.render(f"Remaining: {len(collectables)}", True, WHITE)
            
            screen.blit(time_text, (10, 10))
            screen.blit(score_text, (10, 50))
            screen.blit(level_text, (10, 90))
            screen.blit(remaining_text, (10, 130))
        
        elif game_state == GameState.WIN:
            total_time = level_time + (time.time() - start_time if current_level == 1 else 0)
            draw_win_screen(screen, player.score, total_time)
        
        elif game_state == GameState.LEVEL_COMPLETE:
            draw_level_complete(screen, current_level, player.score, level_time)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()