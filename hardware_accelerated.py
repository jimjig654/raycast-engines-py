import pygame
import numpy as np
import math
import random
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from trippy_effects import TrippyEffects
from non_euclidean_map import NonEuclideanMap

# Initialize Pygame with hardware acceleration
pygame.init()
pygame.display.set_mode((100, 100), pygame.HIDDEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.quit()

# Constants - Utilize your powerful hardware with higher resolution and more rays
WIDTH, HEIGHT = 1280, 720  # Higher resolution for your powerful GPU
HALF_HEIGHT = HEIGHT // 2
FOV = 60  # Field of view
HALF_FOV = FOV / 2
RAY_COUNT = WIDTH  # Full ray count for high quality on powerful hardware
MAX_DEPTH = 20  # Maximum ray distance
CELL_SIZE = 64  # Size of each cell in the map
PLAYER_SIZE = 10
PLAYER_SPEED = 3
ROTATION_SPEED = 2
NUM_THREADS = 16  # Utilize your Ryzen 9 with multiple threads

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

# Set up the display with hardware acceleration
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Trippy Non-Euclidean Raycasting Engine (Hardware Accelerated)")
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

# Pre-compute sin and cos values for performance
sin_table = np.array([math.sin(math.radians(i)) for i in range(360)], dtype=np.float32)
cos_table = np.array([math.cos(math.radians(i)) for i in range(360)], dtype=np.float32)

def fast_sin(angle):
    # Convert angle to degrees and get index in lookup table
    index = int(math.degrees(angle) % 360)
    return sin_table[index]

def fast_cos(angle):
    # Convert angle to degrees and get index in lookup table
    index = int(math.degrees(angle) % 360)
    return cos_table[index]

# Function to cast a ray and find the distance to a wall
def cast_ray(angle, player_pos_x, player_pos_y):
    # Normalize angle
    angle = angle % (2 * math.pi)
    
    # Direction vector using lookup tables for performance
    dir_x = fast_cos(angle)
    dir_y = fast_sin(angle)
    
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
            
            dir_x = fast_cos(distorted_angle)
            dir_y = fast_sin(distorted_angle)
        
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

# Function to process a batch of rays in parallel
def process_ray_batch(start_x, end_x, player_angle, current_fov, player_x, player_y):
    results = []
    for x in range(start_x, end_x):
        # Calculate the ray angle with FOV distortion
        ray_angle = (player_angle - math.radians(current_fov / 2)) + (x / WIDTH) * math.radians(current_fov)
        
        # Cast the ray
        distance, ray_history, texture_x, wall_type = cast_ray(ray_angle, player_x, player_y)
        
        # Apply fish-eye correction
        distance = distance * math.cos(ray_angle - player_angle)
        
        results.append((x, distance, ray_history, texture_x, wall_type, ray_angle))
    
    return results

# Function to render the 3D view with multithreading
def render_3d_view(fps=0):
    # Create a surface for the 3D view with hardware acceleration
    view_surface = pygame.Surface((WIDTH, HEIGHT), pygame.HWSURFACE)
    
    # Draw sky (gradient from dark blue to light blue)
    sky_array = np.zeros((HALF_HEIGHT, WIDTH, 3), dtype=np.uint8)
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(0 * (1 - t) + 100 * t)
        g = int(0 * (1 - t) + 150 * t)
        b = int(50 * (1 - t) + 255 * t)
        sky_array[y, :] = [r, g, b]
    
    sky_surface = pygame.surfarray.make_surface(sky_array)
    view_surface.blit(sky_surface, (0, 0))
    
    # Draw floor (gradient from dark gray to light gray)
    floor_array = np.zeros((HALF_HEIGHT, WIDTH, 3), dtype=np.uint8)
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(50 * (1 - t) + 100 * t)
        g = int(50 * (1 - t) + 100 * t)
        b = int(50 * (1 - t) + 100 * t)
        floor_array[y, :] = [r, g, b]
    
    floor_surface = pygame.surfarray.make_surface(floor_array)
    view_surface.blit(floor_surface, (0, HALF_HEIGHT))
    
    # Apply FOV distortion
    fov_distortion = effects.get_fov_distortion()
    current_fov = FOV + fov_distortion
    
    # Divide the screen into batches for multithreading
    batch_size = WIDTH // NUM_THREADS
    batches = [(i * batch_size, min((i + 1) * batch_size, WIDTH)) for i in range(NUM_THREADS)]
    
    # Process ray batches in parallel
    ray_results = []
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(process_ray_batch, start, end, player_angle, current_fov, player_x, player_y) 
                  for start, end in batches]
        
        for future in futures:
            ray_results.extend(future.result())
    
    # Sort results by x coordinate
    ray_results.sort(key=lambda x: x[0])
    
    # Extract ray histories for minimap
    ray_histories = [result[2] for result in ray_results]
    
    # Create wall slices
    for x, distance, _, texture_x, wall_type, ray_angle in ray_results:
        # Calculate wall height based on distance
        wall_height = (CELL_SIZE / distance) * ((WIDTH / 2) / math.tan(math.radians(HALF_FOV)))
        
        # Draw the wall slice
        wall_top = max(0, HALF_HEIGHT - wall_height // 2)
        wall_bottom = min(HEIGHT, HALF_HEIGHT + wall_height // 2)
        
        # Optimize by drawing vertical lines instead of individual pixels
        height = int(wall_bottom - wall_top)
        if height > 0:
            # Create a small surface for this wall slice
            slice_surf = pygame.Surface((1, height))
            
            # Get the texture for this wall
            texture = textures[wall_type % len(textures)]
            
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
            
            # Blit the slice to the main surface
            view_surface.blit(slice_surf, (x, int(wall_top)))
    
    # Apply visual effects only if FPS is above threshold to prevent slowdowns
    if fps > 20 or fps == 0:  # Apply when FPS unknown (first frame) or good enough
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
    end_x = player_x + fast_cos(player_angle) * CELL_SIZE
    end_y = player_y + fast_sin(player_angle) * CELL_SIZE
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
    
    # Display hardware acceleration status
    hw_text = f"Hardware Acceleration: ON | Threads: {NUM_THREADS} | Resolution: {WIDTH}x{HEIGHT}"
    text_surface = font.render(hw_text, True, WHITE)
    screen.blit(text_surface, (10, HEIGHT - 90))

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
            dx += fast_cos(player_angle) * move_speed
            dy += fast_sin(player_angle) * move_speed
        if moving_backward:
            dx -= fast_cos(player_angle) * move_speed
            dy -= fast_sin(player_angle) * move_speed
        if moving_left:
            dx += fast_cos(player_angle - math.pi/2) * move_speed
            dy += fast_sin(player_angle - math.pi/2) * move_speed
        if moving_right:
            dx += fast_cos(player_angle + math.pi/2) * move_speed
            dy += fast_sin(player_angle + math.pi/2) * move_speed
        
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
        clock.tick(144)  # Higher frame rate cap for powerful hardware
    
    pygame.quit()

if __name__ == "__main__":
    # Set process priority to high for better performance
    try:
        import psutil
        process = psutil.Process()
        process.nice(psutil.HIGH_PRIORITY_CLASS)
    except:
        pass
        
    main()
