import pygame
import sys
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    UPGRADE = 3
    OPTIONS = 4
    CREDITS = 5

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.size = 15
        self.speed = 5
        self.health = 3
        self.max_health = 3
        self.score = 0
        self.shoot_cooldown = 0
        self.base_shoot_delay = 30
        self.shoot_delay = self.base_shoot_delay
        self.color = BLACK
        self.shape = "square"  # Can be "square" or "circle"
        self.double_shot = False
        
    def move(self, dx, dy):
        self.x = max(self.size, min(WIDTH - self.size, self.x + dx * self.speed))
        self.y = max(self.size, min(HEIGHT - self.size, self.y + dy * self.speed))
        
    def draw(self, screen):
        if self.shape == "square":
            pygame.draw.rect(screen, self.color, (self.x - self.size//2, self.y - self.size//2, self.size, self.size))
        else:  # circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size//2)
        
    def can_shoot(self):
        return self.shoot_cooldown <= 0
        
    def shoot(self, target_x, target_y):
        bullets = []
        if self.can_shoot():
            self.shoot_cooldown = self.shoot_delay
            bullets.append(Bullet(self.x, self.y, target_x, target_y))
            if self.double_shot:
                # Add slight angle variation for second bullet
                angle = math.atan2(target_y - self.y, target_x - self.x)
                angle += math.radians(10)  # 10 degree offset
                dist = math.sqrt((target_x-self.x)**2 + (target_y-self.y)**2)
                new_target_x = self.x + dist * math.cos(angle)
                new_target_y = self.y + dist * math.sin(angle)
                bullets.append(Bullet(self.x, self.y, new_target_x, new_target_y))
        return bullets
        
    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        self.radius = 5
        self.speed = 10
        self.damage = 1
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx*dx + dy*dy)
        self.vx = (dx / dist) * self.speed if dist > 0 else 0
        self.vy = (dy / dist) * self.speed if dist > 0 else 0
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        
    def is_off_screen(self):
        return (self.x < -self.radius or self.x > WIDTH + self.radius or 
                self.y < -self.radius or self.y > HEIGHT + self.radius)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.speed = random.uniform(1.0, 2.5)
        self.health = 1
        self.color = random.choice([GREEN, BLUE, YELLOW, PURPLE, CYAN])
        
    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            
    def draw(self, screen):
        points = [
            (self.x, self.y - self.size),
            (self.x - self.size, self.y + self.size),
            (self.x + self.size, self.y + self.size)
        ]
        pygame.draw.polygon(screen, self.color, points)
        
    def collides_with(self, bullet):
        distance = math.sqrt((self.x - bullet.x)**2 + (self.y - bullet.y)**2)
        return distance < self.size + bullet.radius

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont(None, 36)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, 20, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.color = color
        self.dragging = False
        self.update_knob()
        
    def update_knob(self):
        normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_rect.x = self.rect.x + int(normalized * (self.rect.width - self.knob_rect.width))
        
    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, self.color, self.knob_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            knob_x = max(self.rect.x, min(self.rect.x + self.rect.width - self.knob_rect.width, mouse_x))
            self.knob_rect.x = knob_x
            normalized = (knob_x - self.rect.x) / (self.rect.width - self.knob_rect.width)
            self.value = self.min_val + normalized * (self.max_val - self.min_val)
            return True
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rogue-like Shooter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.state = GameState.MENU
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.level = 1
        self.level_shoot_delays = {1: 40, 2: 20}
        self.round_time = 30
        self.last_enemy_spawn = 0
        self.enemy_spawn_delay = 1000
        self.start_time = 0
        self.time_when_died = 0
        self.upgrades = [
            {"name": "Faster Shooting", "description": "Reduces shoot delay by 10"},
            {"name": "Double Shot", "description": "Shoot two bullets at once"}
        ]
        
        # Menu buttons
        self.start_button = Button(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50, "Start", GREEN, (100, 255, 100))
        self.options_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 50, "Options", BLUE, (100, 100, 255))
        self.credits_button = Button(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50, "Credits", YELLOW, (255, 255, 100))
        self.back_button = Button(20, HEIGHT - 70, 100, 50, "Back", RED, (255, 100, 100))
        
        # Options
        self.bg_color = WHITE
        self.color_slider = Slider(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 20, 0, 5, 0, BLUE)
        self.player_color_slider = Slider(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 20, 0, 5, 0, BLUE)
        self.player_shape_button = Button(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 50, "Shape: Square", PURPLE, (200, 100, 200))
        
        # Upgrade buttons
        self.upgrade_buttons = [
            Button(WIDTH//2 - 250, HEIGHT//2 - 50, 200, 100, "Faster Shooting", GREEN, (100, 255, 100)),
            Button(WIDTH//2 + 50, HEIGHT//2 - 50, 200, 100, "Double Shot", BLUE, (100, 100, 255))
        ]
        
        self.restart_button = Button(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 50, "Restart", GREEN, (100, 255, 100))
        
    def reset_level(self):
        self.player = Player()
        self.player.color = self.get_player_color()
        self.player.shape = "circle" if "circle" in self.player_shape_button.text else "square"
        self.bullets = []
        self.enemies = []
        self.start_time = pygame.time.get_ticks()
        self.last_enemy_spawn = 0
        self.player.shoot_delay = self.level_shoot_delays.get(self.level, 30)
        if self.level == 2:
            self.round_time = 45
            
    def get_bg_color(self):
        colors = [WHITE, (230, 230, 230), (200, 200, 255), (255, 200, 200), (200, 255, 200), (220, 220, 255)]
        return colors[int(self.color_slider.value)]
    
    def get_player_color(self):
        colors = [BLACK, RED, BLUE, GREEN, PURPLE, YELLOW]
        return colors[int(self.player_color_slider.value)]
            
    def spawn_enemy(self):
        side = random.randint(0, 3)
        if side == 0:
            x = random.randint(0, WIDTH)
            y = -20
        elif side == 1:
            x = WIDTH + 20
            y = random.randint(0, HEIGHT)
        elif side == 2:
            x = random.randint(0, WIDTH)
            y = HEIGHT + 20
        else:
            x = -20
            y = random.randint(0, HEIGHT)
        self.enemies.append(Enemy(x, y))
        
    def find_closest_enemy(self):
        closest_enemy = None
        min_distance = float('inf')
        for enemy in self.enemies:
            distance = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy
        return closest_enemy
        
    def auto_shoot(self):
        closest_enemy = self.find_closest_enemy()
        if closest_enemy:
            new_bullets = self.player.shoot(closest_enemy.x, closest_enemy.y)
            if new_bullets:
                self.bullets.extend(new_bullets)
        
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            
            if self.state == GameState.OPTIONS:
                self.color_slider.handle_event(event)
                self.player_color_slider.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    elif self.state in [GameState.OPTIONS, GameState.CREDITS]:
                        self.state = GameState.MENU
                    elif self.state == GameState.MENU:
                        return False
        
        # Menu screen
        if self.state == GameState.MENU:
            self.start_button.check_hover(mouse_pos)
            self.options_button.check_hover(mouse_pos)
            self.credits_button.check_hover(mouse_pos)
            
            if mouse_click:
                if self.start_button.is_clicked(mouse_pos, True):
                    self.state = GameState.PLAYING
                    self.reset_level()
                elif self.options_button.is_clicked(mouse_pos, True):
                    self.state = GameState.OPTIONS
                elif self.credits_button.is_clicked(mouse_pos, True):
                    self.state = GameState.CREDITS
        
        # Game over screen
        elif self.state == GameState.GAME_OVER:
            self.restart_button.check_hover(mouse_pos)
            if mouse_click and self.restart_button.is_clicked(mouse_pos, True):
                self.state = GameState.MENU
                self.level = 1
        
        # Upgrade screen
        elif self.state == GameState.UPGRADE:
            for i, button in enumerate(self.upgrade_buttons):
                button.check_hover(mouse_pos)
                if mouse_click and button.is_clicked(mouse_pos, True):
                    if i == 0:  # Faster Shooting
                        self.player.shoot_delay = max(5, self.player.shoot_delay - 10)
                    elif i == 1:  # Double Shot
                        self.player.double_shot = True
                    self.level += 1
                    self.state = GameState.PLAYING
                    self.reset_level()
        
        # Options screen
        elif self.state == GameState.OPTIONS:
            self.back_button.check_hover(mouse_pos)
            self.player_shape_button.check_hover(mouse_pos)
            
            if mouse_click:
                if self.back_button.is_clicked(mouse_pos, True):
                    self.state = GameState.MENU
                elif self.player_shape_button.is_clicked(mouse_pos, True):
                    if "Square" in self.player_shape_button.text:
                        self.player_shape_button.text = "Shape: Circle"
                    else:
                        self.player_shape_button.text = "Shape: Square"
        
        # Credits screen
        elif self.state == GameState.CREDITS:
            self.back_button.check_hover(mouse_pos)
            if mouse_click and self.back_button.is_clicked(mouse_pos, True):
                self.state = GameState.MENU
        
        return True
        
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if dx != 0 or dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx, dy = dx/length, dy/length
            self.player.move(dx, dy)
            
        self.player.update()
        self.auto_shoot()
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_enemy_spawn > self.enemy_spawn_delay:
            self.spawn_enemy()
            self.last_enemy_spawn = current_time
            
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_off_screen():
                self.bullets.remove(bullet)
                
        for enemy in self.enemies[:]:
            enemy.update(self.player)
            distance = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
            if distance < enemy.size + self.player.size//2:
                self.player.health -= 1
                self.enemies.remove(enemy)
                if self.player.health <= 0:
                    self.time_when_died = (pygame.time.get_ticks() - self.start_time) / 1000
                    self.state = GameState.GAME_OVER
                continue
                
            for bullet in self.bullets[:]:
                if enemy.collides_with(bullet):
                    enemy.health -= bullet.damage
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy.health <= 0:
                        self.player.score += 10
                        self.enemies.remove(enemy)
                    break
                    
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
        if elapsed >= self.round_time:
            self.state = GameState.UPGRADE
                
    def draw(self):
        # Set background color based on options
        if self.state == GameState.OPTIONS:
            self.screen.fill(WHITE)
        else:
            self.screen.fill(self.get_bg_color())
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        elif self.state == GameState.UPGRADE:
            self.draw_upgrade_screen()
        elif self.state == GameState.OPTIONS:
            self.draw_options_screen()
        elif self.state == GameState.CREDITS:
            self.draw_credits_screen()
            
        pygame.display.flip()
        
    def draw_menu(self):
        title = self.font.render("ROGUE-LIKE SHOOTER", True, BLACK)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
        
        self.start_button.draw(self.screen)
        self.options_button.draw(self.screen)
        self.credits_button.draw(self.screen)
        
    def draw_game(self):
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        
        health_text = self.font.render(f"Health: {self.player.health}", True, BLACK)
        score_text = self.font.render(f"Score: {self.player.score}", True, BLACK)
        
        if self.state == GameState.GAME_OVER:
            time_left = max(0, self.round_time - self.time_when_died)
        else:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
            time_left = max(0, self.round_time - elapsed)
            
        time_text = self.font.render(f"Time: {time_left:.1f}", True, BLACK)
        level_text = self.font.render(f"Level: {self.level}", True, BLACK)
        
        self.screen.blit(health_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 10))
        self.screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))
        
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        game_over = self.font.render("GAME OVER", True, RED)
        score = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        
        self.screen.blit(game_over, (WIDTH//2 - game_over.get_width()//2, HEIGHT//2 - 50))
        self.screen.blit(score, (WIDTH//2 - score.get_width()//2, HEIGHT//2))
        
        self.restart_button.draw(self.screen)
        
    def draw_upgrade_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font.render("LEVEL COMPLETE!", True, GREEN)
        score = self.font.render(f"Score: {self.player.score}", True, WHITE)
        prompt = self.font.render("Choose an upgrade:", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
        self.screen.blit(score, (WIDTH//2 - score.get_width()//2, HEIGHT//2 - 100))
        self.screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 50))
        
        for i, button in enumerate(self.upgrade_buttons):
            button.draw(self.screen)
            desc = self.small_font.render(self.upgrades[i]["description"], True, WHITE)
            self.screen.blit(desc, (button.rect.x, button.rect.y + button.rect.height + 5))
        
    def draw_options_screen(self):
        title = self.font.render("OPTIONS", True, BLACK)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        bg_text = self.font.render("Background Color:", True, BLACK)
        self.screen.blit(bg_text, (WIDTH//2 - bg_text.get_width()//2, HEIGHT//2 - 100))
        self.color_slider.draw(self.screen)
        
        player_color_text = self.font.render("Player Color:", True, BLACK)
        self.screen.blit(player_color_text, (WIDTH//2 - player_color_text.get_width()//2, HEIGHT//2))
        self.player_color_slider.draw(self.screen)
        
        self.player_shape_button.draw(self.screen)
        
        # Preview
        preview_text = self.small_font.render("Preview:", True, BLACK)
        self.screen.blit(preview_text, (WIDTH//2 - preview_text.get_width()//2, HEIGHT//2 + 160))
        preview_player = Player()
        preview_player.x = WIDTH//2
        preview_player.y = HEIGHT//2 + 200
        preview_player.color = self.get_player_color()
        preview_player.shape = "circle" if "circle" in self.player_shape_button.text else "square"
        preview_player.draw(self.screen)
        
        self.back_button.draw(self.screen)
        
    def draw_credits_screen(self):
        title = self.font.render("CREDITS", True, BLACK)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        line1 = self.font.render("Game developed by", True, BLACK)
        line2 = self.font.render("Your Name Here", True, BLACK)
        line3 = self.small_font.render("Using Python and Pygame", True, BLACK)
        
        self.screen.blit(line1, (WIDTH//2 - line1.get_width()//2, HEIGHT//2 - 50))
        self.screen.blit(line2, (WIDTH//2 - line2.get_width()//2, HEIGHT//2))
        self.screen.blit(line3, (WIDTH//2 - line3.get_width()//2, HEIGHT//2 + 50))
        
        self.back_button.draw(self.screen)
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()