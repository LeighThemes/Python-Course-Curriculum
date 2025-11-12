import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hill Climb Racing")

# Colors
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Fonts
font = pygame.font.Font(None, 36)

# Game states
MAIN_MENU = 0
GAME = 1
GAME_OVER = 2


class Car: #TODO

class Ground:
    def __init__(self):
        self.y = HEIGHT - 100
        self.amplitude = 100
        self.wavelength = 800
        self.offset = 0

    def draw(self):
        for x in range(0, WIDTH, 10):
            y = self.y + self.amplitude * math.sin((x + self.offset) / self.wavelength * 2 * math.pi)
            pygame.draw.rect(screen, BROWN, (x, y, 10, HEIGHT - y))
            pygame.draw.rect(screen, GREEN, (x, y - 10, 10, 10))

    def update(self, car_speed_x):
        self.offset += car_speed_x

    def get_height_at(self, x):
        return self.y + self.amplitude * math.sin((x + self.offset) / self.wavelength * 2 * math.pi)


class Coin:
    def __init__(self, x, y):
        self.radius = 20
        self.x = x
        self.y = y

    def draw(self):
        pygame.draw.circle(screen, GOLD, (int(self.x), int(self.y)), self.radius)

    def update(self, car_speed_x):
        self.x -= car_speed_x


class FuelCan:
    def __init__(self, x, y):
        self.width = 30
        self.height = 60
        self.x = x
        self.y = y

    def draw(self):
        pygame.draw.rect(screen, GREEN, (int(self.x), int(self.y), self.width, self.height))

    def update(self, car_speed_x):
        self.x -= car_speed_x


class Game:
    def __init__(self):
        self.car = Car()
        self.ground = Ground()
        self.coins = []
        self.fuel_cans = []
        self.coin_spawn_delay = 100
        self.coin_spawn_timer = 0
        self.fuel_spawn_delay = 500
        self.fuel_spawn_timer = 0
        self.score = 0
        self.current_state = MAIN_MENU

    def draw_hud(self):
        # Draw fuel meter
        pygame.draw.rect(screen, GREEN, (10, 10, self.car.fuel, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 100, 20), 2)  # Fuel meter border

        # Draw score
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 150, 10))

    def draw_button(self, x, y, width, height, text, color, hover_color, hover):
        color = hover_color if hover else color
        pygame.draw.rect(screen, color, (x, y, width, height))
        text_surface = font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text_surface, text_rect)

    def draw_main_menu(self):
        screen.fill(SKY_BLUE)
        mouse_pos = pygame.mouse.get_pos()
        start_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                              HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25)
        self.draw_button(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50, "Start Game", GREEN, (0, 200, 0), start_button_hover)

    def draw_game_over(self):
        screen.fill(SKY_BLUE)
        game_over_text = font.render("Game Over", True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - 70, HEIGHT // 2 - 50))
        mouse_pos = pygame.mouse.get_pos()
        restart_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                               HEIGHT // 2 + 25 <= mouse_pos[1] <= HEIGHT // 2 + 75)
        self.draw_button(WIDTH // 2 - 100, HEIGHT // 2 + 25, 200, 50, "Restart", GREEN, (0, 200, 0), restart_button_hover)

    def update_coins(self):
        for coin in self.coins[:]:
            coin.update(self.car.speed_x)
            if coin.x + coin.radius < 0:
                self.coins.remove(coin)
            if (self.car.x - self.car.width // 2 < coin.x < self.car.x + self.car.width // 2 and
                self.car.y - self.car.height // 2 < coin.y < self.car.y + self.car.height // 2):
                self.score += 1
                self.coins.remove(coin)

    def update_fuel_cans(self):
        for fuel_can in self.fuel_cans[:]:
            fuel_can.update(self.car.speed_x)
            if fuel_can.x + fuel_can.width < 0:
                self.fuel_cans.remove(fuel_can)
            if (self.car.x - self.car.width // 2 < fuel_can.x < self.car.x + self.car.width // 2 and
                self.car.y - self.car.height // 2 < fuel_can.y < self.car.y + self.car.height // 2):
                self.fuel_cans.remove(fuel_can)
                self.car.fuel = min(100, self.car.fuel + 25)

    def reset_game(self):
        self.car = Car()
        self.ground = Ground()
        self.coins.clear()
        self.fuel_cans.clear()
        self.score = 0

    def run(self):
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.current_state == MAIN_MENU:
                        if (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                            HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25):
                            self.current_state = GAME
                            self.reset_game()
                    elif self.current_state == GAME_OVER:
                        if (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                            HEIGHT // 2 + 25 <= mouse_pos[1] <= HEIGHT // 2 + 75):
                            self.current_state = GAME
                            self.reset_game()

            if self.current_state == MAIN_MENU:
                self.draw_main_menu()
            elif self.current_state == GAME:
                screen.fill(SKY_BLUE)

                keys = pygame.key.get_pressed()
                if keys[pygame.K_RIGHT]:
                    self.car.speed_x = min(self.car.max_speed, self.car.speed_x + self.car.acceleration)
                elif keys[pygame.K_LEFT]:
                    self.car.speed_x = max(0, self.car.speed_x - self.car.brake)
                else:
                    if self.car.speed_x > 0:
                        self.car.speed_x = max(0, self.car.speed_x - self.car.deceleration)
                    elif self.car.speed_x < 0:
                        self.car.speed_x = min(0, self.car.speed_x + self.car.deceleration)

                # Update game objects
                self.ground.update(self.car.speed_x)
                self.current_state = self.car.update(self.ground)

                self.update_coins()
                self.update_fuel_cans()

                # Spawn coins
                self.coin_spawn_timer += 1
                if self.coin_spawn_timer >= self.coin_spawn_delay:
                    y = self.ground.get_height_at(WIDTH) - Coin(0, 0).radius
                    self.coins.append(Coin(WIDTH, y))
                    self.coin_spawn_timer = 0

                # Spawn fuel cans
                self.fuel_spawn_timer += 1
                if self.fuel_spawn_timer >= self.fuel_spawn_delay:
                    y = self.ground.get_height_at(WIDTH) - FuelCan(0, 0).height
                    self.fuel_cans.append(FuelCan(WIDTH, y))
                    self.fuel_spawn_timer = 0

                # Draw game objects
                self.ground.draw()
                self.car.draw()
                for coin in self.coins:
                    coin.draw()
                for fuel_can in self.fuel_cans:
                    fuel_can.draw()
                self.draw_hud()
            elif self.current_state == GAME_OVER:
                self.draw_game_over()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()