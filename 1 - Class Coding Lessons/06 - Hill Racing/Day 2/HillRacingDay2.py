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


class Car:
    def __init__(self):
        self.width = 80
        self.height = 50
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT // 2
        self.speed_x = 0
        self.speed_y = 0
        self.acceleration = 0.2  # Increased acceleration
        self.deceleration = 0.05
        self.brake = 0.5
        self.max_speed = 20  # Increased max speed for more momentum
        self.fuel = 100
        self.fuel_consumption = 0.1
        self.angle = 0
        self.wheel_radius = 10
        self.in_air = False
        self.angular_velocity = 0  # How fast the car is spinning
        self.jump_threshold = 10  # Speed required to gain airtime
        self.gravity = 0.4  # Reduced gravity for longer airtime
        self.air_resistance = 0.98  # Reduced air resistance for more speed
        self.spin_damping = 0.99  # Reduced damping for longer spins

    def draw(self):
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, RED, (0, 0, self.width, self.height))
        rotated_car = pygame.transform.rotate(car_surface, self.angle)
        car_rect = rotated_car.get_rect(center=(self.x, self.y))
        screen.blit(rotated_car, car_rect.topleft)

        wheel_offset_x = self.width // 4
        wheel_offset_y = self.height // 2
        angle_rad = math.radians(-self.angle)
        wheel1_x = self.x + wheel_offset_x * math.cos(angle_rad) - wheel_offset_y * math.sin(angle_rad)
        wheel1_y = self.y + wheel_offset_x * math.sin(angle_rad) + wheel_offset_y * math.cos(angle_rad)
        wheel2_x = self.x - wheel_offset_x * math.cos(angle_rad) - wheel_offset_y * math.sin(angle_rad)
        wheel2_y = self.y - wheel_offset_x * math.sin(angle_rad) + wheel_offset_y * math.cos(angle_rad)

        pygame.draw.circle(screen, BLACK, (int(wheel1_x), int(wheel1_y)), self.wheel_radius)
        pygame.draw.circle(screen, BLACK, (int(wheel2_x), int(wheel2_y)), self.wheel_radius)

    def update(self, ground):
        # Apply gravity
        self.speed_y += self.gravity
        self.y += self.speed_y

        # Check if the car is on the ground
        ground_height = ground.get_height_at(self.x)
        if self.y + self.height // 2 > ground_height:
            self.y = ground_height - self.height // 2
            self.speed_y = 0
            self.in_air = False
            self.angular_velocity = 0  # Stop spinning when on the ground
            slope = ground.get_slope_at(self.x)
            self.angle = -math.degrees(math.atan(slope))
        else:
            self.in_air = True

        # Apply air resistance (only when in the air)
        if self.in_air:
            self.speed_x *= self.air_resistance  # Slow down slightly due to air resistance
            self.angular_velocity += self.speed_x * 0.02  # Increased spin based on horizontal speed
            self.angular_velocity *= self.spin_damping  # Reduced damping for longer spins
            self.angle += self.angular_velocity  # Apply spinning

        # Jump mechanic: Gain airtime if speed is above the threshold
        if not self.in_air and abs(self.speed_x) > self.jump_threshold:
            self.speed_y = -abs(self.speed_x) * 0.6  # Jump higher with more speed
            self.in_air = True

        # Use up fuel
        self.fuel -= self.fuel_consumption
        if self.fuel <= 0:
            self.fuel = 0
            self.speed_x = 0
            return GAME_OVER
        return GAME


class Ground:
    def __init__(self):
        self.y = HEIGHT - 100
        self.offset = 0
        self.waves = []  # List to store sine wave parameters (amplitude, wavelength)
        self.generate_waves()

    def generate_waves(self):
        # Generate random sine waves for varied terrain
        self.waves = []
        for _ in range(5):  # Generate 5 random sine waves
            amplitude = random.randint(50, 200)  # Random amplitude (larger range)
            wavelength = random.randint(800, 2000)  # Random wavelength (stretched out)
            self.waves.append((amplitude, wavelength))

    def draw(self):
        for x in range(0, WIDTH, 10):
            y = self.get_height_at(x)
            pygame.draw.rect(screen, BROWN, (x, y, 10, HEIGHT - y))
            pygame.draw.rect(screen, GREEN, (x, y - 10, 10, 10))

    def update(self, car_speed_x):
        self.offset += car_speed_x

    def get_height_at(self, x):
        # Combine multiple sine waves for varied terrain
        height = 0
        for amplitude, wavelength in self.waves:
            height += amplitude * math.sin((x + self.offset) / wavelength * 2 * math.pi)
        return self.y + height

    def get_slope_at(self, x):
        # Calculate the slope (derivative of the height function)
        slope = 0
        for amplitude, wavelength in self.waves:
            slope += (2 * math.pi / wavelength) * amplitude * math.cos((x + self.offset) / wavelength * 2 * math.pi)
        return slope


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
        pygame.draw.rect(screen, GREEN, (10, 10, self.car.fuel, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 100, 20), 2)

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

                self.ground.update(self.car.speed_x)
                self.current_state = self.car.update(self.ground)

                self.update_coins()
                self.update_fuel_cans()

                self.coin_spawn_timer += 1
                if self.coin_spawn_timer >= self.coin_spawn_delay:
                    y = self.ground.get_height_at(WIDTH) - Coin(0, 0).radius
                    self.coins.append(Coin(WIDTH, y))
                    self.coin_spawn_timer = 0

                self.fuel_spawn_timer += 1
                if self.fuel_spawn_timer >= self.fuel_spawn_delay:
                    y = self.ground.get_height_at(WIDTH) - FuelCan(0, 0).height
                    self.fuel_cans.append(FuelCan(WIDTH, y))
                    self.fuel_spawn_timer = 0

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