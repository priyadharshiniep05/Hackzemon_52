import pygame
import random

import os # Import the os module for path safety

# --- Initialization ---
pygame.init()
pygame.mixer.init()

# Define screen dimensions and colors
SCREEN_WIDTH = 800
# ... (other dimension and color definitions) ...

# --- NEW: Load Sound Effect ---
# Check if the sound file exists before trying to load it
sound_file_path = os.path.join(os.path.dirname(__file__), 'pop_sound.wav')
if os.path.exists(sound_file_path):
    POP_SOUND = pygame.mixer.Sound(sound_file_path)
    # Adjust volume if needed (optional)
    POP_SOUND.set_volume(0.5) 
    print("Pop sound loaded successfully.")
else:
    # Use a dummy object if sound isn't found to prevent errors
    class DummySound:
        def play(self):
            pass
    POP_SOUND = DummySound()
    print("WARNING: 'pop_sound.wav' not found. Sound effect disabled.")


# Setup the screen and title
# ... (screen setup continues) ...

class Bubble:
    def __init__(self, x, y, radius):
        # ... (attributes remain the same) ...
        pass # All attributes remain the same

    # ... (draw method remains the same) ...

    def check_pop(self, pos):
        # Calculate distance between the click position and the bubble center
        distance = ((self.x - pos[0])**2 + (self.y - pos[1])**2)**0.5
        
        if distance < self.radius and not self.is_popped:
            self.is_popped = True
            
            # --- NEW: Play Sound Here ---
            global POP_SOUND
            POP_SOUND.play() # Plays the loaded sound file
            # ---------------------------
            
            return True
        return False

# Define screen dimensions and colors
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)

# Setup the screen and title
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Bubble Pop Relaxation")

# Game clock
clock = pygame.time.Clock()

class Bubble:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = BLUE
        self.is_popped = False

    def draw(self, surface):
        if not self.is_popped:
            # Draw the main circle
            pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
            # Draw a light highlight for a 3D effect
            pygame.draw.circle(surface, WHITE, (self.x - self.radius // 3, self.y - self.radius // 3), 
                               self.radius // 3, 1)

    def check_pop(self, pos):
        # Calculate distance between the click position and the bubble center
        distance = ((self.x - pos[0])**2 + (self.y - pos[1])**2)**0.5
        
        if distance < self.radius and not self.is_popped:
            self.is_popped = True
            global POP_SOUND
            POP_SOUND.play()
            return True
        return False

def create_bubble_grid():
    bubbles = []
    # Grid parameters
    rows = 6
    cols = 10
    padding = 20
    radius = 30
    
    # Calculate starting position for centering
    start_x = (SCREEN_WIDTH - (cols * (radius * 2 + padding) - padding)) // 2
    start_y = (SCREEN_HEIGHT - (rows * (radius * 2 + padding) - padding)) // 2

    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (2 * radius + padding) + radius
            y = start_y + r * (2 * radius + padding) + radius
            bubbles.append(Bubble(x, y, radius))
            
    return bubbles

all_bubbles = create_bubble_grid()

# --- Main Game Loop ---
running = True
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle Mouse Clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                
                for bubble in all_bubbles:
                    if bubble.check_pop(mouse_pos):
                        # Play a pop sound (requires a sound file)
                        # Optional: Add a subtle text message like "Pop!"
                        pass 

    # 2. Drawing (Render)
    screen.fill(WHITE) # Background color

    # Draw all bubbles
    popped_count = 0
    for bubble in all_bubbles:
        bubble.draw(screen)
        if bubble.is_popped:
            popped_count += 1
            
    # Check if all bubbles are popped (and regenerate)
    if popped_count == len(all_bubbles):
        # Simple regeneration after a 1-second delay
        pygame.time.wait(1000) 
        all_bubbles = create_bubble_grid()
        
    # Update the full screen display
    pygame.display.flip()

    # Limit frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()