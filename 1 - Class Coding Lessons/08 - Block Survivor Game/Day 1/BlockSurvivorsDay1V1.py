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
        
    def move(self, dx, dy):
        self.x = max(self.size, min(WIDTH - self.size, self.x + dx * self.speed))
        self.y = max(self.size, min(HEIGHT - self.size, self.y + dy * self.speed))
        
    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, (self.x - self.size//2, self.y - self.size//2, self.size, self.size))
        
    def can_shoot(self):
        return self.shoot_cooldown <= 0
        
    def shoot(self, target_x, target_y):
        if self.can_shoot():
            self.shoot_cooldown = self.shoot_delay
            return Bullet(self.x, self.y, target_x, target_y)
        return None
        
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
        self.level_shoot_delays = {1: 90, 2: 50}
        self.round_time = 30
        self.last_enemy_spawn = 0
        self.enemy_spawn_delay = 1000
        self.start_time = 0
        self.time_when_died = 0  # New variable to store death time
        self.upgrades = ["Faster Shooting"]
        self.restart_button = Button(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 50, "Restart", GREEN, (100, 255, 100))
        
    def reset_level(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.start_time = pygame.time.get_ticks()
        self.last_enemy_spawn = 0
        self.player.shoot_delay = self.level_shoot_delays.get(self.level, 30)
        if self.level == 2:
            self.round_time = 45
            
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
            bullet = self.player.shoot(closest_enemy.x, closest_enemy.y)
            if bullet:
                self.bullets.append(bullet)
        
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    elif self.state == GameState.MENU:
                        return False
        if self.state == GameState.MENU and mouse_click:
            self.state = GameState.PLAYING
            self.reset_level()
        elif self.state == GameState.GAME_OVER:
            self.restart_button.check_hover(mouse_pos)
            if self.restart_button.is_clicked(mouse_pos, mouse_click):
                self.state = GameState.MENU
                self.level = 1
        elif self.state == GameState.UPGRADE and mouse_click:
            if self.upgrades[0] == "Faster Shooting":
                self.player.shoot_delay = max(5, self.player.shoot_delay - 10)
            self.level += 1
            self.state = GameState.PLAYING
            self.reset_level()
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
                    self.time_when_died = (pygame.time.get_ticks() - self.start_time) / 1000  # Store death time
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
        self.screen.fill(WHITE)
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        elif self.state == GameState.UPGRADE:
            self.draw_upgrade_screen()
            
        pygame.display.flip()
        
    def draw_menu(self):
        title = self.font.render("ROGUE-LIKE SHOOTER", True, BLACK)
        start = self.font.render("Click to Start", True, BLACK)
        controls = self.small_font.render("WASD to Move, Auto Shooting", True, BLACK)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 50))
        self.screen.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT//2 + 20))
        self.screen.blit(controls, (WIDTH//2 - controls.get_width()//2, HEIGHT//2 + 70))
        
    def draw_game(self):
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        
        health_text = self.font.render(f"Health: {self.player.health}", True, BLACK)
        score_text = self.font.render(f"Score: {self.player.score}", True, BLACK)
        
        # Use time_when_died if game over, otherwise calculate normally
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
        if self.upgrades[0] == "Faster Shooting":
            new_delay = max(5, self.player.shoot_delay - 10)
            upgrade_text = self.font.render(f"Upgrade: {self.upgrades[0]} (Delay: {self.player.shoot_delay}→{new_delay})", True, WHITE)
        click = self.font.render("Click to continue", True, WHITE)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
        self.screen.blit(score, (WIDTH//2 - score.get_width()//2, HEIGHT//2 - 30))
        self.screen.blit(upgrade_text, (WIDTH//2 - upgrade_text.get_width()//2, HEIGHT//2 + 20))
        self.screen.blit(click, (WIDTH//2 - click.get_width()//2, HEIGHT//2 + 70))
        
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