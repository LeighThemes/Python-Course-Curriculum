import pygame
import math
import sys

# Initialize pygame
pygame.init()

# Screen dimensions - made larger to accommodate zoomed-out view
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Solar System Explorer")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
BROWN = (165, 42, 42)
LIGHT_BLUE = (173, 216, 230)
GRAY = (128, 128, 128)

# Font
font = pygame.font.SysFont('Arial', 18)
title_font = pygame.font.SysFont('Arial', 28)

# Scale factor to zoom out the entire solar system
SCALE_FACTOR = 0.5  # Reduces all distances by 30%

# Base class for all celestial bodies
class CelestialBody:
    def __init__(self, name, radius, color, distance_from_sun, orbital_speed):
        self.name = name
        self.radius = radius
        self.color = color
        self.distance_from_sun = distance_from_sun * SCALE_FACTOR  # Apply zoom-out
        self.orbital_speed = orbital_speed * 0.3  # Reduced speed by 70%
        self.angle = 0
        self.zoomed = False
        self.highlight = False
    
    def update(self):
        self.angle += self.orbital_speed
    
    def draw(self, screen, zoomed_body=None):
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Draw orbit path (only in solar system view) with thicker lines
        if zoomed_body is None:
            pygame.draw.circle(screen, (80, 80, 80), (center_x, center_y), 
                             self.distance_from_sun, 2)  # Increased from 1 to 2 pixels
        
        if zoomed_body is None or self.zoomed:
            # Calculate position in orbit
            x = center_x + math.cos(self.angle) * self.distance_from_sun
            y = center_y + math.sin(self.angle) * self.distance_from_sun
            
            # Draw highlight glow if mouse is near
            if self.highlight and zoomed_body is None:
                glow_radius = self.radius + 15
                glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*self.color, 100), 
                                 (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surface, (int(x) - glow_radius, int(y) - glow_radius))
            
            # Draw the body
            pygame.draw.circle(screen, self.color, (int(x), int(y)), self.radius)
            
            # Draw the name if not zoomed
            if not self.zoomed:
                name_text = font.render(self.name, True, WHITE)
                screen.blit(name_text, (int(x) - name_text.get_width() // 2, int(y) - self.radius - 25))
    
    def is_clicked(self, pos):
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        x = center_x + math.cos(self.angle) * self.distance_from_sun
        y = center_y + math.sin(self.angle) * self.distance_from_sun
        
        distance = math.sqrt((pos[0] - x) ** 2 + (pos[1] - y) ** 2)
        self.highlight = distance <= (self.radius * 1.5)
        return self.highlight
    
    def draw_zoomed(self, screen):
        # Draw planet info
        title = title_font.render(f"Planet: {self.name}", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw back button
        back_text = font.render("Click to go back to solar system", True, WHITE)
        screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 50))

# Planet class inheriting from CelestialBody
class Planet(CelestialBody):
    def __init__(self, name, radius, color, distance_from_sun, orbital_speed, 
                 mass, atmosphere, fun_fact):
        super().__init__(name, radius, color, distance_from_sun, orbital_speed)
        self.mass = mass
        self.atmosphere = atmosphere
        self.fun_fact = fun_fact
    
    def draw_zoomed(self, screen):
        super().draw_zoomed(screen)
        
        # Draw planet details
        mass_text = font.render(f"Mass: {self.mass}", True, WHITE)
        atmos_text = font.render(f"Atmosphere: {self.atmosphere}", True, WHITE)
        fact_text = font.render(f"Fun Fact: {self.fun_fact}", True, WHITE)
        
        screen.blit(mass_text, (WIDTH // 2 - mass_text.get_width() // 2, 190))
        screen.blit(atmos_text, (WIDTH // 2 - atmos_text.get_width() // 2, 220))
        screen.blit(fact_text, (WIDTH // 2 - fact_text.get_width() // 2, 250))
        
        # Draw the planet representation with enhanced glow effect
        glow_surface = pygame.Surface((220, 220), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 80), (110, 110), 110)
        screen.blit(glow_surface, (WIDTH // 2 - 110, HEIGHT // 2 - 110))
        pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), 100)

# Create solar system bodies with original distances (will be scaled down)
sun = CelestialBody("Sun", 20, YELLOW, 0, 0)

planets = [
    Planet("Mercury", 10, GRAY, 100, 0.02, 
           "3.3 × 10²³ kg", "Thin exosphere", 
           "Smallest planet in our solar system"),
    Planet("Venus", 15, ORANGE, 150, 0.015, 
           "4.9 × 10²⁴ kg", "96% CO₂, 3% N₂", 
           "Hottest planet due to thick atmosphere"),
    Planet("Earth", 16, BLUE, 220, 0.01, 
           "6 × 10²⁴ kg", "78% N₂, 21% O₂", 
           "Only known planet with life"),
    Planet("Mars", 13, RED, 290, 0.008, 
           "6.4 × 10²³ kg", "95% CO₂, 3% N₂", 
           "Home to the tallest volcano in the solar system"),
    Planet("Jupiter", 25, BROWN, 380, 0.004, 
           "1.9 × 10²⁷ kg", "90% H₂, 10% He", 
           "Largest planet in our solar system"),
    Planet("Saturn", 23, LIGHT_BLUE, 470, 0.003, 
           "5.7 × 10²⁶ kg", "96% H₂, 3% He", 
           "Has beautiful rings made of ice and rock"),
    Planet("Uranus", 19, GREEN, 550, 0.002, 
           "8.7 × 10²⁵ kg", "83% H₂, 15% He, 2% CH₄", 
           "Rotates on its side"),
    Planet("Neptune", 19, BLUE, 630, 0.001, 
           "1 × 10²⁶ kg", "80% H₂, 19% He, 1% CH₄", 
           "Has the strongest winds in the solar system")
]

# Game state
zoomed_planet = None
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if zoomed_planet is None:
                # Check if a planet was clicked
                for planet in planets:
                    if planet.is_clicked(mouse_pos):
                        zoomed_planet = planet
                        planet.zoomed = True
                        break
            else:
                # Return to solar system view
                zoomed_planet.zoomed = False
                zoomed_planet = None
    
    # Update highlight status for all planets
    if zoomed_planet is None:
        for planet in planets:
            planet.is_clicked(mouse_pos)
    
    # Update planets
    for planet in planets:
        planet.update()
    
    # Draw everything
    screen.fill(BLACK)
    
    if zoomed_planet is None:
        # Draw solar system view
        sun.draw(screen)
        for planet in planets:
            planet.draw(screen)
        
        # Draw instructions
        instructions = font.render("Click on a planet to learn about it!", True, WHITE)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, 30))
        
        # Draw additional help text
        help_text = font.render("Planets will glow when mouse is near", True, (150, 150, 150))
        screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, 60))
    else:
        # Draw zoomed planet view
        zoomed_planet.draw_zoomed(screen)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()