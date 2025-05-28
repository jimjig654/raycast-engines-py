import pygame
import numpy as np
import math
import random
import time
import os
from numba import njit, prange  # For just-in-time compilation and parallelization

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
HALF_HEIGHT = HEIGHT // 2
FOV = 60
HALF_FOV = FOV / 2
PLAYER_SIZE = 10
PLAYER_SPEED = 3

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Set up display with hardware acceleration
flags = pygame.HWSURFACE | pygame.DOUBLEBUF
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Ultra Fast Trippy Renderer")
clock = pygame.time.Clock()

# Create a texture atlas - a single texture containing all wall textures
TEXTURE_SIZE = 64
NUM_TEXTURES = 4
ATLAS_WIDTH = TEXTURE_SIZE * NUM_TEXTURES
ATLAS_HEIGHT = TEXTURE_SIZE

# Create texture atlas
def create_texture_atlas():
    atlas = np.zeros((ATLAS_HEIGHT, ATLAS_WIDTH, 3), dtype=np.uint8)
    
    # Texture 1: Brick
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            # Brick pattern
            brick_x = x % 16
            brick_y = y % 16
            if brick_x == 0 or brick_y == 0:
                atlas[y, x] = [120, 60, 30]  # Mortar
            else:
                atlas[y, x] = [200, 70, 60]  # Brick
    
    # Texture 2: Psychedelic
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            # Psychedelic pattern
            r = int(127 + 127 * math.sin(x * 0.1 + y * 0.1))
            g = int(127 + 127 * math.sin(x * 0.1 + y * 0.2 + 2))
            b = int(127 + 127 * math.sin(x * 0.1 + y * 0.3 + 4))
            atlas[y, x + TEXTURE_SIZE] = [r, g, b]
    
    # Texture 3: Checkerboard
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            # Checkerboard pattern
            if (x // 8 + y // 8) % 2 == 0:
                atlas[y, x + TEXTURE_SIZE * 2] = [240, 240, 240]  # White
            else:
                atlas[y, x + TEXTURE_SIZE * 2] = [20, 20, 20]  # Black
    
    # Texture 4: Gradient
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            # Gradient pattern
            t = y / TEXTURE_SIZE
            r = int(255 * t)
            g = int(100 + 100 * math.sin(t * 10))
            b = int(255 * (1 - t))
            atlas[y, x + TEXTURE_SIZE * 3] = [r, g, b]
    
    return atlas

# Create the texture atlas
texture_atlas = create_texture_atlas()

# Pre-render distortion effects
def create_distortion_map(width, height, time_offset=0):
    """Create a distortion map for warping effects"""
    distortion = np.zeros((height, width), dtype=np.float32)
    for y in range(height):
        for x in range(width):
            # Create various wave patterns
            value = 0.0
            value += math.sin(x * 0.02 + time_offset) * 2.0
            value += math.sin(y * 0.03 + time_offset * 1.5) * 1.5
            value += math.sin((x + y) * 0.02 + time_offset * 0.7) * 1.0
            distortion[y, x] = value
    return distortion

# Pre-render some distortion maps for different time offsets
NUM_DISTORTION_MAPS = 16
distortion_maps = [create_distortion_map(WIDTH, HEIGHT, i * 0.2) for i in range(NUM_DISTORTION_MAPS)]

# Create a simple map (1 = wall, 0 = empty space)
MAP_SIZE = 16
MAP = np.zeros((MAP_SIZE, MAP_SIZE), dtype=np.int32)

# Fill the border with walls
MAP[0, :] = 1
MAP[MAP_SIZE-1, :] = 1
MAP[:, 0] = 1
MAP[:, MAP_SIZE-1] = 1

# Add some random walls
for _ in range(20):
    x = random.randint(2, MAP_SIZE-3)
    y = random.randint(2, MAP_SIZE-3)
    MAP[y, x] = 1

# Add some portals (special walls that teleport)
PORTALS = []
for _ in range(3):
    x1, y1 = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
    x2, y2 = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
    if MAP[y1, x1] == 0 and MAP[y2, x2] == 0:
        PORTALS.append((x1, y1, x2, y2))
        # Mark portals with special values
        MAP[y1, x1] = 2
        MAP[y2, x2] = 2

# Create distortion fields
DISTORTION_FIELDS = []
for _ in range(4):
    x = random.randint(1, MAP_SIZE-2)
    y = random.randint(1, MAP_SIZE-2)
    radius = random.uniform(1.5, 3.0)
    strength = random.uniform(0.2, 0.8)
    DISTORTION_FIELDS.append((x, y, radius, strength))

# Player settings
player_x = 1.5
player_y = 1.5
player_angle = 0.0
player_height = 0.5

# Pre-compute sin and cos tables for performance
SIN_TABLE = np.array([math.sin(math.radians(i)) for i in range(360)], dtype=np.float32)
COS_TABLE = np.array([math.cos(math.radians(i)) for i in range(360)], dtype=np.float32)

# Optimized ray casting using Numba for JIT compilation
@njit(fastmath=True)
def fast_raycast(player_x, player_y, player_angle, map_data, width, height, fov):
    """Optimized ray casting function using Numba"""
    # Pre-allocate arrays for results
    wall_heights = np.zeros(width, dtype=np.float32)
    wall_textures = np.zeros(width, dtype=np.int32)
    wall_texture_x = np.zeros(width, dtype=np.float32)
    wall_distances = np.zeros(width, dtype=np.float32)
    
    # Constants
    map_size = len(map_data)
    half_fov = fov / 2
    
    # For each column on the screen
    for x in range(width):
        # Calculate ray angle
        ray_angle = (player_angle - math.radians(half_fov)) + (x / width) * math.radians(fov)
        
        # Normalize angle
        ray_angle = ray_angle % (2 * math.pi)
        
        # Ray direction
        ray_dir_x = math.cos(ray_angle)
        ray_dir_y = math.sin(ray_angle)
        
        # Current map position
        map_x = int(player_x)
        map_y = int(player_y)
        
        # Length of ray from current position to next x or y-side
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')
        
        # Direction to step in
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1
        
        # Length of ray from one side to next
        if ray_dir_x < 0:
            side_dist_x = (player_x - map_x) * delta_dist_x
        else:
            side_dist_x = (map_x + 1.0 - player_x) * delta_dist_x
            
        if ray_dir_y < 0:
            side_dist_y = (player_y - map_y) * delta_dist_y
        else:
            side_dist_y = (map_y + 1.0 - player_y) * delta_dist_y
        
        # Perform DDA (Digital Differential Analysis)
        hit = 0
        side = 0
        max_distance = 20.0
        distance = 0.0
        
        while hit == 0 and distance < max_distance:
            # Jump to next map square
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
                distance += delta_dist_x
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
                distance += delta_dist_y
            
            # Check if ray has hit a wall
            if 0 <= map_x < map_size and 0 <= map_y < map_size:
                if map_data[map_y, map_x] > 0:
                    hit = 1
        
        # Calculate distance projected on camera direction
        if hit == 1:
            if side == 0:
                perp_wall_dist = side_dist_x - delta_dist_x
                wall_x = player_y + perp_wall_dist * ray_dir_y
            else:
                perp_wall_dist = side_dist_y - delta_dist_y
                wall_x = player_x + perp_wall_dist * ray_dir_x
            
            wall_x -= math.floor(wall_x)
            
            # Calculate texture coordinate
            tex_x = int(wall_x * TEXTURE_SIZE)
            if (side == 0 and ray_dir_x > 0) or (side == 1 and ray_dir_y < 0):
                tex_x = TEXTURE_SIZE - tex_x - 1
            
            # Store results
            wall_heights[x] = min(height, height / perp_wall_dist)
            wall_textures[x] = (map_data[map_y, map_x] - 1) % NUM_TEXTURES
            wall_texture_x[x] = tex_x
            wall_distances[x] = perp_wall_dist
        else:
            # No wall hit
            wall_heights[x] = 0
            wall_textures[x] = 0
            wall_texture_x[x] = 0
            wall_distances[x] = max_distance
    
    return wall_heights, wall_textures, wall_texture_x, wall_distances

# Optimized rendering using pre-rendered columns
def render_frame(player_x, player_y, player_angle, distortion_level=0.0, distortion_map_index=0):
    # Create a surface for the frame
    frame = pygame.Surface((WIDTH, HEIGHT))
    
    # Draw sky (gradient)
    sky = pygame.Surface((WIDTH, HALF_HEIGHT))
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(0 * (1 - t) + 100 * t)
        g = int(0 * (1 - t) + 150 * t)
        b = int(50 * (1 - t) + 255 * t)
        pygame.draw.line(sky, (r, g, b), (0, y), (WIDTH, y))
    frame.blit(sky, (0, 0))
    
    # Draw floor (gradient)
    floor = pygame.Surface((WIDTH, HALF_HEIGHT))
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(50 * (1 - t) + 100 * t)
        g = int(50 * (1 - t) + 100 * t)
        b = int(50 * (1 - t) + 100 * t)
        pygame.draw.line(floor, (r, g, b), (0, y), (WIDTH, y))
    frame.blit(floor, (0, HALF_HEIGHT))
    
    # Get distortion map for current frame
    distortion_map = distortion_maps[distortion_map_index]
    
    # Perform raycasting
    wall_heights, wall_textures, wall_texture_x, wall_distances = fast_raycast(
        player_x, player_y, player_angle, MAP, WIDTH, HEIGHT, FOV
    )
    
    # Draw walls
    for x in range(WIDTH):
        if wall_heights[x] > 0:
            # Calculate wall height
            wall_height = wall_heights[x]
            wall_top = max(0, HALF_HEIGHT - wall_height // 2)
            wall_bottom = min(HEIGHT, HALF_HEIGHT + wall_height // 2)
            
            # Apply distortion to wall height if enabled
            if distortion_level > 0:
                distortion = distortion_map[int(wall_top) % HEIGHT, x] * distortion_level
                wall_top = max(0, wall_top + distortion)
                wall_bottom = min(HEIGHT, wall_bottom + distortion)
            
            # Get texture for this wall
            texture_id = int(wall_textures[x])
            texture_x = int(wall_texture_x[x])
            
            # Draw the wall slice
            wall_slice = pygame.Surface((1, int(wall_bottom - wall_top)))
            
            # Extract the texture column from the atlas
            atlas_x = texture_x + texture_id * TEXTURE_SIZE
            
            # Draw the textured wall slice
            for y in range(int(wall_bottom - wall_top)):
                # Calculate texture y-coordinate
                texture_y = int((y / (wall_bottom - wall_top)) * TEXTURE_SIZE)
                
                # Get color from texture atlas
                color = texture_atlas[texture_y, atlas_x]
                
                # Apply distance shading
                shade = 1.0 - min(1.0, wall_distances[x] / 20.0)
                color = tuple(int(c * shade) for c in color)
                
                # Apply trippy color shifting based on time and position
                if distortion_level > 0:
                    shift = math.sin(time.time() * 2 + x * 0.01 + y * 0.01) * distortion_level * 0.3
                    r = min(255, int(color[0] * (1 + shift)))
                    g = min(255, int(color[1] * (1 - shift)))
                    b = color[2]
                    color = (r, g, b)
                
                # Draw pixel
                wall_slice.set_at((0, y), color)
            
            # Blit the wall slice to the frame
            frame.blit(wall_slice, (x, int(wall_top)))
    
    # Draw minimap
    minimap_size = 150
    minimap_scale = minimap_size / MAP_SIZE
    minimap = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    minimap.fill((0, 0, 0, 128))
    
    # Draw walls on minimap
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            if MAP[y, x] == 1:  # Regular wall
                pygame.draw.rect(
                    minimap, WHITE,
                    (x * minimap_scale, y * minimap_scale, minimap_scale, minimap_scale)
                )
            elif MAP[y, x] == 2:  # Portal
                pygame.draw.rect(
                    minimap, (0, 255, 255),
                    (x * minimap_scale, y * minimap_scale, minimap_scale, minimap_scale)
                )
    
    # Draw player on minimap
    pygame.draw.circle(
        minimap, GREEN,
        (int(player_x * minimap_scale), int(player_y * minimap_scale)),
        int(PLAYER_SIZE * minimap_scale / 4)
    )
    
    # Draw player direction
    end_x = player_x + math.cos(player_angle) * 0.5
    end_y = player_y + math.sin(player_angle) * 0.5
    pygame.draw.line(
        minimap, GREEN,
        (int(player_x * minimap_scale), int(player_y * minimap_scale)),
        (int(end_x * minimap_scale), int(end_y * minimap_scale)),
        2
    )
    
    # Draw distortion fields
    for x, y, radius, _ in DISTORTION_FIELDS:
        pygame.draw.circle(
            minimap, (255, 0, 255, 100),
            (int(x * minimap_scale), int(y * minimap_scale)),
            int(radius * minimap_scale),
            1
        )
    
    # Draw minimap to frame
    frame.blit(minimap, (10, 10))
    
    return frame

# Pre-render wall columns for each texture and distance
def pre_render_wall_columns():
    """Pre-render wall columns for different heights and textures"""
    columns = {}
    
    # For each texture
    for texture_id in range(NUM_TEXTURES):
        columns[texture_id] = {}
        
        # For each possible texture x-coordinate
        for tex_x in range(TEXTURE_SIZE):
            columns[texture_id][tex_x] = {}
            
            # For a range of wall heights (quantized)
            for height in range(0, HEIGHT * 2, 4):  # Step by 4 for efficiency
                if height == 0:
                    continue
                    
                # Create a column surface
                column = pygame.Surface((1, height))
                
                # Draw the textured column
                for y in range(height):
                    # Calculate texture y-coordinate
                    tex_y = int((y / height) * TEXTURE_SIZE)
                    
                    # Get color from texture atlas
                    atlas_x = tex_x + texture_id * TEXTURE_SIZE
                    color = texture_atlas[tex_y, atlas_x]
                    
                    # Draw pixel
                    column.set_at((0, y), color)
                
                # Store the pre-rendered column
                columns[texture_id][tex_x][height] = column
    
    return columns

# Main game loop
def main():
    global player_x, player_y, player_angle
    
    # Pre-render wall columns
    print("Pre-rendering wall columns...")
    # Commented out for now as it's memory intensive
    # pre_rendered_columns = pre_render_wall_columns()
    
    # Game state
    running = True
    mouse_locked = True
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    # Movement flags
    moving_forward = False
    moving_backward = False
    moving_left = False
    moving_right = False
    
    # Effects settings
    distortion_enabled = True
    distortion_level = 0.5
    distortion_map_index = 0
    distortion_time = 0
    
    # FPS tracking
    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    
    # Frame timing
    last_time = time.time()
    
    # Main loop
    while running:
        # Calculate delta time
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Update distortion
        distortion_time += dt
        if distortion_time >= 0.1:  # Change distortion map every 100ms
            distortion_time = 0
            distortion_map_index = (distortion_map_index + 1) % NUM_DISTORTION_MAPS
        
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
                    distortion_enabled = not distortion_enabled
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    distortion_level = min(1.0, distortion_level + 0.1)
                elif event.key == pygame.K_MINUS:
                    distortion_level = max(0.0, distortion_level - 0.1)
            
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
            
            # Handle mouse movement
            elif event.type == pygame.MOUSEMOTION and mouse_locked:
                # Adjust player angle based on mouse movement
                player_angle += math.radians(event.rel[0] * 0.1)
        
        # Calculate movement
        move_speed = PLAYER_SPEED * dt
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
        
        # Apply movement
        new_x = player_x + dx
        new_y = player_y + dy
        
        # Check for portals
        for x1, y1, x2, y2 in PORTALS:
            if int(new_x) == x1 and int(new_y) == y1:
                # Teleport to the other end of the portal
                new_x, new_y = x2 + 0.5, y2 + 0.5
                break
            elif int(new_x) == x2 and int(new_y) == y2:
                # Teleport to the other end of the portal
                new_x, new_y = x1 + 0.5, y1 + 0.5
                break
        
        # Check for collisions
        if 0 <= int(new_x) < MAP_SIZE and 0 <= int(new_y) < MAP_SIZE:
            if MAP[int(new_y), int(player_x)] != 1:  # Not a wall
                player_y = new_y
            if MAP[int(player_y), int(new_x)] != 1:  # Not a wall
                player_x = new_x
        
        # Apply distortion fields
        if distortion_enabled:
            for field_x, field_y, radius, strength in DISTORTION_FIELDS:
                dx = player_x - field_x
                dy = player_y - field_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < radius:
                    # Apply distortion to player angle
                    influence = 1.0 - (dist / radius)
                    angle_to_center = math.atan2(dy, dx)
                    player_angle += math.sin(angle_to_center - player_angle) * influence * strength * dt
        
        # Render the frame
        current_distortion = distortion_level if distortion_enabled else 0.0
        frame = render_frame(player_x, player_y, player_angle, current_distortion, distortion_map_index)
        
        # Display the frame
        screen.blit(frame, (0, 0))
        
        # Display FPS
        fps_counter += 1
        if current_time - fps_timer > 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_timer = current_time
        
        font = pygame.font.SysFont(None, 24)
        fps_text = f"FPS: {fps}"
        text_surface = font.render(fps_text, True, WHITE)
        screen.blit(text_surface, (WIDTH - 100, 10))
        
        # Display distortion status
        status_text = f"Distortion: {'ON' if distortion_enabled else 'OFF'} (SPACE) | Level: {distortion_level:.1f} (+/-)"
        text_surface = font.render(status_text, True, WHITE)
        screen.blit(text_surface, (10, HEIGHT - 30))
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(144)
    
    pygame.quit()

if __name__ == "__main__":
    # Check if Numba is available
    try:
        import numba
        print(f"Using Numba {numba.__version__} for acceleration")
    except ImportError:
        print("Numba not found. Install with: pip install numba")
        print("Continuing without Numba acceleration...")
    
    # Run the game
    main()
