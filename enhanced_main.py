import pygame
import numpy as np
import math
import random
import time
from trippy_effects import TrippyEffects
from non_euclidean_map import NonEuclideanMap

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600  # Reduced resolution for better performance
HALF_HEIGHT = HEIGHT // 2
FOV = 60  # Field of view
HALF_FOV = FOV / 2
RAY_COUNT = WIDTH // 2  # Cast fewer rays for better performance
MAX_DEPTH = 15  # Reduced maximum ray distance
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
pygame.display.set_caption("Trippy Non-Euclidean Raycasting Engine")
clock = pygame.time.Clock()

# Create the map
map_generator = NonEuclideanMap(16, 16, CELL_SIZE)

# Create trippy effects handler
effects = TrippyEffects()

# Player settings
player_x = CELL_SIZE * 2
player_y = CELL_SIZE * 2
player_angle = 0  # Facing East initially

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
    elif pattern == "psychedelic":
        for y in range(texture_height):
            for x in range(texture_width):
                r = (math.sin(x * 0.1) + 1) * 127
                g = (math.sin(y * 0.1 + 2) + 1) * 127
                b = (math.sin((x + y) * 0.1 + 4) + 1) * 127
                texture[y, x] = (int(r), int(g), int(b))
    
    return texture

# Create different wall textures
textures = [
    create_texture(RED, YELLOW, "checker"),
    create_texture(BLUE, CYAN, "brick"),
    create_texture(GREEN, PURPLE, "gradient"),
    create_texture(WHITE, GRAY, "psychedelic")
]

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
    
    # Use larger step size for better performance
    base_step_size = 10
    
    # Cast the ray with distortion
    while distance < MAX_DEPTH * CELL_SIZE:
        # Only apply distortion every few steps for better performance
        if distance % 30 < 0.1 or distance < 1:
            # Apply distortion to the ray direction
            distorted_angle = angle + effects.apply_ray_distortion(angle, distance / CELL_SIZE)
            
            # Add map-based distortion (less frequently)
            if distance % 60 < 0.1:
                map_distortion = map_generator.get_distortion(pos_x, pos_y, angle, distance)
                distorted_angle += map_distortion
            
            dir_x = math.cos(distorted_angle)
            dir_y = math.sin(distorted_angle)
        
        # Adaptive step size - larger steps when far from player
        step_size = base_step_size + (distance / CELL_SIZE)
        step_size = min(step_size, 20)  # Cap at reasonable maximum
        
        # Move the ray
        pos_x += dir_x * step_size
        pos_y += dir_y * step_size
        distance += step_size
        
        # Check for portal (less frequently for performance)
        if distance % 20 < step_size:
            portal_dest = map_generator.check_portal(pos_x, pos_y)
            if portal_dest:
                pos_x, pos_y = portal_dest
                ray_history.append((pos_x, pos_y))
        
        # Store ray position for visualization (less frequently)
        if len(ray_history) % 10 == 0:  # Store every 10th position to save memory
            ray_history.append((pos_x, pos_y))
        
        # Check if we hit a wall
        if map_generator.is_wall(pos_x, pos_y):
            # For performance, only check impossible spaces if not in a regular wall
            # Calculate the exact hit position for texture mapping
            map_x, map_y = int(pos_x / CELL_SIZE), int(pos_y / CELL_SIZE)
            
            # Determine which side of the wall was hit (N/S or E/W)
            # This affects the texture mapping and shading
            cell_x = map_x * CELL_SIZE
            cell_y = map_y * CELL_SIZE
            
            # Get texture ID from the map
            texture_id = map_generator.get_texture(pos_x, pos_y)
            
            # Calculate texture coordinate
            if abs(pos_x - cell_x) < abs(pos_y - cell_y):
                # Hit vertical wall (E/W)
                texture_x = int((pos_y % CELL_SIZE) / CELL_SIZE * texture_width)
                wall_type = texture_id
            else:
                # Hit horizontal wall (N/S)
                texture_x = int((pos_x % CELL_SIZE) / CELL_SIZE * texture_width)
                wall_type = texture_id
            
            return distance, ray_history, texture_x, wall_type
        elif distance % 30 < step_size and map_generator.is_in_impossible_space(pos_x, pos_y):
            # Check impossible spaces less frequently
            # Use a default texture for impossible spaces
            texture_x = int((pos_x % CELL_SIZE) / CELL_SIZE * texture_width)
            wall_type = 3  # Use the psychedelic texture for impossible spaces
            
            return distance, ray_history, texture_x, wall_type
    
    # If we didn't hit anything, return maximum distance
    return MAX_DEPTH * CELL_SIZE, ray_history, 0, 0

# Function to render the 3D view
def render_3d_view(fps=0):
    # Create a surface for the 3D view
    view_surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Draw sky (gradient from dark blue to light blue)
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(0 * (1 - t) + 100 * t)
        g = int(0 * (1 - t) + 150 * t)
        b = int(50 * (1 - t) + 255 * t)
        pygame.draw.line(view_surface, (r, g, b), (0, y), (WIDTH, y))
    
    # Draw floor (gradient from dark gray to light gray)
    for y in range(HALF_HEIGHT, HEIGHT):
        t = (y - HALF_HEIGHT) / HALF_HEIGHT
        r = int(50 * (1 - t) + 100 * t)
        g = int(50 * (1 - t) + 100 * t)
        b = int(50 * (1 - t) + 100 * t)
        pygame.draw.line(view_surface, (r, g, b), (0, y), (WIDTH, y))
    
    # Apply FOV distortion
    fov_distortion = effects.get_fov_distortion()
    current_fov = FOV + fov_distortion
    
    # Cast rays for each column of the screen
    ray_histories = []

    # Optimize by casting rays at intervals and interpolating between them
    for x in range(0, WIDTH, 2):
        # Calculate the ray angle with FOV distortion
        ray_angle = (player_angle - math.radians(current_fov / 2)) + (x / WIDTH) * math.radians(current_fov)
        
        # Cast the ray
        distance, ray_history, texture_x, wall_type = cast_ray(ray_angle, player_x, player_y)
        ray_histories.append(ray_history)
        
        # Apply fish-eye correction
        distance = distance * math.cos(ray_angle - player_angle)
        
        # Calculate wall height based on distance
        wall_height = (CELL_SIZE / distance) * ((WIDTH / 2) / math.tan(math.radians(HALF_FOV)))
        
        # Draw the wall slice
        wall_top = max(0, HALF_HEIGHT - wall_height // 2)
        wall_bottom = min(HEIGHT, HALF_HEIGHT + wall_height // 2)
        
        # Get the texture for this wall
        texture = textures[wall_type % len(textures)]
        
        # Draw the textured wall slice
        # Optimize by drawing vertical lines instead of individual pixels
        height = int(wall_bottom - wall_top)
        if height > 0:
            # Create a small surface for this wall slice
            slice_surf = pygame.Surface((2, height))
            
            # Draw the textured wall slice
            for y in range(height):
                # Calculate texture y-coordinate
                texture_y = int((y / height) * texture_height)
                
                # Get the texture color
                color = texture[texture_y, texture_x]
                
                # Apply distance shading and trippy effects
                shade = 1.0 - min(1.0, distance / (MAX_DEPTH * CELL_SIZE))
                
                # Apply trippy color effects (but only sometimes to improve performance)
                if x % 4 == 0:  # Apply effects to every 4th column
                    color = effects.apply_color_distortion(color, distance, ray_angle)
                
                # Apply distance shading
                color = tuple(int(c * shade) for c in color)
                
                # Draw the pixel
                slice_surf.set_at((0, y), color)
                slice_surf.set_at((1, y), color)  # Also draw to the next column
            
            # Blit the slice to the main surface
            view_surface.blit(slice_surf, (x, int(wall_top)))
    
    # Apply visual effects only if FPS is above threshold to prevent slowdowns
    if fps > 15 or fps == 0:  # Apply when FPS unknown (first frame) or good enough
        # Apply afterimage effect
        effects.apply_afterimage(view_surface)
        
        # Apply visual noise
        effects.apply_visual_noise(view_surface)
    
    # Draw the final view to the screen
    screen.blit(view_surface, (0, 0))
    
    # Draw a minimap in the corner
    minimap_size = 150
    minimap_scale = minimap_size / (map_generator.width * CELL_SIZE)
    minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    minimap_surface.fill((0, 0, 0, 128))  # Semi-transparent background
    
    # Draw walls on minimap
    for y in range(map_generator.height):
        for x in range(map_generator.width):
            if map_generator.grid[y][x] == 1:
                pygame.draw.rect(
                    minimap_surface,
                    WHITE,
                    (x * CELL_SIZE * minimap_scale, y * CELL_SIZE * minimap_scale, 
                     CELL_SIZE * minimap_scale, CELL_SIZE * minimap_scale)
                )
    
    # Draw portals on minimap
    for x1, y1, x2, y2 in map_generator.portals:
        # Draw first portal entrance
        pygame.draw.circle(
            minimap_surface,
            CYAN,
            (int((x1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((y1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            int(CELL_SIZE / 3 * minimap_scale)
        )
        # Draw second portal entrance
        pygame.draw.circle(
            minimap_surface,
            PURPLE,
            (int((x2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((y2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            int(CELL_SIZE / 3 * minimap_scale)
        )
        # Draw connection line
        pygame.draw.line(
            minimap_surface,
            YELLOW,
            (int((x1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((y1 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            (int((x2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((y2 * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            1
        )
    
    # Draw distortion fields on minimap
    for field in map_generator.distortion_fields:
        pygame.draw.circle(
            minimap_surface,
            (255, 0, 255, 100),  # Semi-transparent magenta
            (int((field['x'] * CELL_SIZE + CELL_SIZE / 2) * minimap_scale), 
             int((field['y'] * CELL_SIZE + CELL_SIZE / 2) * minimap_scale)),
            int(field['radius'] * CELL_SIZE * minimap_scale),
            1
        )
    
    # Draw ray paths on minimap (only every 40th ray to avoid clutter)
    for i in range(0, len(ray_histories), 40):
        ray_history = ray_histories[i]
        if len(ray_history) > 1:
            # Optimize by reducing the number of points
            points = [(int(x * minimap_scale), int(y * minimap_scale)) for x, y in ray_history[::3]]
            if len(points) > 1:  # Make sure we have at least 2 points
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
    
    # Draw minimap to screen
    screen.blit(minimap_surface, (10, 10))
    
    # Draw HUD and status information
    font = pygame.font.SysFont(None, 24)
    
    # Display distortion status
    status_text = f"Distortion: {'ON' if effects.enabled else 'OFF'} (SPACE to toggle)"
    text_surface = font.render(status_text, True, WHITE)
    screen.blit(text_surface, (10, HEIGHT - 60))
    
    # Display controls
    controls_text = "Controls: WASD=Move, Mouse=Look, R=New Map, +/-=Adjust Intensity"
    text_surface = font.render(controls_text, True, WHITE)
    screen.blit(text_surface, (10, HEIGHT - 30))

# Main game loop
def main():
    global player_x, player_y, player_angle
    
    running = True
    mouse_locked = True
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    # For smooth movement
    moving_forward = False
    moving_backward = False
    moving_left = False
    moving_right = False
    
    # For FPS calculation
    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    
    while running:
        # Calculate delta time for smooth movement
        dt = clock.get_time() / 1000.0
        
        # Update trippy effects
        effects.update(dt)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle key presses
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Toggle mouse lock
                    mouse_locked = not mouse_locked
                    pygame.mouse.set_visible(not mouse_locked)
                    pygame.event.set_grab(mouse_locked)
                elif event.key == pygame.K_w:
                    moving_forward = True
                elif event.key == pygame.K_s:
                    moving_backward = True
                elif event.key == pygame.K_a:
                    moving_left = True
                elif event.key == pygame.K_d:
                    moving_right = True
                elif event.key == pygame.K_SPACE:
                    effects.toggle()
                elif event.key == pygame.K_r:
                    # Generate a new map
                    map_generator.generate_new_map()
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Increase effect intensity
                    effects.increase_intensity()
                elif event.key == pygame.K_MINUS:
                    # Decrease effect intensity
                    effects.decrease_intensity()
            
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
        move_speed = PLAYER_SPEED * dt * 60  # Normalize for 60 FPS
        
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
        
        # Apply trippy movement distortion
        if effects.enabled:
            dx, dy = effects.apply_movement_distortion(dx, dy)
        
        # Check if new position would be in a wall
        new_x = player_x + dx
        new_y = player_y + dy
        
        # Check for portal at new position
        portal_dest = map_generator.check_portal(new_x, new_y)
        if portal_dest:
            player_x, player_y = portal_dest
        else:
            # Only move if not hitting a wall
            if not map_generator.is_wall(new_x, player_y) and not map_generator.is_in_impossible_space(new_x, player_y):
                player_x = new_x
            if not map_generator.is_wall(player_x, new_y) and not map_generator.is_in_impossible_space(player_x, new_y):
                player_y = new_y
        
        # Clear the screen
        screen.fill(BLACK)
        
        # Render the 3D view
        render_3d_view(fps)
        
        # Calculate and display FPS
        fps_counter += 1
        if time.time() - fps_timer > 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_timer = time.time()
        
        font = pygame.font.SysFont(None, 24)
        fps_text = f"FPS: {fps}"
        text_surface = font.render(fps_text, True, WHITE)
        screen.blit(text_surface, (WIDTH - 100, 10))
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
