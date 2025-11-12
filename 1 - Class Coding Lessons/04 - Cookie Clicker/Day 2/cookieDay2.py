import pygame
import sys
import math
from random import randint

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cookie Clicker")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 223, 0)
CHOCOLATE = (20, 42, 14)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (70, 70, 230)
PURPLE = (128, 80, 128)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (215, 229, 252)  # Light blue background color
GREY = (128, 128, 128)  # Grey color for disabled button
GLOW_COLOR = (255, 255, 0, 100)  # Semi-transparent yellow for glowing effect

# Fonts
font = pygame.font.Font(None, 36)

# Cookie settings
cookie_radius = 140
cookie_x = WIDTH // 3
cookie_y = HEIGHT // 2
cookie_color = BROWN

# Chocolate chip settings
chip_radius = 20
chips = [
    (cookie_x - 75, cookie_y - 60),  # Fixed positions for chips
    (cookie_x + 45, cookie_y - 40),
    (cookie_x - 20, cookie_y + 70),
    (cookie_x + 40, cookie_y + 30),
    (cookie_x - 70, cookie_y + 10),
    (cookie_x + 80, cookie_y + 3),
]

# Score
score = 0
power_up_level = 0  # Tracks the number of power-ups
click_multiplier = 1  # Tracks the multiplier for cookie clicks

# Animation variables
click_effect = False
click_effect_time = 0

# Auto-clicker variables
auto_clicker_last_time = 0
auto_clicker_interval = 1000  # 1 second

# Boost variables
boost_active = False
boost_start_time = 0
boost_duration = 10000  # 10 seconds in milliseconds
boost_multiplier = 2  # Double the cookie gain rate during boost

# Falling cookies
falling_cookies = []
falling_cookie_speed = 3

# Button settings
buttons = [
    {"x": WIDTH - 220, "y": 150, "width": 200, "height": 50, "color": GREEN, "cost": 100, "label": "Buy +1 (100)"},
    {"x": WIDTH - 220, "y": 210, "width": 200, "height": 50, "color": BLUE, "cost": 200, "label": "Buy +2 (200)"},
    {"x": WIDTH - 220, "y": 270, "width": 200, "height": 50, "color": PURPLE, "cost": 500, "label": "Buy +5 (500)"},
    {"x": WIDTH - 220, "y": 330, "width": 200, "height": 50, "color": ORANGE, "cost": 1000, "label": "Buy +10 (1K)"},
    {"x": WIDTH - 220, "y": 390, "width": 200, "height": 50, "color": RED, "cost": 10000, "label": "Buy +100 (10K)"},
]

# Boost button
boost_button = {"x": WIDTH - 440, "y": 50, "width": 200, "height": 50, "color": ORANGE, "cost": 10, "label": "Boost (300)"}

# Triple Click button
triple_click_button = {"x": WIDTH - 220, "y": 50, "width": 200, "height": 50, "color": PURPLE, "cost": 5000, "label": "4X Mult (5000)"}

def draw_cookie():
    # Draw the base cookie
    pygame.draw.circle(screen, cookie_color, (cookie_x, cookie_y), cookie_radius)
    # Draw chocolate chips
    for chip in chips:
        pygame.draw.circle(screen, CHOCOLATE, chip, chip_radius)
    # Draw click effect (yellow glow)
    if click_effect:
        pygame.draw.circle(screen, YELLOW, (cookie_x, cookie_y), cookie_radius + 10, 5)

def draw_score():
    score_text = font.render(f"Cookies: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))
    power_up_text = font.render(f"Auto-Click: {power_up_level}/s", True, BLACK)
    screen.blit(power_up_text, (10, 50))

def draw_buttons():
    for button in buttons:
        pygame.draw.rect(screen, button["color"], (button["x"], button["y"], button["width"], button["height"]))
        button_label = font.render(button["label"], True, BLACK)
        screen.blit(button_label, (button["x"] + 10, button["y"] + 10))
    # Draw Boost button
    if score >= boost_button["cost"]:
        pygame.draw.rect(screen, boost_button["color"], (boost_button["x"], boost_button["y"], boost_button["width"], boost_button["height"]))
        # Draw glowing effect
        glow_surface = pygame.Surface((boost_button["width"] + 20, boost_button["height"] + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, GLOW_COLOR, (boost_button["width"] // 2 + 10, boost_button["height"] // 2 + 10), boost_button["width"] // 2 + 10)
        screen.blit(glow_surface, (boost_button["x"] - 10, boost_button["y"] - 10))
    else:
        pygame.draw.rect(screen, GREY, (boost_button["x"], boost_button["y"], boost_button["width"], boost_button["height"]))
    boost_label = font.render(boost_button["label"], True, BLACK)
    screen.blit(boost_label, (boost_button["x"] + 10, boost_button["y"] + 10))
    # Draw Triple Click button
    if score >= triple_click_button["cost"]:
        pygame.draw.rect(screen, triple_click_button["color"], (triple_click_button["x"], triple_click_button["y"], triple_click_button["width"], triple_click_button["height"]))
        # Draw glowing effect
        glow_surface = pygame.Surface((triple_click_button["width"] + 20, triple_click_button["height"] + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, GLOW_COLOR, (triple_click_button["width"] // 2 + 10, triple_click_button["height"] // 2 + 10), triple_click_button["width"] // 2 + 10)
        screen.blit(glow_surface, (triple_click_button["x"] - 10, triple_click_button["y"] - 10))
    else:
        pygame.draw.rect(screen, GREY, (triple_click_button["x"], triple_click_button["y"], triple_click_button["width"], triple_click_button["height"]))
    triple_click_label = font.render(triple_click_button["label"], True, BLACK)
    screen.blit(triple_click_label, (triple_click_button["x"] + 10, triple_click_button["y"] + 10))

def draw_click_effect():
    global click_effect, click_effect_time
    if click_effect:
        current_time = pygame.time.get_ticks()
        if current_time - click_effect_time > 100:  # Effect lasts for 100ms
            click_effect = False

def handle_auto_clicker():
    global score, auto_clicker_last_time
    current_time = pygame.time.get_ticks()
    if current_time - auto_clicker_last_time >= auto_clicker_interval:
        if boost_active:
            score += power_up_level * boost_multiplier  # Apply boost multiplier
        else:
            score += power_up_level  # Normal auto-clicker
        auto_clicker_last_time = current_time

def handle_button_click(mouse_x, mouse_y):
    global score, power_up_level, boost_active, boost_start_time, click_multiplier
    for button in buttons:
        if (button["x"] <= mouse_x <= button["x"] + button["width"] and
            button["y"] <= mouse_y <= button["y"] + button["height"]):
            if score >= button["cost"]:
                score -= button["cost"]
                # Increase auto-clicker power based on the button
                if button["cost"] == 100:
                    power_up_level += 1
                elif button["cost"] == 200:
                    power_up_level += 2
                elif button["cost"] == 500:
                    power_up_level += 5
                elif button["cost"] == 1000:
                    power_up_level += 10
                elif button["cost"] == 10000:
                    power_up_level += 100
    # Check if Boost button is clicked and player has enough cookies
    if (boost_button["x"] <= mouse_x <= boost_button["x"] + boost_button["width"] and
        boost_button["y"] <= mouse_y <= boost_button["y"] + boost_button["height"]):
        if score >= boost_button["cost"]:
            score -= boost_button["cost"]
            boost_active = True
            boost_start_time = pygame.time.get_ticks()
    # Check if Triple Click button is clicked and player has enough cookies
    if (triple_click_button["x"] <= mouse_x <= triple_click_button["x"] + triple_click_button["width"] and
        triple_click_button["y"] <= mouse_y <= triple_click_button["y"] + triple_click_button["height"]):
        if score >= triple_click_button["cost"]:
            score -= triple_click_button["cost"]
            click_multiplier *= 4  # Permanently multiply cookie clicks by 4

def create_falling_cookie():
    x = randint(50, WIDTH - 250)  # Random x position (avoid buttons on the right)
    y = -50  # Start above the screen
    return {"x": x, "y": y, "radius": 20}

def draw_falling_cookies():
    for cookie in falling_cookies:
        pygame.draw.circle(screen, BROWN, (cookie["x"], cookie["y"]), cookie["radius"])
        # Draw chocolate chips
        for i in range(5):  # Add 5 chocolate chips
            angle = randint(0, 360)
            distance = randint(0, cookie["radius"] - 5)
            chip_x = cookie["x"] + int(distance * math.cos(math.radians(angle)))
            chip_y = cookie["y"] + int(distance * math.sin(math.radians(angle)))
            pygame.draw.circle(screen, CHOCOLATE, (chip_x, chip_y), 5)

def update_falling_cookies():
    global falling_cookies, score
    for cookie in falling_cookies:
        cookie["y"] += falling_cookie_speed  # Move cookie down
    # Remove cookies that fall off the screen
    falling_cookies = [cookie for cookie in falling_cookies if cookie["y"] < HEIGHT + 50]
    # Add a new falling cookie every 100 cookies
    if score > 0 and score % 100 == 0:
        falling_cookies.append(create_falling_cookie())

def update_boost():
    global boost_active, boost_start_time
    if boost_active:
        current_time = pygame.time.get_ticks()
        if current_time - boost_start_time >= boost_duration:
            boost_active = False  # End boost after 10 seconds

def draw_boost_timer():
    if boost_active:
        remaining_time = max(0, (boost_duration - (pygame.time.get_ticks() - boost_start_time)) // 1000)
        boost_timer_text = font.render(f"Boost: {remaining_time}s", True, BLACK)
        screen.blit(boost_timer_text, (WIDTH - 440, 100))

# Main game loop
running = True
while running:
    screen.fill(LIGHT_BLUE)  # Set background color to light blue

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Check if the cookie is clicked
            distance_sq = (mouse_x - cookie_x)**2 + (mouse_y - cookie_y)**2
            if distance_sq <= cookie_radius**2:
                if boost_active:
                    score += click_multiplier * boost_multiplier  # Apply boost multiplier and click multiplier
                else:
                    score += click_multiplier  # Apply click multiplier
                click_effect = True
                click_effect_time = pygame.time.get_ticks()
            # Check if any button is clicked
            handle_button_click(mouse_x, mouse_y)

    # Handle auto-clicker
    handle_auto_clicker()

    # Update falling cookies
    update_falling_cookies()

    # Update boost
    update_boost()

    # Draw everything
    draw_falling_cookies()  # Draw falling cookies first (background)
    draw_cookie()
    draw_score()
    draw_buttons()
    draw_click_effect()
    draw_boost_timer()  # Draw boost timer

    # Update display
    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()