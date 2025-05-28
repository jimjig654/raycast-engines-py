import pygame
import numpy as np
import math
import random
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1024, 768
HALF_HEIGHT = HEIGHT // 2
FOV = 60  # Field of view
HALF_FOV = FOV / 2
RAY_COUNT = WIDTH // 2  # Number of rays to cast
MAX_DEPTH = 20  # Maximum ray distance
CELL_SIZE = 64  # Size of each cell in the map
PLAYER_SIZE = 10
PLAYER_SPEED = 3
ROTATION_SPEED = 2

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

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trippy Raycasting Engine")
clock = pygame.time.Clock()

# Create a simple map (1 = wall, 0 = empty space)
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)

# Player settings
player_x = CELL_SIZE * 2
player_y = CELL_SIZE * 2
player_angle = 0  # Facing East initially

# Distortion settings
distortion_enabled = True
distortion_level = 0.5  # 0.0 to 1.0
distortion_frequency = 0.1  # How quickly distortion changes
distortion_time = 0
wave_amplitude = 0.2  # Amplitude of the sine wave for ray bending
wave_frequency = 0.1  # Frequency of the sine wave for ray bending
color_shift_speed = 0.02  # Speed of color shifting
portal_positions = [(8, 8, 12, 3)]  # (x1, y1, x2, y2) pairs for portals

# Texture settings
texture_width = 64
texture_height = 64

# Create some simple textures
def create_texture(color1, color2, pattern="checker"):
    texture = np.zeros((texture_height, texture_width, 3), dtype=np.uint8)
    
    if pattern == "checker":
        for y in range(texture_height):
            for x in range(texture_width):
                if (x // 8 + y // 8) % 2 == 0:
                    texture[y, x] = color1
                else:
                    texture[y, x] = color2
    elif pattern == "brick":
        for y in range(texture_height):
            for x in range(texture_width):
                if (y % 16 < 8) or (x + 8 * (y // 16 % 2)) % 16 < 14:
                    texture[y, x] = color1
                else:
                    texture[y, x] = color2
    elif pattern == "gradient":
        for y in range(texture_height):
            t = y / texture_height
            r = int(color1[0] * (1 - t) + color2[0] * t)
            g = int(color1[1] * (1 - t) + color2[1] * t)
            b = int(color1[2] * (1 - t) + color2[2] * t)
            for x in range(texture_width):
                texture[y, x] = (r, g, b)
    
    return texture

# Create different wall textures
textures = [
    create_texture(RED, YELLOW, "checker"),
    create_texture(BLUE, CYAN, "brick"),
    create_texture(GREEN, PURPLE, "gradient"),
    create_texture(WHITE, GRAY, "checker")
]

# Function to check if a position is inside a wall
def is_wall(x, y):
    map_x = int(x / CELL_SIZE)
    map_y = int(y / CELL_SIZE)
    
    if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
        return True
    
    return MAP[map_y][map_x] == 1

# Function to apply distortion to a ray angle
def apply_distortion(angle, distance, time):
    if not distortion_enabled:
        return angle
    
    # Apply sine wave distortion based on distance and time
    distortion = math.sin(distance * wave_frequency + time * distortion_frequency) * wave_amplitude
    distortion *= distortion_level
    
    return angle + distortion

# Function to check if a position is near a portal
def check_portal(x, y):
    cell_x, cell_y = int(x / CELL_SIZE), int(y / CELL_SIZE)
    
    for portal_x1, portal_y1, portal_x2, portal_y2 in portal_positions:
        if cell_x == portal_x1 and cell_y == portal_y1:
            return (portal_x2 * CELL_SIZE + CELL_SIZE / 2, portal_y2 * CELL_SIZE + CELL_SIZE / 2)
    
    return None

# Function to cast a ray and find the distance to a wall
def cast_ray(angle, player_pos_x, player_pos_y):
    # Normalize angle
    angle = angle % (2 * math.pi)
    
    # Direction vector
    dir_x = math.cos(angle)
    dir_y = math.sin(angle)
    
    # Current position
    pos_x, pos_y = player_pos_x, player_pos_y
    
    # Distance traveled
    distance = 0
    
    # History of ray positions for visualization
    ray_history = [(pos_x, pos_y)]
    
    # Cast the ray with distortion
    while distance < MAX_DEPTH * CELL_SIZE:
        # Apply distortion to the ray direction
        distorted_angle = apply_distortion(angle, distance / CELL_SIZE, distortion_time)
        dir_x = math.cos(distorted_angle)
        dir_y = math.sin(distorted_angle)
        
        # Step size (smaller steps for more accurate distortion)
        step_size = 5
        
        # Move the ray
        pos_x += dir_x * step_size
        pos_y += dir_y * step_size
        distance += step_size
        
        # Check for portal
        portal_dest = check_portal(pos_x, pos_y)
        if portal_dest:
            pos_x, pos_y = portal_dest
            ray_history.append((pos_x, pos_y))
        
        # Store ray position for visualization
        if len(ray_history) % 5 == 0:  # Store every 5th position to save memory
            ray_history.append((pos_x, pos_y))
        
        # Check if we hit a wall
        if is_wall(pos_x, pos_y):
            # Calculate the exact hit position for texture mapping
            map_x, map_y = int(pos_x / CELL_SIZE), int(pos_y / CELL_SIZE)
            
            # Determine which side of the wall was hit (N/S or E/W)
            # This affects the texture mapping and shading
            cell_x = map_x * CELL_SIZE
            cell_y = map_y * CELL_SIZE
            
            # Calculate texture coordinate
            if abs(pos_x - cell_x) < abs(pos_y - cell_y):
                # Hit vertical wall (E/W)
                texture_x = int((pos_y % CELL_SIZE) / CELL_SIZE * texture_width)
                wall_type = 0  # Use first texture for E/W walls
            else:
                # Hit horizontal wall (N/S)
                texture_x = int((pos_x % CELL_SIZE) / CELL_SIZE * texture_width)
                wall_type = 1  # Use second texture for N/S walls
            
            return distance, ray_history, texture_x, wall_type
    
    # If we didn't hit anything, return maximum distance
    return MAX_DEPTH * CELL_SIZE, ray_history, 0, 0

# Function to render the 3D view
def render_3d_view():
    # Clear the screen
    screen.fill(BLACK)
    
    # Draw sky (gradient from dark blue to light blue)
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(0 * (1 - t) + 100 * t)
        g = int(0 * (1 - t) + 150 * t)
        b = int(50 * (1 - t) + 255 * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    
    # Draw floor (gradient from dark gray to light gray)
    for y in range(HALF_HEIGHT, HEIGHT):
        t = (y - HALF_HEIGHT) / HALF_HEIGHT
        r = int(50 * (1 - t) + 100 * t)
        g = int(50 * (1 - t) + 100 * t)
        b = int(50 * (1 - t) + 100 * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    
    # Cast rays for each column of the screen
    ray_histories = []
    
    for x in range(WIDTH):
        # Calculate the ray angle
        ray_angle = (player_angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Cast the ray
        distance, ray_history, texture_x, wall_type = cast_ray(ray_angle, player_x, player_y)
        ray_histories.append(ray_history)
        
        # Apply fish-eye correction
        distance = distance * math.cos(ray_angle - player_angle)
        
        # Calculate wall height based on distance
        wall_height = (CELL_SIZE / distance) * ((WIDTH / 2) / math.tan(math.radians(HALF_FOV)))
        
        # Apply trippy color shifting based on time
        color_shift = (math.sin(distortion_time * color_shift_speed) + 1) / 2
        
        # Draw the wall slice
        wall_top = max(0, HALF_HEIGHT - wall_height // 2)
        wall_bottom = min(HEIGHT, HALF_HEIGHT + wall_height // 2)
        
        # Get the texture for this wall
        texture = textures[wall_type]
        
        # Draw the textured wall slice
        for y in range(int(wall_top), int(wall_bottom)):
            # Calculate texture y-coordinate
            texture_y = int((y - wall_top) / (wall_bottom - wall_top) * texture_height)
            
            # Get the texture color
            color = texture[texture_y, texture_x]
            
            # Apply distance shading and trippy effects
            shade = 1.0 - min(1.0, distance / (MAX_DEPTH * CELL_SIZE))
            
            # Apply color shifting if distortion is enabled
            if distortion_enabled:
                r = int(color[0] * shade * (1 + color_shift * 0.3))
                g = int(color[1] * shade * (1 + (1 - color_shift) * 0.3))
                b = int(color[2] * shade)
                color = (min(255, r), min(255, g), min(255, b))
            else:
                color = tuple(int(c * shade) for c in color)
            
            # Draw the pixel
            screen.set_at((x, y), color)
    
    # Draw a minimap in the corner
    minimap_size = 150
    minimap_scale = minimap_size / (MAP_WIDTH * CELL_SIZE)
    minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    minimap_surface.fill((0, 0, 0, 128))  # Semi-transparent background
    
    # Draw walls on minimap
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if MAP[y][x] == 1:
                pygame.draw.rect(
                    minimap_surface,
                    WHITE,
                    (x * CELL_SIZE * minimap_scale, y * CELL_SIZE * minimap_scale, 
                     CELL_SIZE * minimap_scale, CELL_SIZE * minimap_scale)
                )
    
    # Draw ray paths on minimap (only every 10th ray to avoid clutter)
    for i in range(0, len(ray_histories), 10):
        ray_history = ray_histories[i]
        if len(ray_history) > 1:
            points = [(int(x * minimap_scale), int(y * minimap_scale)) for x, y in ray_history]
            pygame.draw.lines(minimap_surface, (255, 0, 0, 150), False, points, 1)
    
    # Draw player on minimap
    pygame.draw.circle(
        minimap_surface,
        GREEN,
        (int(player_x * minimap_scale), int(player_y * minimap_scale)),
        int(PLAYER_SIZE * minimap_scale)
    )
    
    # Draw player direction on minimap
    end_x = player_x + math.cos(player_angle) * CELL_SIZE
    end_y = player_y + math.sin(player_angle) * CELL_SIZE
    pygame.draw.line(
        minimap_surface,
        GREEN,
        (int(player_x * minimap_scale), int(player_y * minimap_scale)),
        (int(end_x * minimap_scale), int(end_y * minimap_scale)),
        2
    )
    
    # Draw portals on minimap
    for portal_x1, portal_y1, portal_x2, portal_y2 in portal_positions:
        pygame.draw.circle(
            minimap_surface,
            CYAN,
            (int((portal_x1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((portal_y1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            int(CELL_SIZE / 3 * minimap_scale)
        )
        pygame.draw.circle(
            minimap_surface,
            PURPLE,
            (int((portal_x2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((portal_y2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            int(CELL_SIZE / 3 * minimap_scale)
        )
    
    # Draw minimap to screen
    screen.blit(minimap_surface, (10, 10))
    
    # Draw distortion status
    font = pygame.font.SysFont(None, 24)
    status_text = f"Distortion: {'ON' if distortion_enabled else 'OFF'} (SPACE to toggle)"
    text_surface = font.render(status_text, True, WHITE)
    screen.blit(text_surface, (10, HEIGHT - 30))

# Main game loop
def main():
    global player_x, player_y, player_angle, distortion_enabled, distortion_time
    
    running = True
    mouse_locked = True
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    # For smooth movement
    moving_forward = False
    moving_backward = False
    moving_left = False
    moving_right = False
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle key presses
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    moving_forward = True
                elif event.key == pygame.K_s:
                    moving_backward = True
                elif event.key == pygame.K_a:
                    moving_left = True
                elif event.key == pygame.K_d:
                    moving_right = True
                elif event.key == pygame.K_SPACE:
                    distortion_enabled = not distortion_enabled
            
            # Handle key releases
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    moving_forward = False
                elif event.key == pygame.K_s:
                    moving_backward = False
                elif event.key == pygame.K_a:
                    moving_left = False
                elif event.key == pygame.K_d:
                    moving_right = False
            
            # Handle mouse movement for looking around
            elif event.type == pygame.MOUSEMOTION and mouse_locked:
                # Adjust player angle based on mouse movement
                player_angle += math.radians(event.rel[0] * 0.1)
        
        # Update player position based on movement keys
        move_speed = PLAYER_SPEED
        
        # Calculate movement vector
        dx, dy = 0, 0
        
        if moving_forward:
            dx += math.cos(player_angle) * move_speed
            dy += math.sin(player_angle) * move_speed
        if moving_backward:
            dx -= math.cos(player_angle) * move_speed
            dy -= math.sin(player_angle) * move_speed
        if moving_left:
            dx += math.cos(player_angle - math.pi/2) * move_speed
            dy += math.sin(player_angle - math.pi/2) * move_speed
        if moving_right:
            dx += math.cos(player_angle + math.pi/2) * move_speed
            dy += math.sin(player_angle + math.pi/2) * move_speed
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx = dx / length * move_speed
            dy = dy / length * move_speed
        
        # Check if new position would be in a wall
        new_x = player_x + dx
        new_y = player_y + dy
        
        # Check for portal at new position
        portal_dest = check_portal(new_x, new_y)
        if portal_dest:
            player_x, player_y = portal_dest
        else:
            # Only move if not hitting a wall
            if not is_wall(new_x, player_y):
                player_x = new_x
            if not is_wall(player_x, new_y):
                player_y = new_y
        
        # Update distortion time
        distortion_time += 0.05
        
        # Render the 3D view
        render_3d_view()
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
