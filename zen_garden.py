import pygame
import random

# --- Initialization ---
pygame.init()

# Define screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Colors
SAND_COLOR = (244, 235, 204) # Light, calming beige/sand color
RAKE_COLOR = (150, 150, 150) # Darker gray for the rake line
LINE_THICKNESS = 4

# Setup the screen and title
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Zen Garden Simulator")

# Game clock
clock = pygame.time.Clock()

# --- Drawing State Variables ---
# List to store all the points drawn by the mouse
drawing_points = []
is_raking = False

# --- Main Game Loop ---
running = True
while running:
    
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Start Raking (Mouse Button Down)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                is_raking = True
                # Start a new rake stroke with the current mouse position
                drawing_points.append(pygame.mouse.get_pos()) 
        
        # Stop Raking (Mouse Button Up)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_raking = False
        
        # Record Mouse Movement (when holding the button down)
        elif event.type == pygame.MOUSEMOTION:
            if is_raking:
                # Only add a point if the mouse is moving and the button is down
                drawing_points.append(pygame.mouse.get_pos())


    # 2. Drawing (Render)
    # The first thing we do is fill the screen with the base sand color.
    screen.fill(SAND_COLOR) 

    # Draw Rake Marks
    # pygame.draw.lines is used to connect a list of points smoothly
    if len(drawing_points) > 1:
        # pygame.draw.aaline(s) are better for smooth lines, but lines() is simpler for beginners
        pygame.draw.lines(
            screen,          # Surface to draw on
            RAKE_COLOR,      # Color of the rake mark
            False,           # False means don't connect the last point to the first (not a closed loop)
            drawing_points,  # The list of (x, y) coordinates
            LINE_THICKNESS   # The thickness of the rake mark
        )

    # 3. Auto-Smooth/Clear Mechanic (The Zen Part)
    # To simulate the sand settling, we'll slowly remove older points.
    # We remove points a little faster when the player isn't actively raking.
    
    # Define a clear rate (number of points to remove per frame)
    if not is_raking and len(drawing_points) > 0:
        clear_rate = 3  # Faster decay when not raking
        
        # Remove a few points from the beginning of the list
        drawing_points = drawing_points[clear_rate:] 
    
    elif is_raking and len(drawing_points) > 200:
        # If the list gets too long while raking, trim the oldest points for performance
        drawing_points = drawing_points[1:]


    # Update the full screen display
    pygame.display.flip()

    # Limit frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()