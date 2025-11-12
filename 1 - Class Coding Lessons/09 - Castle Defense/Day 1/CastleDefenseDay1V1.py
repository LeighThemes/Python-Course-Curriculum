import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Top-Down Castle Defense")

# Colors
GRASS_GREEN = (34, 139, 34)
PATH_BROWN = (139, 69, 19)
STONE_GRAY = (169, 169, 169)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
UI_BOX_COLOR = (50, 50, 50, 200)  # Darker and more opaque

# Game states
MAIN_MENU = 0
GAME = 1
GAME_OVER = 2
current_state = MAIN_MENU


# Castle settings
castle_width, castle_height = 80, 80
castle_x = WIDTH - castle_width - 7
castle_y = HEIGHT // 2 - castle_height // 2
castle_health = 100
max_castle_health = 100

# Path settings
path_width = 60
path_points = [
    (0, HEIGHT // 4),
    (WIDTH // 4, HEIGHT // 4),
    (WIDTH // 4, HEIGHT // 2),
    (WIDTH // 2, HEIGHT // 2),
    (WIDTH // 2, HEIGHT * 3 // 4),
    (WIDTH * 3 // 4, HEIGHT * 3 // 4),
    (WIDTH * 3 // 4, HEIGHT // 2),
    (WIDTH, HEIGHT // 2)
]

# Tower settings
cannon_radius = 15
wizard_radius = 15
cannon_cost = 50
wizard_cost = 75
cannon_cooldown_max = 45
wizard_cooldown_max = 90
cannon_range = 180
wizard_range = 200
cannon_damage = 10
wizard_damage = 25

placed_towers = []
selected_tower = None
dragging_tower = False

# Enemy settings
enemies = []
enemy_spawn_timer = 0
enemy_spawn_delay = 120
enemy_speed = 1.5
enemy_types = [
    {"color": RED, "health": 30, "speed": 1.5, "reward": 10, "size": 11},
    {"color": BLUE, "health": 50, "speed": 1.0, "reward": 20, "size": 13},
    {"color": YELLOW, "health": 80, "speed": 0.8, "reward": 30, "size": 15}
]

# Wave tracking
enemies_in_wave = 0
enemies_remaining = 0
enemies_to_spawn = 0

# Projectile settings
projectiles = []
projectile_speed = 5
projectile_radius = 4

# Resources
gold = 200
gold_increase_timer = 0
gold_increase_delay = 180

# Waves
current_wave = 1
wave_timer = 0
wave_duration = 1800
time_between_waves = 450
is_between_waves = False  # Start in wave mode
wave_announcement_timer = 120  # Start with wave 1 announcement
wave_announcement_duration = 120  # 2 seconds at 60 FPS

# Fonts
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 72)

def draw_wave_announcement():
    if wave_announcement_timer > 0:
        wave_text = big_font.render(f"WAVE {current_wave}", True, GOLD)
        text_rect = wave_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        
        # Add background rectangle
        pygame.draw.rect(screen, (0, 0, 0, 200), 
                        (text_rect.x - 30, text_rect.y - 15, 
                         text_rect.width + 60, text_rect.height + 30),
                        border_radius=15)
        screen.blit(wave_text, text_rect)

def find_nearest_enemy(x, y):
    nearest_enemy = None
    min_distance = float('inf')
    
    for enemy in enemies:
        distance = math.dist((x, y), (enemy["x"], enemy["y"]))
        if distance < min_distance:
            min_distance = distance
            nearest_enemy = enemy
    
    return nearest_enemy

def draw_castle():
    # Main castle body
    pygame.draw.rect(screen, STONE_GRAY, (castle_x, castle_y, castle_width, castle_height))
    
    # Draw battlements (three little blocks on top)
    battlement_width = castle_width // 4  # Width of each battlement
    battlement_height = 15  # Height of the battlements
    gap_width = (castle_width - 3 * battlement_width) // 2  # Space between battlements
    
    # Calculate positions for three battlements
    for i in range(3):
        battlement_x = castle_x + i * (battlement_width + gap_width)
        pygame.draw.rect(screen, STONE_GRAY, 
                        (battlement_x, castle_y - battlement_height, 
                         battlement_width, battlement_height))
    
    # Health bar
    health_width = castle_width
    health_height = 8
    health_ratio = castle_health / max_castle_health
    pygame.draw.rect(screen, RED, (castle_x, castle_y - 12 - battlement_height, health_width, health_height))
    pygame.draw.rect(screen, (0, 255, 0), (castle_x, castle_y - 12 - battlement_height, 
                         health_width * health_ratio, health_height))
                         
def draw_path():
    for i in range(len(path_points) - 1):
        start = path_points[i]
        end = path_points[i + 1]
        
        if start[1] == end[1]:  # Horizontal
            y = start[1] - path_width // 2
            pygame.draw.rect(screen, PATH_BROWN, 
                           (min(start[0], end[0]), y, 
                           abs(end[0] - start[0]) + 1, path_width))
        else:  # Vertical
            x = start[0] - path_width // 2
            pygame.draw.rect(screen, PATH_BROWN, 
                           (x, min(start[1], end[1]), 
                           path_width, abs(end[1] - start[1])))

def draw_towers():
    for tower in placed_towers:
        color = (100, 100, 100) if tower["cooldown"] > 0 else (BLACK if tower["type"] == "cannon" else PURPLE)
        radius = cannon_radius if tower["type"] == "cannon" else wizard_radius
        pygame.draw.circle(screen, color, (int(tower["x"]), int(tower["y"])), radius)
        
        if tower["cooldown"] <= (cannon_cooldown_max if tower["type"] == "cannon" else wizard_cooldown_max) * 0.8:
            nearest_enemy = find_nearest_enemy(tower["x"], tower["y"])
            if nearest_enemy:
                angle = math.atan2(nearest_enemy["y"] - tower["y"], nearest_enemy["x"] - tower["x"])
                length = radius + 10
                end_x = tower["x"] + length * math.cos(angle)
                end_y = tower["y"] + length * math.sin(angle)
                line_color = BLACK if tower["type"] == "cannon" else YELLOW
                pygame.draw.line(screen, line_color, (tower["x"], tower["y"]), (end_x, end_y), 4)
        
        if selected_tower == tower:
            range = cannon_range if tower["type"] == "cannon" else wizard_range
            pygame.draw.circle(screen, (200, 200, 200, 100), (int(tower["x"]), int(tower["y"])), range, 1)

def draw_enemies():
    for enemy in enemies:
        pygame.draw.circle(screen, enemy["color"], (int(enemy["x"]), int(enemy["y"])), enemy["size"])
        health_width = enemy["size"] * 2
        health_height = 4
        health_ratio = enemy["health"] / enemy["max_health"]
        pygame.draw.rect(screen, RED, (int(enemy["x"] - enemy["size"]), int(enemy["y"] - enemy["size"] - 8), 
                         health_width, health_height))
        pygame.draw.rect(screen, (0, 255, 0), (int(enemy["x"] - enemy["size"]), int(enemy["y"] - enemy["size"] - 8), 
                         health_width * health_ratio, health_height))

def draw_projectiles():
    for projectile in projectiles:
        if projectile["type"] == "cannon":
            pygame.draw.circle(screen, BLACK, (int(projectile["x"]), int(projectile["y"])), projectile_radius)
        else:  # wizard lightning
            pygame.draw.line(screen, YELLOW, 
                            (projectile["start_x"], projectile["start_y"]), 
                            (int(projectile["x"]), int(projectile["y"])), 2)
            # Add lightning branches
            for i in range(2):
                mid_x = (projectile["start_x"] + projectile["x"]) // 2
                mid_y = (projectile["start_y"] + projectile["y"]) // 2
                branch_x = mid_x + random.randint(-8, 8)
                branch_y = mid_y + random.randint(-8, 8)
                pygame.draw.line(screen, YELLOW, (mid_x, mid_y), (branch_x, branch_y), 1)

def spawn_enemy():
    global enemies_in_wave, enemies_remaining
    enemy_type = random.choice(enemy_types)
    enemy = {
        "x": path_points[0][0],
        "y": path_points[0][1],
        "size": enemy_type["size"],
        "speed": enemy_type["speed"],
        "health": enemy_type["health"],
        "max_health": enemy_type["health"],
        "color": enemy_type["color"],
        "reward": enemy_type["reward"],
        "path_index": 0,
        "progress": 0
    }
    enemies.append(enemy)
    enemies_in_wave += 1
    enemies_remaining += 1

def update_enemies():
    global castle_health, gold, enemies_remaining
    for enemy in enemies[:]:
        path_index = enemy["path_index"]
        if path_index >= len(path_points) - 1:
            castle_health -= 10
            enemies.remove(enemy)
            enemies_remaining -= 1
            if castle_health <= 0:
                global current_state
                current_state = GAME_OVER
            continue
        
        start = path_points[path_index]
        end = path_points[path_index + 1]
        enemy["progress"] += enemy["speed"] / math.dist(start, end)
        
        if enemy["progress"] >= 1:
            enemy["path_index"] += 1
            enemy["progress"] = 0
        else:
            enemy["x"] = start[0] + (end[0] - start[0]) * enemy["progress"]
            enemy["y"] = start[1] + (end[1] - start[1]) * enemy["progress"]

def update_towers():
    for tower in placed_towers:
        if tower["cooldown"] > 0:
            tower["cooldown"] -= 1
        else:
            nearest_enemy = find_nearest_enemy(tower["x"], tower["y"])
            range = cannon_range if tower["type"] == "cannon" else wizard_range
            if nearest_enemy and math.dist((tower["x"], tower["y"]), (nearest_enemy["x"], nearest_enemy["y"])) <= range:
                angle = math.atan2(nearest_enemy["y"] - tower["y"], nearest_enemy["x"] - tower["x"])
                projectile = {
                    "x": tower["x"],
                    "y": tower["y"],
                    "dx": projectile_speed * math.cos(angle),
                    "dy": projectile_speed * math.sin(angle),
                    "damage": cannon_damage if tower["type"] == "cannon" else wizard_damage,
                    "type": tower["type"],
                    "start_x": tower["x"],
                    "start_y": tower["y"]
                }
                projectiles.append(projectile)
                tower["cooldown"] = cannon_cooldown_max if tower["type"] == "cannon" else wizard_cooldown_max

def update_projectiles():
    global gold, enemies_remaining
    for projectile in projectiles[:]:
        projectile["x"] += projectile["dx"]
        projectile["y"] += projectile["dy"]
        
        for enemy in enemies[:]:
            distance = math.dist((projectile["x"], projectile["y"]), (enemy["x"], enemy["y"]))
            if distance < enemy["size"] + projectile_radius:
                enemy["health"] -= projectile["damage"]
                if enemy["health"] <= 0:
                    gold += enemy["reward"]
                    enemies.remove(enemy)
                    enemies_remaining -= 1
                projectiles.remove(projectile)
                break
        
        if (projectile["x"] < 0 or projectile["x"] > WIDTH or 
            projectile["y"] < 0 or projectile["y"] > HEIGHT):
            projectiles.remove(projectile)

def draw_ui():
    # UI box background
    ui_box_rect = pygame.Rect(WIDTH - 160, HEIGHT - 190, 150, 180)
    pygame.draw.rect(screen, UI_BOX_COLOR, ui_box_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, ui_box_rect, 2, border_radius=10)
    
    # Gold and wave info
    gold_text = small_font.render(f"Gold: {gold}", True, GOLD)
    screen.blit(gold_text, (WIDTH - 150, HEIGHT - 180))
    
    wave_text = small_font.render(f"Wave: {current_wave}", True, WHITE)
    screen.blit(wave_text, (WIDTH - 150, HEIGHT - 150))
    
    # Enemies remaining
    enemies_text = small_font.render(f"Enemies: {enemies_remaining}", True, WHITE)
    screen.blit(enemies_text, (WIDTH - 150, HEIGHT - 120))
    
    # Tower buttons
    button_width, button_height = 130, 35
    cannon_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 90, button_width, button_height)
    wizard_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, button_width, button_height)
    
    # Cannon button
    cannon_color = GOLD if gold >= cannon_cost else (100, 100, 100)
    pygame.draw.rect(screen, cannon_color, cannon_button_rect, border_radius=6)
    pygame.draw.rect(screen, WHITE, cannon_button_rect, 2, border_radius=6)
    cannon_text = small_font.render(f"Cannon: {cannon_cost}g", True, BLACK)
    screen.blit(cannon_text, (cannon_button_rect.x + 5, cannon_button_rect.y + 8))
    
    # Wizard button
    wizard_color = PURPLE if gold >= wizard_cost else (100, 50, 100)
    pygame.draw.rect(screen, wizard_color, wizard_button_rect, border_radius=6)
    pygame.draw.rect(screen, WHITE, wizard_button_rect, 2, border_radius=6)
    wizard_text = small_font.render(f"Wizard: {wizard_cost}g", True, WHITE)
    screen.blit(wizard_text, (wizard_button_rect.x + 5, wizard_button_rect.y + 8))

def draw_main_menu():
    # Gradient background
    for y in range(HEIGHT):
        shade = int(34 + (y / HEIGHT) * 100)
        pygame.draw.line(screen, (34, min(139, shade), 34), (0, y), (WIDTH, y))
    
    # Improved castle design with towers
    castle_menu_x = WIDTH // 2 - 120
    castle_width = 240
    
    # Main castle body
    pygame.draw.rect(screen, (80, 80, 80), (castle_menu_x, HEIGHT//2 - 100, castle_width, 120))
    
    # Central tower
    pygame.draw.rect(screen, (70, 70, 70), (castle_menu_x + castle_width//2 - 20, HEIGHT//2 - 150, 40, 50))
    
    # Side towers
    pygame.draw.rect(screen, (70, 70, 70), (castle_menu_x - 10, HEIGHT//2 - 130, 30, 50))
    pygame.draw.rect(screen, (70, 70, 70), (castle_menu_x + castle_width - 20, HEIGHT//2 - 130, 30, 50))
    
    # Battlements
    battlement_width = 30
    for i in range(castle_width // battlement_width):
        pygame.draw.rect(screen, (70, 70, 70), 
                        (castle_menu_x + i * battlement_width, HEIGHT//2 - 100 - 15, 
                         battlement_width - 5, 15))
    
    # Castle windows
    for i in range(3):
        pygame.draw.rect(screen, GOLD, (castle_menu_x + 40 + i * 60, HEIGHT//2 - 60, 15, 20))
    
    # Wizard character
    # Wizard hat
    pygame.draw.polygon(screen, PURPLE, [
        (WIDTH//4, HEIGHT//2 - 30),
        (WIDTH//4 - 25, HEIGHT//2),
        (WIDTH//4 + 25, HEIGHT//2)
    ])
    # Wizard head
    pygame.draw.circle(screen, (210, 180, 140), (WIDTH//4, HEIGHT//2 + 10), 15)
    # Wizard robe
    pygame.draw.rect(screen, (100, 0, 100), (WIDTH//4 - 20, HEIGHT//2 + 25, 40, 40))
    # Wizard staff (adjusted position)
    staff_top_x = WIDTH//4 - 30
    staff_top_y = HEIGHT//2 - 20  # Higher up
    staff_length = 80
    pygame.draw.rect(screen, (139, 69, 19), 
                    (staff_top_x, staff_top_y, 5, staff_length))
    # Staff orb (now at top of staff)
    pygame.draw.circle(screen, (200, 200, 255), 
                      (staff_top_x + 2, staff_top_y), 8)  # +2 to center on staff
    # Magic glow around orb
    pygame.draw.circle(screen, (200, 200, 255, 100),  # Semi-transparent
                      (staff_top_x + 2, staff_top_y), 12, 1)
    
    # Title with magical effect
    title_text = big_font.render("CASTLE DEFENSE", True, (200, 200, 255))
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
    
    # Magic sparkles around wizard
    for _ in range(5):
        sparkle_x = random.randint(WIDTH//4 - 50, WIDTH//4 + 50)
        sparkle_y = random.randint(HEIGHT//2 - 20, HEIGHT//2 + 60)
        pygame.draw.circle(screen, (255, 255, 200), (sparkle_x, sparkle_y), 2)
    
    # Start button
    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT*2//3, 300, 50)
    pygame.draw.rect(screen, PURPLE, button_rect, border_radius=10)
    pygame.draw.rect(screen, (200, 200, 255), button_rect, 3, border_radius=10)
    
    start_text = font.render("BEGIN MAGIC DEFENSE", True, WHITE)
    screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT*2//3 + 15))
    

def draw_game_over():
    screen.fill(GRASS_GREEN)
    title_text = big_font.render("Game Over", True, RED)
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
    
    score_text = font.render(f"Wave: {current_wave}", True, BLACK)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    
    restart_text = font.render("Click to restart", True, BLACK)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT*2//3))

def is_valid_tower_position(x, y):
    # Check path collision
    for i in range(len(path_points) - 1):
        start = path_points[i]
        end = path_points[i + 1]
        
        if start[0] == end[0]:  # Vertical
            seg_left = start[0] - path_width//2 - cannon_radius
            seg_right = start[0] + path_width//2 + cannon_radius
            seg_top = min(start[1], end[1]) - cannon_radius
            seg_bottom = max(start[1], end[1]) + cannon_radius
            if seg_left <= x <= seg_right and seg_top <= y <= seg_bottom:
                return False
        else:  # Horizontal
            seg_left = min(start[0], end[0]) - cannon_radius
            seg_right = max(start[0], end[0]) + cannon_radius
            seg_top = start[1] - path_width//2 - cannon_radius
            seg_bottom = start[1] + path_width//2 + cannon_radius
            if seg_left <= x <= seg_right and seg_top <= y <= seg_bottom:
                return False
    
    # Check castle collision
    if (castle_x - cannon_radius <= x <= castle_x + castle_width + cannon_radius and
        castle_y - cannon_radius <= y <= castle_y + castle_height + cannon_radius):
        return False
    
    # Check other towers
    for tower in placed_towers:
        if tower == selected_tower:
            continue
        if math.dist((x, y), (tower["x"], tower["y"])) < cannon_radius * 2:
            return False
    
    # Check screen bounds
    if (x < cannon_radius or x > WIDTH - cannon_radius or
        y < cannon_radius or y > HEIGHT - cannon_radius):
        return False
    
    return True

def reset_game():
    global castle_health, gold, current_wave, wave_timer, is_between_waves
    global enemies, projectiles, placed_towers, selected_tower, dragging_tower
    global wave_announcement_timer, enemies_in_wave, enemies_remaining
    
    castle_health = max_castle_health
    gold = 200
    current_wave = 1
    wave_timer = 0
    is_between_waves = False  # Start immediately in wave mode
    wave_announcement_timer = wave_announcement_duration
    enemies = []
    projectiles = []
    placed_towers = []
    selected_tower = None
    dragging_tower = False
    enemies_in_wave = 0
    enemies_remaining = 0

# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if current_state == MAIN_MENU:
                current_state = GAME
                reset_game()
            elif current_state == GAME_OVER:
                current_state = GAME
                reset_game()
            elif current_state == GAME:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Check tower buttons
                button_width, button_height = 130, 35
                cannon_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 90, button_width, button_height)
                wizard_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, button_width, button_height)
                
                if cannon_button_rect.collidepoint(mouse_x, mouse_y) and gold >= cannon_cost:
                    gold -= cannon_cost
                    new_tower = {
                        "x": mouse_x,
                        "y": mouse_y,
                        "cooldown": 0,
                        "type": "cannon"
                    }
                    placed_towers.append(new_tower)
                    selected_tower = new_tower
                    dragging_tower = True
                
                elif wizard_button_rect.collidepoint(mouse_x, mouse_y) and gold >= wizard_cost:
                    gold -= wizard_cost
                    new_tower = {
                        "x": mouse_x,
                        "y": mouse_y,
                        "cooldown": 0,
                        "type": "wizard"
                    }
                    placed_towers.append(new_tower)
                    selected_tower = new_tower
                    dragging_tower = True
                
                # Check existing towers
                elif not dragging_tower:
                    for tower in placed_towers:
                        radius = cannon_radius if tower["type"] == "cannon" else wizard_radius
                        if math.dist((mouse_x, mouse_y), (tower["x"], tower["y"])) <= radius:
                            selected_tower = tower
                            dragging_tower = True
                            break
        
        elif event.type == pygame.MOUSEBUTTONUP and current_state == GAME:
            if dragging_tower:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if is_valid_tower_position(mouse_x, mouse_y):
                    selected_tower["x"] = mouse_x
                    selected_tower["y"] = mouse_y
                else:
                    if "original_x" not in selected_tower:  # New tower
                        placed_towers.remove(selected_tower)
                        refund = cannon_cost if selected_tower["type"] == "cannon" else wizard_cost
                        gold += refund
                
                dragging_tower = False
                selected_tower = None
    
    # Game logic
    if current_state == GAME:
        # Handle tower dragging
        if dragging_tower and selected_tower:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            selected_tower["x"] = mouse_x
            selected_tower["y"] = mouse_y
        
        # Update wave announcement timer
        if wave_announcement_timer > 0:
            wave_announcement_timer -= 1
        
        # Wave management
        if is_between_waves:
            # Only start next wave when all enemies are gone
            if len(enemies) == 0:
                wave_timer += 1
                if wave_timer >= time_between_waves:
                    current_wave += 1
                    is_between_waves = False
                    wave_timer = 0
                    wave_announcement_timer = wave_announcement_duration
                    enemy_speed += 0.1
                    enemy_spawn_delay = max(30, enemy_spawn_delay - 5)
                    enemies_in_wave = 0  # Reset for new wave
        else:
            # Spawn enemies during wave (spawn more as waves progress)
            enemy_spawn_timer += 1
            if enemy_spawn_timer >= enemy_spawn_delay:
                spawn_enemy()
                enemy_spawn_timer = 0
                # Increase spawn rate as wave progresses
                if wave_timer > wave_duration // 2:
                    enemy_spawn_delay = max(30, enemy_spawn_delay - 2)
            
            # Check if wave should end (either time expired or all enemies defeated)
            wave_timer += 1
            if wave_timer >= wave_duration or (enemies_in_wave > 0 and enemies_remaining == 0):
                is_between_waves = True
                wave_timer = 0
        
        # Increase gold
        gold_increase_timer += 1
        if gold_increase_timer >= gold_increase_delay:
            gold += 2
            gold_increase_timer = 0
        
        # Update game objects
        update_enemies()
        update_towers()
        update_projectiles()
    
    # Drawing
    screen.fill(GRASS_GREEN)
    
    if current_state == MAIN_MENU:
        draw_main_menu()
    elif current_state == GAME_OVER:
        draw_game_over()
    elif current_state == GAME:
        draw_path()
        draw_castle()
        draw_enemies()
        draw_projectiles()
        draw_towers()
        draw_ui()
        
        # Draw placement preview
        if dragging_tower and selected_tower and "original_x" not in selected_tower:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = (0, 255, 0) if is_valid_tower_position(mouse_x, mouse_y) else (255, 0, 0)
            radius = cannon_radius if selected_tower["type"] == "cannon" else wizard_radius
            pygame.draw.circle(screen, color, (mouse_x, mouse_y), radius, 2)
        
        # Draw wave announcement
        draw_wave_announcement()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()