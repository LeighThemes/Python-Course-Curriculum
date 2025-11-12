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


# Parent Car Class
class Car:
    def __init__(self, width, height, color, max_speed, acceleration):
        self.width = width
        self.height = height
        self.color = color
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT // 2
        self.speed_x = 0
        self.speed_y = 0
        self.deceleration = 0.05
        self.brake = 0.5
        self.fuel = 100
        self.fuel_consumption = 0.1
        self.angle = 0
        self.wheel_radius = 10
        self.in_air = False
        self.angular_velocity = 0
        self.jump_threshold = 10
        self.gravity = 0.5
        self.air_resistance = 0.98
        self.spin_damping = 0.99
        self.ground_friction = 0.02
        self.airtime_timer = 0
        self.min_airtime_for_spin = 60

    def draw(self):
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, self.color, (0, 0, self.width, self.height))
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
            self.angular_velocity = 0
            self.airtime_timer = 0
            slope = ground.get_slope_at(self.x)
            self.angle = -math.degrees(math.atan(slope))

            # Apply gravity-based movement on slopes
            if not self.in_air:
                gravity_along_slope = self.gravity * math.sin(math.atan(slope))
                self.speed_x += gravity_along_slope
                self.speed_x *= (1 - self.ground_friction)

        else:
            self.in_air = True
            self.airtime_timer += 1

        # Apply air resistance (only when in the air)
        if self.in_air:
            self.speed_x *= self.air_resistance
            if self.airtime_timer > self.min_airtime_for_spin:
                self.angular_velocity += self.speed_x * 0.02
                self.angular_velocity *= self.spin_damping
                self.angle += self.angular_velocity

        # Jump mechanic: Gain upward momentum based on speed and slope
        if not self.in_air and abs(self.speed_x) > self.jump_threshold:
            slope = ground.get_slope_at(self.x)
            upward_momentum = abs(self.speed_x) * math.sin(math.atan(abs(slope))) * 1.2
            self.speed_y = -upward_momentum
            self.in_air = True

        # Use up fuel
        self.fuel -= self.fuel_consumption
        if self.fuel <= 0:
            self.fuel = 0
            self.speed_x = 0
            return GAME_OVER
        return GAME


# Child Vehicle Classes
class Sedan(Car):
    def __init__(self):
        super().__init__(width=90, height=55, color=RED, max_speed=18, acceleration=0.5)


class Truck(Car):
    def __init__(self):
        super().__init__(width=120, height=70, color=GREEN, max_speed=12, acceleration=0.3)


class SportsCar(Car):
    def __init__(self):
        super().__init__(width=80, height=40, color=GOLD, max_speed=25, acceleration=0.8)


# Ground Class
class Ground:
    def __init__(self):
        self.y = HEIGHT - 130
        self.offset = 0
        self.waves = []
        self.generate_waves()

    def generate_waves(self):
        self.waves = []
        for _ in range(7):
            amplitude = random.randint(20, 35)
            wavelength = random.randint(800, 2000)
            self.waves.append((amplitude, wavelength))

    def draw(self):
        for x in range(0, WIDTH, 10):
            y = self.get_height_at(x)
            pygame.draw.rect(screen, BROWN, (x, y, 10, HEIGHT - y))
            pygame.draw.rect(screen, GREEN, (x, y - 10, 10, 10))

    def update(self, car_speed_x):
        self.offset += car_speed_x

    def get_height_at(self, x):
        height = 0
        for amplitude, wavelength in self.waves:
            height += amplitude * math.sin((x + self.offset) / wavelength * 2 * math.pi)
        return self.y + height

    def get_slope_at(self, x):
        slope = 0
        for amplitude, wavelength in self.waves:
            slope += (2 * math.pi / wavelength) * amplitude * math.cos((x + self.offset) / wavelength * 2 * math.pi)
        return slope


# Coin Class
class Coin:
    def __init__(self, x, y, is_fuel=False):
        self.radius = 20
        self.x = x
        self.y = y
        self.is_fuel = is_fuel
        self.color = GOLD if not self.is_fuel else GREEN

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def update(self, car_speed_x):
        self.x -= car_speed_x


# Game Class
class Game:
    def __init__(self):
        self.ground = Ground()
        self.coins = []
        self.coin_spawn_delay = 200
        self.coin_spawn_timer = 0
        self.score = 0
        self.current_state = MAIN_MENU
        self.selected_vehicle = None

    def draw_hud(self):
        pygame.draw.rect(screen, GREEN, (10, 10, self.selected_vehicle.fuel, 20))
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

        # Draw vehicle selection buttons
        sedan_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                              HEIGHT // 2 - 100 <= mouse_pos[1] <= HEIGHT // 2 - 50)
        truck_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                              HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25)
        sports_car_button_hover = (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                                   HEIGHT // 2 + 50 <= mouse_pos[1] <= HEIGHT // 2 + 100)

        self.draw_button(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50, "Sedan", RED, (200, 0, 0), sedan_button_hover)
        self.draw_button(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50, "Truck", GREEN, (0, 200, 0), truck_button_hover)
        self.draw_button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Sports Car", GOLD, (255, 215, 0), sports_car_button_hover)

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
            coin.update(self.selected_vehicle.speed_x)
            if coin.x + coin.radius < 0:
                self.coins.remove(coin)
            if (self.selected_vehicle.x - self.selected_vehicle.width // 2 < coin.x < self.selected_vehicle.x + self.selected_vehicle.width // 2 and
                self.selected_vehicle.y - self.selected_vehicle.height // 2 < coin.y < self.selected_vehicle.y + self.selected_vehicle.height // 2):
                if coin.is_fuel:
                    self.selected_vehicle.fuel = min(100, self.selected_vehicle.fuel + 25)
                else:
                    self.score += 1
                self.coins.remove(coin)

    def spawn_coins_in_line(self):
        num_coins = random.randint(3, 6)
        spacing = 50
        start_x = WIDTH
        float_height = 20

        fuel_coin_index = 0 if random.choice([True, False]) else num_coins - 1

        for i in range(num_coins):
            x = start_x + i * spacing
            y = self.ground.get_height_at(x) - Coin(0, 0).radius - float_height
            is_fuel = (i == fuel_coin_index)
            self.coins.append(Coin(x, y, is_fuel))

    def reset_game(self):
        self.ground = Ground()
        self.coins.clear()
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
                            HEIGHT // 2 - 100 <= mouse_pos[1] <= HEIGHT // 2 - 50):
                            self.selected_vehicle = Sedan()
                            self.current_state = GAME
                            self.reset_game()
                        elif (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                              HEIGHT // 2 - 25 <= mouse_pos[1] <= HEIGHT // 2 + 25):
                            self.selected_vehicle = Truck()
                            self.current_state = GAME
                            self.reset_game()
                        elif (WIDTH // 2 - 100 <= mouse_pos[0] <= WIDTH // 2 + 100 and
                              HEIGHT // 2 + 50 <= mouse_pos[1] <= HEIGHT // 2 + 100):
                            self.selected_vehicle = SportsCar()
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
                    self.selected_vehicle.speed_x = min(self.selected_vehicle.max_speed, self.selected_vehicle.speed_x + self.selected_vehicle.acceleration)
                elif keys[pygame.K_LEFT]:
                    self.selected_vehicle.speed_x = max(0, self.selected_vehicle.speed_x - self.selected_vehicle.brake)
                else:
                    if self.selected_vehicle.speed_x > 0:
                        self.selected_vehicle.speed_x = max(0, self.selected_vehicle.speed_x - self.selected_vehicle.deceleration)
                    elif self.selected_vehicle.speed_x < 0:
                        self.selected_vehicle.speed_x = min(0, self.selected_vehicle.speed_x + self.selected_vehicle.deceleration)

                self.ground.update(self.selected_vehicle.speed_x)
                self.current_state = self.selected_vehicle.update(self.ground)

                self.update_coins()

                self.coin_spawn_timer += 1
                if self.coin_spawn_timer >= self.coin_spawn_delay:
                    self.spawn_coins_in_line()
                    self.coin_spawn_timer = 0

                self.ground.draw()
                self.selected_vehicle.draw()
                for coin in self.coins:
                    coin.draw()
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