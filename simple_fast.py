import pygame
import numpy as np
import math
import random
import time

# Initialize Pygame
pygame.init()

# Constants - smaller resolution for better performance
WIDTH, HEIGHT = 640, 480
HALF_HEIGHT = HEIGHT // 2
FOV = 60
HALF_FOV = FOV / 2
PLAYER_SIZE = 10
PLAYER_SPEED = 1.0  # Reduced to walking pace
MOUSE_SENSITIVITY = 0.2  # Mouse look sensitivity

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Set up display with hardware acceleration
flags = pygame.HWSURFACE | pygame.DOUBLEBUF
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Simple Fast Trippy Renderer")
clock = pygame.time.Clock()

# Create a more complex map with impossible spaces
MAP_SIZE = 16
MAP = np.zeros((MAP_SIZE, MAP_SIZE), dtype=np.int32)

# Fill the border with walls
MAP[0, :] = 1
MAP[MAP_SIZE-1, :] = 1
MAP[:, 0] = 1
MAP[:, MAP_SIZE-1] = 1

# Add some random walls
for _ in range(15):
    x = random.randint(2, MAP_SIZE-3)
    y = random.randint(2, MAP_SIZE-3)
    MAP[y, x] = 1

# Wall types:
# 0 = empty space
# 1 = normal wall
# 2 = portal entrance/exit
# 3 = non-Euclidean space entrance
# 4 = reality distortion wall
# 5 = perspective shift wall
# 6 = 4D hypercube entrance

# Add seamless portals (special walls that you can see through and walk between)
PORTALS = []
SEAMLESS_PORTALS = []
for _ in range(3):
    # Create portals that are not just single points but entire doorways
    # This allows for seamless walking through and seeing through
    
    # First, find two empty wall sections to place portals
    valid_placement = False
    attempts = 0
    
    while not valid_placement and attempts < 50:
        attempts += 1
        # Choose a random direction for the first portal (0=north, 1=east, 2=south, 3=west)
        dir1 = random.randint(0, 3)
        
        # Find a suitable wall section for the first portal
        if dir1 == 0:  # North wall
            x1 = random.randint(2, MAP_SIZE-3)
            y1 = 1  # Just inside the north wall
            facing1 = 0  # Facing north
        elif dir1 == 1:  # East wall
            x1 = MAP_SIZE-2  # Just inside the east wall
            y1 = random.randint(2, MAP_SIZE-3)
            facing1 = 1  # Facing east
        elif dir1 == 2:  # South wall
            x1 = random.randint(2, MAP_SIZE-3)
            y1 = MAP_SIZE-2  # Just inside the south wall
            facing1 = 2  # Facing south
        else:  # West wall
            x1 = 1  # Just inside the west wall
            y1 = random.randint(2, MAP_SIZE-3)
            facing1 = 3  # Facing west
        
        # Choose a different direction for the second portal
        dir2 = (dir1 + 2) % 4  # Opposite direction for interesting effect
        
        # Find a suitable wall section for the second portal
        if dir2 == 0:  # North wall
            x2 = random.randint(2, MAP_SIZE-3)
            y2 = 1  # Just inside the north wall
            facing2 = 0  # Facing north
        elif dir2 == 1:  # East wall
            x2 = MAP_SIZE-2  # Just inside the east wall
            y2 = random.randint(2, MAP_SIZE-3)
            facing2 = 1  # Facing east
        elif dir2 == 2:  # South wall
            x2 = random.randint(2, MAP_SIZE-3)
            y2 = MAP_SIZE-2  # Just inside the south wall
            facing2 = 2  # Facing south
        else:  # West wall
            x2 = 1  # Just inside the west wall
            y2 = random.randint(2, MAP_SIZE-3)
            facing2 = 3  # Facing west
        
        # Check if the locations are valid (not already used)
        if MAP[y1, x1] == 0 and MAP[y2, x2] == 0:
            valid_placement = True
    
    if valid_placement:
        # Store the portal information including position, facing direction, and linked portal
        portal1 = {'x': x1, 'y': y1, 'facing': facing1, 'linked_to': 1}
        portal2 = {'x': x2, 'y': y2, 'facing': facing2, 'linked_to': 0}
        SEAMLESS_PORTALS.append([portal1, portal2])
        
        # Mark portals with special values in the map
        MAP[y1, x1] = 2
        MAP[y2, x2] = 2
        
        # Also store the traditional portal data for compatibility
        PORTALS.append((x1, y1, x2, y2))

# Add non-Euclidean spaces (rooms bigger on the inside)
NON_EUCLIDEAN_SPACES = []
for _ in range(2):
    x, y = random.randint(2, MAP_SIZE-3), random.randint(2, MAP_SIZE-3)
    if MAP[y, x] == 0:
        # Create a non-Euclidean space entrance
        MAP[y, x] = 3
        
        # Define the inner space (bigger than it should be)
        inner_width = random.randint(5, 8)
        inner_height = random.randint(5, 8)
        inner_map = np.zeros((inner_height, inner_width), dtype=np.int32)
        
        # Add walls to the inner space
        inner_map[0, :] = 1
        inner_map[inner_height-1, :] = 1
        inner_map[:, 0] = 1
        inner_map[:, inner_width-1] = 1
        
        # Add some random features inside
        for _ in range(inner_width * inner_height // 4):
            ix = random.randint(1, inner_width-2)
            iy = random.randint(1, inner_height-2)
            inner_map[iy, ix] = random.choice([1, 4, 5])
        
        # Store the inner space
        NON_EUCLIDEAN_SPACES.append({
            'entrance': (x, y),
            'map': inner_map,
            'width': inner_width,
            'height': inner_height
        })

# Add 4D hypercube entrances - now with brain-breaking recursive maps
HYPERCUBES = []
for _ in range(2):
    x, y = random.randint(2, MAP_SIZE-3), random.randint(2, MAP_SIZE-3)
    if MAP[y, x] == 0:
        MAP[y, x] = 6  # Mark as hypercube entrance
        
        # Create a completely different map structure for each hypercube
        # This will be a recursive, impossible space that breaks the brain
        
        # First, create a larger outer map for the hypercube dimension
        outer_size = MAP_SIZE * 2  # Twice the size of the normal map
        outer_map = np.zeros((outer_size, outer_size), dtype=np.int32)
        
        # Create a fractal-like pattern in the outer map
        # This creates a space that seems to fold in on itself
        for ox in range(outer_size):
            for oy in range(outer_size):
                # Create fractal patterns that repeat at different scales
                if (ox % 8 == 0 or oy % 8 == 0) and random.random() < 0.7:
                    outer_map[oy, ox] = 1
                # Add some reality distortion walls
                elif (ox + oy) % 12 == 0 and random.random() < 0.5:
                    outer_map[oy, ox] = 4
                # Add perspective shift walls in a pattern
                elif (ox * oy) % 16 == 0 and random.random() < 0.4:
                    outer_map[oy, ox] = 5
        
        # Create recursive portals that lead to copies of the same space
        # but with slight alterations - truly impossible spaces
        recursive_portals = []
        for i in range(5):  # Create 5 recursive portals
            rx1 = random.randint(5, outer_size-6)
            ry1 = random.randint(5, outer_size-6)
            rx2 = random.randint(5, outer_size-6)
            ry2 = random.randint(5, outer_size-6)
            
            # Make sure we're not placing portals on walls
            if outer_map[ry1, rx1] == 0 and outer_map[ry2, rx2] == 0:
                # Mark the portal locations
                outer_map[ry1, rx1] = 10 + i  # Portal IDs start at 10
                outer_map[ry2, rx2] = 10 + i
                recursive_portals.append((rx1, ry1, rx2, ry2))
        
        # Create a series of interconnected rooms that form a hypercube topology
        rooms = []
        for i in range(16):  # 16 vertices for a tesseract (4D hypercube)
            # Each room is a section of the outer map
            section_size = 8
            start_x = (i % 4) * section_size
            start_y = (i // 4) * section_size
            
            # Extract a section of the outer map
            room_map = np.copy(outer_map[start_y:start_y+section_size, start_x:start_x+section_size])
            
            # Add connections based on hypercube topology
            # In a 4D hypercube, each vertex connects to vertices that differ by one bit
            connections = []
            for j in range(16):
                if bin(i ^ j).count('1') == 1:  # XOR to check if they differ by exactly one bit
                    connections.append(j)
                    # Add a special wall that marks the connection
                    edge_x = 0 if (j % 4) < (i % 4) else section_size-1
                    edge_y = 0 if (j // 4) < (i // 4) else section_size-1
                    # Only add if it's not already a portal
                    if room_map[edge_y, edge_x] < 10:
                        room_map[edge_y, edge_x] = 20 + j  # Connection IDs start at 20
            
            # Add some special features to each room
            # These will create unique visual and gameplay effects
            for _ in range(3):
                fx = random.randint(1, section_size-2)
                fy = random.randint(1, section_size-2)
                feature_type = random.choice([4, 5, 7, 8])  # Different special wall types
                if room_map[fy, fx] == 0:  # Only place on empty space
                    room_map[fy, fx] = feature_type
            
            # Store room data
            rooms.append({
                'map': room_map,
                'size': section_size,
                'connections': connections,
                'portals': recursive_portals,
                'position': (start_x, start_y),  # Position in the outer map
                'outer_map': outer_map  # Reference to the complete outer map
            })
        
        # Add a special central room that connects to all others
        central_map = np.zeros((8, 8), dtype=np.int32)
        # Add walls in a maze-like pattern
        for cx in range(8):
            for cy in range(8):
                if (cx + cy) % 3 == 0 and cx > 0 and cx < 7 and cy > 0 and cy < 7:
                    central_map[cy, cx] = 1
        
        # Add connections to all other rooms
        central_connections = list(range(16))
        
        # Add the central room
        rooms.append({
            'map': central_map,
            'size': 8,
            'connections': central_connections,
            'portals': recursive_portals,
            'position': (outer_size//2, outer_size//2),  # Center of the outer map
            'is_central': True
        })
        
        HYPERCUBES.append({
            'entrance': (x, y),
            'rooms': rooms,
            'outer_map': outer_map,
            'outer_size': outer_size,
            'recursive_portals': recursive_portals
        })

# Add reality distortion walls
for _ in range(5):
    x, y = random.randint(2, MAP_SIZE-3), random.randint(2, MAP_SIZE-3)
    if MAP[y, x] == 0:
        MAP[y, x] = 4  # Reality distortion wall

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

# Player state
player_state = {
    'in_normal_space': True,  # Whether player is in normal space or in a special space
    'current_space': None,     # Current special space the player is in
    'space_position': (0, 0),  # Position within the special space
    'gravity_direction': 0,    # Direction of gravity (0=down, 1=right, 2=up, 3=left)
    'reality_level': 1.0,      # How "real" the current space is (affects physics)
    'dimension': 3,            # Current dimension (3 for 3D, 4 for 4D)
    'hypercube_room': 0        # Current room in hypercube
}

# Pre-compute sin and cos tables for performance
SIN_TABLE = [math.sin(math.radians(i)) for i in range(360)]
COS_TABLE = [math.cos(math.radians(i)) for i in range(360)]

def fast_sin(angle):
    # Convert angle to degrees and get index in lookup table
    index = int(math.degrees(angle) % 360)
    return SIN_TABLE[index]

def fast_cos(angle):
    # Convert angle to degrees and get index in lookup table
    index = int(math.degrees(angle) % 360)
    return COS_TABLE[index]

# Advanced ray casting with impossible spaces
def advanced_raycast(player_x, player_y, player_angle):
    # Results
    wall_heights = [0] * WIDTH
    wall_colors = [(0, 0, 0)] * WIDTH
    wall_types = [0] * WIDTH
    wall_effects = [None] * WIDTH
    
    # Check if player is in a special space
    if not player_state['in_normal_space']:
        # Handle non-Euclidean space
        if player_state['current_space'] == 'non_euclidean':
            return raycast_non_euclidean(player_state['space_position'][0], player_state['space_position'][1], player_angle)
        # Handle hypercube
        elif player_state['current_space'] == 'hypercube':
            return raycast_hypercube(player_state['hypercube_room'], player_state['space_position'][0], player_state['space_position'][1], player_angle)
    
    # Cast a ray for each column of the screen
    for x in range(0, WIDTH, 1):  # Step by 1 for full resolution
        # Calculate ray angle
        ray_angle = (player_angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Apply reality distortion to ray angle
        if player_state['reality_level'] < 1.0:
            distortion = math.sin(time.time() * 3 + x * 0.05) * (1.0 - player_state['reality_level']) * 0.2
            ray_angle += distortion
        
        # Ray direction
        ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        
        # Apply gravity direction to ray
        if player_state['gravity_direction'] == 1:  # Right
            ray_dir_x, ray_dir_y = ray_dir_y, -ray_dir_x
        elif player_state['gravity_direction'] == 2:  # Up
            ray_dir_x, ray_dir_y = -ray_dir_x, -ray_dir_y
        elif player_state['gravity_direction'] == 3:  # Left
            ray_dir_x, ray_dir_y = -ray_dir_y, ray_dir_x
        
        # Current position
        ray_x = player_x
        ray_y = player_y
        
        # Distance traveled
        distance = 0.0
        hit_wall = False
        wall_type = 0
        special_effect = None
        portal_traversed = False  # Track if we've gone through a portal
        portal_distance = 0.0     # Distance at which we went through the portal
        linked_portal = None      # The portal we're linked to
        portal_offset_x = 0.0     # Offset to apply after portal traversal
        portal_offset_y = 0.0     # Offset to apply after portal traversal
        portal_rotation = 0.0     # Rotation to apply after portal traversal
        
        # Step size - larger for better performance
        step_size = 0.05
        
        # Cast the ray
        while not hit_wall and distance < 20:
            # Move the ray
            ray_x += ray_dir_x * step_size
            ray_y += ray_dir_y * step_size
            distance += step_size
            
            # Check if we hit a wall
            map_x = int(ray_x)
            map_y = int(ray_y)
            
            # Check for portals - if we're near a portal, check if we should go through it
            for portal_pair in SEAMLESS_PORTALS:
                for i, portal in enumerate(portal_pair):
                    # Check if we're close to this portal
                    portal_x, portal_y = portal['x'], portal['y']
                    portal_facing = portal['facing']
                    
                    # Calculate distance to portal center
                    dx = ray_x - portal_x
                    dy = ray_y - portal_y
                    dist_to_portal = math.sqrt(dx*dx + dy*dy)
                    
                    # If we're close to the portal and facing the right direction
                    if dist_to_portal < 0.5:
                        # Check if we're approaching from the right direction
                        # (opposite to the portal's facing direction)
                        approaching = False
                        if portal_facing == 0 and dy > 0:  # North-facing portal, approaching from south
                            approaching = True
                        elif portal_facing == 1 and dx < 0:  # East-facing portal, approaching from west
                            approaching = True
                        elif portal_facing == 2 and dy < 0:  # South-facing portal, approaching from north
                            approaching = True
                        elif portal_facing == 3 and dx > 0:  # West-facing portal, approaching from east
                            approaching = True
                        
                        # If we're approaching the portal and haven't gone through one yet
                        if approaching and not portal_traversed:
                            # We're going through the portal!
                            portal_traversed = True
                            portal_distance = distance
                            
                            # Get the linked portal
                            linked_idx = portal['linked_to']
                            linked_portal = portal_pair[linked_idx]
                            
                            # Calculate the offset to apply to the ray
                            portal_offset_x = linked_portal['x'] - portal_x
                            portal_offset_y = linked_portal['y'] - portal_y
                            
                            # Calculate rotation to apply (difference in facing directions)
                            portal_rotation = (linked_portal['facing'] - portal_facing) * math.pi/2
                            
                            # Apply the portal transformation
                            ray_x += portal_offset_x
                            ray_y += portal_offset_y
                            
                            # Apply rotation to ray direction if portals face different directions
                            if portal_rotation != 0:
                                old_dir_x = ray_dir_x
                                old_dir_y = ray_dir_y
                                ray_dir_x = old_dir_x * math.cos(portal_rotation) - old_dir_y * math.sin(portal_rotation)
                                ray_dir_y = old_dir_x * math.sin(portal_rotation) + old_dir_y * math.cos(portal_rotation)
            
            # Check if we're in bounds and hit a wall
            if 0 <= map_x < MAP_SIZE and 0 <= map_y < MAP_SIZE:
                wall_type = MAP[map_y, map_x]
                if wall_type > 0 and wall_type != 2:  # Not a portal
                    hit_wall = True
                    
                    # Special effects for different wall types
                    if wall_type == 3:  # Non-Euclidean space entrance
                        special_effect = 'non_euclidean_entrance'
                    elif wall_type == 4:  # Reality distortion wall
                        special_effect = 'reality_distortion'
                    elif wall_type == 5:  # Perspective shift wall
                        special_effect = 'perspective_shift'
                    elif wall_type == 6:  # 4D hypercube entrance
                        special_effect = 'hypercube_entrance'
        
        # Calculate wall height
        if hit_wall:
            # Apply fish-eye correction
            distance = distance * math.cos(ray_angle - player_angle)
            
            # Calculate wall height
            wall_height = min(HEIGHT, int((1.0 / distance) * HEIGHT * 0.5))
            
            # Apply perspective shifts for special walls
            if special_effect == 'perspective_shift':
                # Make the wall appear to shift in perspective
                shift = math.sin(time.time() * 2 + x * 0.1) * 0.3
                wall_height = int(wall_height * (1.0 + shift))
            
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color based on distance and type
            if wall_type == 1:  # Regular wall
                base_color = (200, 70, 60)  # Brick red
            elif wall_type == 2:  # Portal
                base_color = (0, 200, 200)  # Cyan
            elif wall_type == 3:  # Non-Euclidean space
                base_color = (200, 0, 200)  # Magenta
            elif wall_type == 4:  # Reality distortion
                base_color = (255, 150, 0)  # Orange
            elif wall_type == 5:  # Perspective shift
                base_color = (100, 255, 100)  # Light green
            elif wall_type == 6:  # 4D hypercube
                base_color = (150, 150, 255)  # Light blue
            else:
                base_color = (200, 200, 200)  # Gray
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / 20.0)
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply trippy color effect
            time_factor = time.time() * 2
            r = min(255, int(wall_color[0] * (1 + math.sin(time_factor + x * 0.1) * 0.2)))
            g = min(255, int(wall_color[1] * (1 + math.sin(time_factor + x * 0.05) * 0.2)))
            b = min(255, int(wall_color[2] * (1 + math.sin(time_factor + x * 0.02) * 0.2)))
            
            # Apply special color effects
            if special_effect == 'reality_distortion':
                # Reality distortion makes colors shift more dramatically
                r = (r + int(255 * math.sin(time_factor * 3 + x * 0.2))) // 2
                g = (g + int(255 * math.sin(time_factor * 2 + x * 0.1))) // 2
                b = (b + int(255 * math.sin(time_factor * 4 + x * 0.3))) // 2
            elif special_effect == 'hypercube_entrance':
                # Hypercube entrances have a shimmering 4D effect
                r = int(r * (0.7 + 0.3 * math.sin(time_factor * 5 + x * 0.3)))
                g = int(g * (0.7 + 0.3 * math.sin(time_factor * 6 + x * 0.2)))
                b = int(b * (0.7 + 0.3 * math.sin(time_factor * 7 + x * 0.1)))
            
            # Clamp colors
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            wall_colors[x] = (r, g, b)
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Raycasting for non-Euclidean spaces
def raycast_non_euclidean(pos_x, pos_y, angle):
    # Find which non-Euclidean space we're in
    current_space = None
    for space in NON_EUCLIDEAN_SPACES:
        if player_state['non_euclidean_map_id'] == space['entrance']:
            current_space = space
            break
    
    if not current_space:
        # Fallback to normal raycasting
        return advanced_raycast(player_x, player_y, player_angle)
    
    # Results
    wall_heights = [0] * WIDTH
    wall_colors = [(0, 0, 0)] * WIDTH
    wall_types = [0] * WIDTH
    wall_effects = [None] * WIDTH
    
    inner_map = current_space['map']
    inner_width = current_space['width']
    inner_height = current_space['height']
    
    # Cast rays in the inner space
    for x in range(WIDTH):
        # Calculate ray angle
        ray_angle = (angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Ray direction
        ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        
        # Apply non-Euclidean bending to ray direction
        # This creates the impossible space effect where angles don't add up to what they should
        bend_factor = math.sin(time.time() * 0.5 + x * 0.01) * 0.05
        temp_x = ray_dir_x
        ray_dir_x = ray_dir_x * math.cos(bend_factor) - ray_dir_y * math.sin(bend_factor)
        ray_dir_y = temp_x * math.sin(bend_factor) + ray_dir_y * math.cos(bend_factor)
        
        # Current position
        ray_x = pos_x
        ray_y = pos_y
        
        # Distance traveled
        distance = 0.0
        hit_wall = False
        wall_type = 0
        special_effect = None
        
        # Cast the ray
        while not hit_wall and distance < inner_width + inner_height:
            # Move the ray
            ray_x += ray_dir_x * 0.05
            ray_y += ray_dir_y * 0.05
            distance += 0.05
            
            # Check if we hit a wall in the inner space
            map_x = int(ray_x)
            map_y = int(ray_y)
            
            if 0 <= map_x < inner_width and 0 <= map_y < inner_height:
                wall_type = inner_map[map_y, map_x]
                if wall_type > 0:
                    hit_wall = True
                    
                    # Special effects for different wall types
                    if wall_type == 3:  # Exit back to normal space
                        special_effect = 'non_euclidean_exit'
                    elif wall_type == 4:  # Reality distortion wall
                        special_effect = 'reality_distortion'
                    elif wall_type == 5:  # Perspective shift wall
                        special_effect = 'perspective_shift'
            else:
                # Hit the boundary of the inner space, return to normal space
                hit_wall = True
                wall_type = 3  # Non-Euclidean space exit
                special_effect = 'non_euclidean_exit'
        
        # Calculate wall height
        if hit_wall:
            # Apply fish-eye correction
            distance = distance * math.cos(ray_angle - angle)
            
            # Calculate wall height
            wall_height = min(HEIGHT, int((1.0 / distance) * HEIGHT * 0.5))
            
            # Apply perspective shifts for special walls
            if special_effect == 'perspective_shift':
                # Make the wall appear to shift in perspective
                shift = math.sin(time.time() * 2 + x * 0.1) * 0.3
                wall_height = int(wall_height * (1.0 + shift))
            
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color based on distance and type
            if wall_type == 1:  # Regular wall
                base_color = (150, 50, 150)  # Purple for inner space walls
            elif wall_type == 3:  # Exit
                base_color = (200, 0, 200)  # Magenta
            elif wall_type == 4:  # Reality distortion
                base_color = (255, 150, 0)  # Orange
            elif wall_type == 5:  # Perspective shift
                base_color = (100, 255, 100)  # Light green
            else:
                base_color = (150, 150, 150)  # Gray
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / (inner_width + inner_height))
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply trippy color effect
            time_factor = time.time() * 2
            r = min(255, int(wall_color[0] * (1 + math.sin(time_factor + x * 0.1) * 0.2)))
            g = min(255, int(wall_color[1] * (1 + math.sin(time_factor + x * 0.05) * 0.2)))
            b = min(255, int(wall_color[2] * (1 + math.sin(time_factor + x * 0.02) * 0.2)))
            
            wall_colors[x] = (r, g, b)
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Raycasting for 4D hypercube spaces
def raycast_hypercube(room_id, pos_x, pos_y, angle):
    # Find the current hypercube
    current_cube = None
    for cube in HYPERCUBES:
        if player_state['current_hypercube_id'] == cube['entrance']:
            current_cube = cube
            break
    
    if not current_cube:
        # Fallback to normal raycasting
        return advanced_raycast(player_x, player_y, player_angle)
    
    # Get the current room in the hypercube
    current_room = current_cube['rooms'][room_id]
    room_map = current_room['map']
    room_size = current_room['size']
    
    # Results
    wall_heights = [0] * WIDTH
    wall_colors = [(0, 0, 0)] * WIDTH
    wall_types = [0] * WIDTH
    wall_effects = [None] * WIDTH
    
    # Get the 4D coordinates for this room
    is_central = current_room.get('is_central', False)
    if is_central:
        room_x, room_y = current_room['position']
    else:
        room_x, room_y = current_room['position']
    
    # Cast rays in the hypercube room
    for x in range(WIDTH):
        # Calculate ray angle
        ray_angle = (angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Ray direction
        ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        
        # Apply 4D rotation to ray direction based on w-coordinate
        # This creates the effect of the 4th dimension influencing the 3D projection
        w_coord = room_id / 16.0  # Normalize to 0-1 range
        w_effect = math.sin(w_coord * math.pi * 2 + time.time() * 0.5) * 0.1
        
        # Apply a more extreme distortion in the central room
        if is_central:
            # In the central room, rays bend based on distance from center
            center_x, center_y = room_size / 2, room_size / 2
            dist_from_center = math.sqrt((pos_x - center_x)**2 + (pos_y - center_y)**2)
            center_effect = 0.2 * math.sin(dist_from_center * 0.5 + time.time())
            w_effect += center_effect
        
        # Apply the 4D rotation
        temp_x = ray_dir_x
        ray_dir_x = ray_dir_x * math.cos(w_effect) - ray_dir_y * math.sin(w_effect)
        ray_dir_y = temp_x * math.sin(w_effect) + ray_dir_y * math.cos(w_effect)
        
        # Current position
        ray_x = pos_x
        ray_y = pos_y
        
        # Distance traveled
        distance = 0.0
        hit_wall = False
        wall_type = 0
        special_effect = None
        connection_id = -1
        portal_id = -1
        
        # Cast the ray
        max_distance = room_size * 3  # Allow for longer rays to see distant features
        while not hit_wall and distance < max_distance:
            # Move the ray
            ray_x += ray_dir_x * 0.05
            ray_y += ray_dir_y * 0.05
            distance += 0.05
            
            # Check if we hit a wall in the room
            map_x = int(ray_x)
            map_y = int(ray_y)
            
            if 0 <= map_x < room_size and 0 <= map_y < room_size:
                wall_type = room_map[map_y, map_x]
                if wall_type > 0:
                    hit_wall = True
                    
                    # Check for different wall types
                    if wall_type >= 20 and wall_type < 36:  # Connections to other rooms (20-35)
                        connection_id = wall_type - 20
                        # Check if this connection is valid in the hypercube topology
                        if connection_id in current_room['connections']:
                            special_effect = f'hypercube_connection_{connection_id}'
                    elif wall_type >= 10 and wall_type < 15:  # Recursive portals (10-14)
                        portal_id = wall_type - 10
                        special_effect = f'recursive_portal_{portal_id}'
                    elif wall_type == 6:  # Exit back to normal space
                        special_effect = 'hypercube_exit'
                    elif wall_type == 7:  # Reality fracture
                        special_effect = 'reality_fracture'
                    elif wall_type == 8:  # Dimensional shift
                        special_effect = 'dimensional_shift'
                    elif wall_type == 4:  # Reality distortion
                        special_effect = 'reality_distortion'
                    elif wall_type == 5:  # Perspective shift
                        special_effect = 'perspective_shift'
            else:
                # We've hit the boundary of the current room section
                # In our recursive space, we can see into other sections of the outer map
                
                # Calculate position in the outer map
                outer_x = room_x + map_x
                outer_y = room_y + map_y
                
                # Check if this position is within the outer map
                outer_size = current_cube['outer_size']
                if 0 <= outer_x < outer_size and 0 <= outer_y < outer_size:
                    # We can see into the outer map - truly impossible space
                    wall_type = current_cube['outer_map'][outer_y, outer_x]
                    if wall_type > 0:
                        hit_wall = True
                        special_effect = 'outer_map_view'
                else:
                    # Hit the boundary of the entire space
                    hit_wall = True
                    wall_type = 6  # Hypercube exit
                    special_effect = 'hypercube_exit'
        
        # Calculate wall height
        if hit_wall:
            # Apply fish-eye correction
            distance = distance * math.cos(ray_angle - angle)
            
            # Calculate wall height with 4D effect
            # The 4D effect makes walls appear to change height based on the 4th dimension
            w_height_effect = 1.0 + 0.3 * math.sin(w_coord * math.pi * 4 + time.time())
            
            # Add additional effects for special walls
            if special_effect == 'reality_fracture':
                # Reality fractures cause walls to appear to break apart
                fracture = math.sin(time.time() * 3 + x * 0.2) * 0.4
                w_height_effect *= (1.0 + fracture)
            elif special_effect == 'dimensional_shift':
                # Dimensional shifts cause walls to appear to shift between dimensions
                shift = math.sin(time.time() * 2 + distance * 0.5) * 0.5
                w_height_effect *= (1.0 + shift)
            elif special_effect == 'outer_map_view':
                # Seeing into the outer map creates a sense of vast space
                w_height_effect *= 0.7  # Make these walls appear further away
            
            wall_height = min(HEIGHT, int((1.0 / distance) * HEIGHT * 0.5 * w_height_effect))
            
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color based on distance, type, and 4D position
            if wall_type == 1:  # Regular wall
                # Color based on 4D coordinate
                r = 100 + int(w_coord * 100)
                g = 50 + int(math.sin(w_coord * math.pi * 2) * 50)
                b = 150 + int(math.cos(w_coord * math.pi * 2) * 50)
                base_color = (r, g, b)
            elif wall_type >= 20 and wall_type < 36:  # Connection to another room
                # Color based on connection ID
                hue = (wall_type - 20) / 16.0  # Normalize to 0-1
                r = int(150 + math.sin(hue * math.pi * 2) * 100)
                g = int(150 + math.sin(hue * math.pi * 2 + 2*math.pi/3) * 100)
                b = int(150 + math.sin(hue * math.pi * 2 + 4*math.pi/3) * 100)
                base_color = (r, g, b)
            elif wall_type >= 10 and wall_type < 15:  # Recursive portal
                # Portals have shifting rainbow colors
                portal_hue = (wall_type - 10) / 5.0 + time.time() * 0.2
                r = int(128 + 127 * math.sin(portal_hue * math.pi * 2))
                g = int(128 + 127 * math.sin(portal_hue * math.pi * 2 + 2*math.pi/3))
                b = int(128 + 127 * math.sin(portal_hue * math.pi * 2 + 4*math.pi/3))
                base_color = (r, g, b)
            elif wall_type == 6:  # Exit
                base_color = (150, 150, 255)  # Light blue
            elif wall_type == 7:  # Reality fracture
                # Reality fractures have unstable, glitchy colors
                t = time.time() * 5
                r = int(200 + 55 * math.sin(t + x * 0.1))
                g = int(100 + 100 * math.cos(t * 1.5))
                b = int(50 + 50 * math.sin(t * 0.7 + x * 0.2))
                base_color = (r, g, b)
            elif wall_type == 8:  # Dimensional shift
                # Dimensional shifts have colors that shift between dimensions
                t = time.time()
                r = int(100 + 100 * math.sin(t * 0.5))
                g = int(100 + 100 * math.sin(t * 0.5 + math.pi/2))
                b = int(100 + 100 * math.sin(t * 0.5 + math.pi))
                base_color = (r, g, b)
            elif wall_type == 4:  # Reality distortion
                base_color = (255, 150, 0)  # Orange
            elif wall_type == 5:  # Perspective shift
                base_color = (100, 255, 100)  # Light green
            else:
                # For walls in the outer map
                if special_effect == 'outer_map_view':
                    # These walls have a dreamlike quality
                    t = time.time() * 0.2
                    r = int(80 + 50 * math.sin(t + outer_x * 0.05))
                    g = int(80 + 50 * math.sin(t + outer_y * 0.05))
                    b = int(150 + 50 * math.sin(t + (outer_x + outer_y) * 0.05))
                    base_color = (r, g, b)
                else:
                    base_color = (150, 150, 150)  # Gray
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / max_distance)
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply 4D color shifting effect
            time_factor = time.time() * 2
            w_factor = math.sin(w_coord * math.pi * 4 + time_factor) * 0.3
            r = min(255, int(wall_color[0] * (1 + math.sin(time_factor + x * 0.1 + w_factor) * 0.3)))
            g = min(255, int(wall_color[1] * (1 + math.sin(time_factor + x * 0.05 + w_factor) * 0.3)))
            b = min(255, int(wall_color[2] * (1 + math.sin(time_factor + x * 0.02 + w_factor) * 0.3)))
            
            # Add extra effects for special wall types
            if special_effect == 'reality_fracture':
                # Add glitchy color artifacts
                if random.random() < 0.3:
                    r, g, b = b, r, g  # Color channel swapping
            elif special_effect == 'dimensional_shift':
                # Add color bleeding between dimensions
                bleed = 0.2 * math.sin(time.time() * 3 + x * 0.1)
                r = int(r * (1 + bleed))
                g = int(g * (1 - bleed))
                b = int(b * (1 + bleed * 0.5))
            
            wall_colors[x] = (min(255, r), min(255, g), min(255, b))
    
    return wall_heights, wall_colors, wall_types, wall_effects
    
    if not current_cube:
        # Fallback to normal raycasting
        return advanced_raycast(player_x, player_y, player_angle)
    
    # Get the current room
    room = current_cube['rooms'][room_id]
    room_map = room['map']
    room_size = room['size']
    
    # Results
    wall_heights = [0] * WIDTH
    wall_colors = [(0, 0, 0)] * WIDTH
    wall_types = [0] * WIDTH
    wall_effects = [None] * WIDTH
    
    # Cast rays in the hypercube room
    for x in range(0, WIDTH, 1):
        # Calculate ray angle
        ray_angle = (angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Ray direction
        ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        
        # Current position
        ray_x = pos_x
        ray_y = pos_y
        
        # Distance traveled
        distance = 0.0
        hit_wall = False
        wall_type = 0
        special_effect = None
        
        # Cast the ray
        while not hit_wall and distance < room_size * 2:
            # Move the ray
            ray_x += ray_dir_x * 0.05
            ray_y += ray_dir_y * 0.05
            distance += 0.05
            
            # Check if we hit a wall in the room
            map_x = int(ray_x)
            map_y = int(ray_y)
            
            if 0 <= map_x < room_size and 0 <= map_y < room_size:
                wall_type = room_map[map_y, map_x]
                if wall_type > 0:
                    hit_wall = True
                    
                    # Check if we hit a connection to another room
                    for conn_id in room['connections']:
                        # Place connections at specific positions in the room
                        conn_x = conn_id % room_size
                        conn_y = conn_id // room_size % room_size
                        
                        if map_x == conn_x and map_y == conn_y:
                            special_effect = f'hypercube_connection_{conn_id}'
            else:
                # Hit the boundary of the room
                hit_wall = True
                wall_type = 6  # Hypercube boundary
        
        # Calculate wall height
        if hit_wall:
            # Apply fish-eye correction
            distance = distance * math.cos(ray_angle - angle)
            
            # Calculate wall height
            wall_height = min(HEIGHT, int((1.0 / distance) * HEIGHT * 0.5))
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color
            if wall_type == 1:  # Regular wall
                # Use a color based on the 4D coordinates of the room
                r = 50 + ((room_id & 1) * 150)  # First bit affects red
                g = 50 + ((room_id & 2) * 75)   # Second bit affects green
                b = 50 + ((room_id & 4) * 50)   # Third bit affects blue
                base_color = (r, g, b)
            elif special_effect and special_effect.startswith('hypercube_connection'):
                # Connection to another room
                conn_id = int(special_effect.split('_')[-1])
                # Pulsing color based on connection ID
                pulse = (math.sin(time.time() * 3 + conn_id) + 1) / 2
                r = int(100 + pulse * 155)
                g = int(100 + (1-pulse) * 155)
                b = 255
                base_color = (r, g, b)
            elif wall_type == 6:  # Hypercube boundary
                base_color = (150, 150, 255)  # Light blue
            else:
                base_color = (150, 150, 150)  # Gray
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / (room_size * 2))
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply 4D visual effects
            time_factor = time.time() * 2
            w_coord = math.sin(time_factor + room_id * 0.5)  # Simulated 4th dimension
            
            # The 4th dimension affects the color mixing
            r = int(wall_color[0] * (0.7 + 0.3 * math.sin(w_coord + x * 0.01)))
            g = int(wall_color[1] * (0.7 + 0.3 * math.sin(w_coord + x * 0.02)))
            b = int(wall_color[2] * (0.7 + 0.3 * math.sin(w_coord + x * 0.03)))
            
            # Clamp colors
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            wall_colors[x] = (r, g, b)
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Render a frame
def render_frame(player_x, player_y, player_angle, distortion_level=0.0):
    # Get wall heights, colors, types, and effects
    wall_heights, wall_colors, wall_types, wall_effects = advanced_raycast(player_x, player_y, player_angle)
    
    # Clear the screen
    screen.fill(BLACK)
    
    # Draw sky based on current space and reality level
    if player_state['in_normal_space']:
        # Normal space sky
        if player_state['reality_level'] < 1.0:
            # Distorted reality sky
            for y in range(HALF_HEIGHT):
                t = y / HALF_HEIGHT
                r = int(50 * (1 - t) + 100 * t * player_state['reality_level'])
                g = int(50 * (1 - t) + 150 * t * player_state['reality_level'])
                b = int(100 * (1 - t) + 200 * t)
                # Add wavy distortion
                wave = math.sin(y * 0.1 + time.time() * 2) * (1.0 - player_state['reality_level']) * 20
                pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y + int(wave)))
        else:
            # Normal sky
            pygame.draw.rect(screen, (0, 100, 200), (0, 0, WIDTH, HALF_HEIGHT))
    elif player_state['current_space'] == 'non_euclidean':
        # Non-Euclidean space sky (purple gradient)
        for y in range(HALF_HEIGHT):
            t = y / HALF_HEIGHT
            r = int(50 * (1 - t) + 100 * t)
            g = int(0 * (1 - t) + 50 * t)
            b = int(100 * (1 - t) + 200 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    elif player_state['current_space'] == 'hypercube':
        # 4D hypercube sky (shifting based on 4D coordinates)
        room_id = player_state['hypercube_room']
        for y in range(HALF_HEIGHT):
            t = y / HALF_HEIGHT
            # Use the room ID to affect the sky color
            r = int(50 * (1 - t) + ((room_id & 1) * 150 + 50) * t)
            g = int(50 * (1 - t) + ((room_id & 2) * 75 + 50) * t)
            b = int(100 * (1 - t) + ((room_id & 4) * 50 + 150) * t)
            # Add 4D ripple effect
            w_coord = math.sin(time.time() + room_id * 0.5)  # Simulated 4th dimension
            ripple = math.sin(y * 0.1 + w_coord) * 10
            pygame.draw.line(screen, (r, g, b), (int(ripple), y), (WIDTH + int(ripple), y))
    
    # Draw floor based on current space and gravity direction
    if player_state['gravity_direction'] == 0:  # Normal down gravity
        if player_state['in_normal_space']:
            # Normal space floor
            if player_state['reality_level'] < 1.0:
                # Distorted reality floor
                for y in range(HALF_HEIGHT, HEIGHT):
                    t = (y - HALF_HEIGHT) / HALF_HEIGHT
                    r = int(50 * (1 - t) + 70 * t)
                    g = int(50 * (1 - t) + 70 * t)
                    b = int(50 * (1 - t) + 70 * t)
                    # Add checkerboard pattern that shifts with reality level
                    checker_size = int(10 + (1.0 - player_state['reality_level']) * 20)
                    if ((y // checker_size) + (int(time.time() * 5) // checker_size)) % 2 == 0:
                        r, g, b = r//2, g//2, b//2
                    pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
            else:
                # Normal floor
                pygame.draw.rect(screen, (50, 50, 50), (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))
        else:
            # Special space floor
            pygame.draw.rect(screen, (30, 30, 50), (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))
    else:
        # Gravity is in a different direction - draw a grid pattern
        grid_size = 20
        for x in range(0, WIDTH, grid_size):
            for y in range(HALF_HEIGHT, HEIGHT, grid_size):
                if (x // grid_size + y // grid_size) % 2 == 0:
                    pygame.draw.rect(screen, (40, 40, 40), (x, y, grid_size, grid_size))
                else:
                    pygame.draw.rect(screen, (60, 60, 60), (x, y, grid_size, grid_size))
    
    # Draw walls with special effects
    for x in range(WIDTH):
        if wall_heights[x] > 0:
            # Calculate wall position
            wall_top = HALF_HEIGHT - wall_heights[x] // 2
            wall_bottom = HALF_HEIGHT + wall_heights[x] // 2
            
            # Apply distortion effects
            if distortion_level > 0:
                # Basic wave distortion
                wave_distortion = math.sin(x * 0.05 + time.time() * 2) * distortion_level * 10
                wall_top += int(wave_distortion)
                wall_bottom += int(wave_distortion)
                
                # Apply special effects based on wall type
                if wall_effects[x] == 'non_euclidean_entrance':
                    # Non-Euclidean entrances warp and pulse
                    pulse = math.sin(time.time() * 3) * 5
                    wall_top -= int(pulse)
                    wall_bottom += int(pulse)
                elif wall_effects[x] == 'reality_distortion':
                    # Reality distortion walls shimmer and bend
                    shimmer = math.sin(x * 0.2 + time.time() * 5) * 8
                    wall_top += int(shimmer)
                    wall_bottom -= int(shimmer)
                elif wall_effects[x] == 'perspective_shift':
                    # Perspective shift walls change apparent height
                    shift = math.sin(time.time() * 2) * 0.3
                    height = wall_bottom - wall_top
                    new_height = int(height * (1.0 + shift))
                    wall_top = HALF_HEIGHT - new_height // 2
                    wall_bottom = HALF_HEIGHT + new_height // 2
                elif wall_effects[x] == 'hypercube_entrance':
                    # Hypercube entrances have a 4D visual effect
                    w_effect = math.sin(time.time() * 4 + x * 0.1) * 10
                    wall_top = int(wall_top + w_effect * math.sin(x * 0.05))
                    wall_bottom = int(wall_bottom - w_effect * math.sin(x * 0.05))
                elif wall_effects[x] and wall_effects[x].startswith('hypercube_connection'):
                    # Connections between hypercube rooms pulse
                    conn_id = int(wall_effects[x].split('_')[-1])
                    pulse = math.sin(time.time() * 3 + conn_id) * 8
                    wall_top -= int(pulse)
                    wall_bottom += int(pulse)
            
            # Draw wall slice with special rendering based on wall type
            if wall_types[x] == 6:  # Hypercube walls have a 4D shimmer effect
                # Draw multiple lines with slight offsets for a shimmering effect
                for i in range(3):
                    offset = math.sin(time.time() * (i+1) * 2 + x * 0.1) * 2
                    color = wall_colors[x]
                    # Adjust color for each layer
                    r, g, b = color
                    r = min(255, r + i * 20)
                    g = min(255, g + i * 10)
                    b = min(255, b + i * 30)
                    pygame.draw.line(screen, (r, g, b), (x, int(wall_top + offset)), (x, int(wall_bottom + offset)), 1)
            elif wall_types[x] == 4:  # Reality distortion walls
                # Draw with a glitchy effect
                for i in range(3):
                    if random.random() < 0.7:  # 70% chance to draw each segment
                        segment_height = (wall_bottom - wall_top) // 3
                        start_y = wall_top + i * segment_height
                        end_y = start_y + segment_height
                        # Randomly offset the segments horizontally
                        offset = random.randint(-2, 2)
                        pygame.draw.line(screen, wall_colors[x], (x + offset, start_y), (x + offset, end_y), 1)
            else:  # Normal walls
                pygame.draw.line(screen, wall_colors[x], (x, wall_top), (x, wall_bottom), 1)
    
    # Draw minimap
    minimap_size = 100
    minimap_scale = minimap_size / MAP_SIZE
    
    # Draw background
    pygame.draw.rect(screen, (0, 0, 0, 128), (10, 10, minimap_size, minimap_size))
    
    # Draw walls
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            if MAP[y, x] == 1:  # Wall
                pygame.draw.rect(
                    screen, WHITE,
                    (10 + x * minimap_scale, 10 + y * minimap_scale, minimap_scale, minimap_scale)
                )
            elif MAP[y, x] == 2:  # Portal
                pygame.draw.rect(
                    screen, (0, 255, 255),
                    (10 + x * minimap_scale, 10 + y * minimap_scale, minimap_scale, minimap_scale)
                )
    
    # Draw player
    pygame.draw.circle(
        screen, GREEN,
        (10 + int(player_x * minimap_scale), 10 + int(player_y * minimap_scale)),
        int(3)
    )
    
    # Draw player direction
    end_x = player_x + fast_cos(player_angle) * 0.5
    end_y = player_y + fast_sin(player_angle) * 0.5
    pygame.draw.line(
        screen, GREEN,
        (10 + int(player_x * minimap_scale), 10 + int(player_y * minimap_scale)),
        (10 + int(end_x * minimap_scale), 10 + int(end_y * minimap_scale)),
        1
    )
def main():
    global MAP
    
    # Player position and angle
    player_x = 8.0
    player_y = 8.0
    player_angle = 0.0
    
    # Movement flags
    moving_forward = False
    moving_backward = False
    moving_left = False
    moving_right = False
    
    # Distortion settings
    distortion_enabled = True
    distortion_level = 0.5
    
    # Mouse lock for FPS controls - enabled by default
    mouse_locked = True
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    # FPS counter
    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    
    # Initialize player state
    player_state['in_normal_space'] = True
    player_state['current_space'] = 'normal'
    player_state['space_position'] = [0, 0]
    player_state['reality_level'] = 1.0
    player_state['gravity_direction'] = 0  # 0=down, 1=right, 2=up, 3=left
    player_state['non_euclidean_map_id'] = None
    player_state['non_euclidean_center'] = [0, 0]
    player_state['current_hypercube_id'] = None
    player_state['hypercube_room'] = 0
    
    # Create maps for non-Euclidean spaces
    NON_EUCLIDEAN_MAPS = {}
    for space in NON_EUCLIDEAN_SPACES:
        NON_EUCLIDEAN_MAPS[space['entrance']] = space['map']
    
    # Create maps for hypercube rooms
    HYPERCUBE_MAPS = {}
    for cube in HYPERCUBES:
        for i, room in enumerate(cube['rooms']):
            HYPERCUBE_MAPS[i] = room['map']
    
    # Reality distortion effect timer
    reality_distortion_timer = 0
    
    # Main loop
    running = True
    while running:
        # Get delta time
        current_time = time.time()
        dt = min(current_time - fps_timer, 0.1)  # Cap to avoid huge jumps
        
        # Process events
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
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    distortion_level = min(1.0, distortion_level + 0.1)
                elif event.key == pygame.K_MINUS:
                    distortion_level = max(0.0, distortion_level - 0.1)
                elif event.key == pygame.K_m:
                    # Toggle mouse lock
                    mouse_locked = not mouse_locked
                    pygame.mouse.set_visible(not mouse_locked)
                    pygame.event.set_grab(mouse_locked)
                elif event.key == pygame.K_r:
                    # Toggle reality level (for testing)
                    player_state['reality_level'] = 1.0 if player_state['reality_level'] < 1.0 else 0.5
                elif event.key == pygame.K_g:
                    # Change gravity direction (for testing)
                    player_state['gravity_direction'] = (player_state['gravity_direction'] + 1) % 4
            
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
                # Adjust player angle based on mouse movement with the new sensitivity
                player_angle += math.radians(event.rel[0] * MOUSE_SENSITIVITY)
        
        # Calculate movement based on current space and gravity
        move_speed = PLAYER_SPEED * dt
        dx, dy = 0, 0
        
        # Adjust movement direction based on gravity
        if player_state['gravity_direction'] == 0:  # Normal down gravity
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
        elif player_state['gravity_direction'] == 1:  # Right gravity
            if moving_forward:
                dx += fast_cos(player_angle - math.pi/2) * move_speed
                dy += fast_sin(player_angle - math.pi/2) * move_speed
            if moving_backward:
                dx += fast_cos(player_angle + math.pi/2) * move_speed
                dy += fast_sin(player_angle + math.pi/2) * move_speed
            if moving_left:
                dx -= fast_cos(player_angle) * move_speed
                dy -= fast_sin(player_angle) * move_speed
            if moving_right:
                dx += fast_cos(player_angle) * move_speed
                dy += fast_sin(player_angle) * move_speed
        elif player_state['gravity_direction'] == 2:  # Up gravity
            if moving_forward:
                dx -= fast_cos(player_angle) * move_speed
                dy -= fast_sin(player_angle) * move_speed
            if moving_backward:
                dx += fast_cos(player_angle) * move_speed
                dy += fast_sin(player_angle) * move_speed
            if moving_left:
                dx -= fast_cos(player_angle + math.pi/2) * move_speed
                dy -= fast_sin(player_angle + math.pi/2) * move_speed
            if moving_right:
                dx -= fast_cos(player_angle - math.pi/2) * move_speed
                dy -= fast_sin(player_angle - math.pi/2) * move_speed
        elif player_state['gravity_direction'] == 3:  # Left gravity
            if moving_forward:
                dx += fast_cos(player_angle + math.pi/2) * move_speed
                dy += fast_sin(player_angle + math.pi/2) * move_speed
            if moving_backward:
                dx += fast_cos(player_angle - math.pi/2) * move_speed
                dy += fast_sin(player_angle - math.pi/2) * move_speed
            if moving_left:
                dx += fast_cos(player_angle) * move_speed
                dy += fast_sin(player_angle) * move_speed
            if moving_right:
                dx -= fast_cos(player_angle) * move_speed
                dy -= fast_sin(player_angle) * move_speed
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx = dx / length * move_speed
            dy = dy / length * move_speed
        
        # Apply movement based on current space
        if player_state['in_normal_space']:
            # Normal space movement
            new_x = player_x + dx
            new_y = player_y + dy
            
            # Check for seamless portals - allow walking through them
            portal_found = False  # Flag to track if we found a portal to go through
            
            for portal_pair in SEAMLESS_PORTALS:
                if portal_found:
                    break  # Skip remaining portal checks if we already found one
                    
                for i, portal in enumerate(portal_pair):
                    portal_x, portal_y = portal['x'], portal['y']
                    portal_facing = portal['facing']
                    
                    # Calculate distance to portal center
                    dx = new_x - portal_x
                    dy = new_y - portal_y
                    dist_to_portal = math.sqrt(dx*dx + dy*dy)
                    
                    # If we're close to the portal and about to walk through it
                    if dist_to_portal < 0.5:
                        # Check if we're approaching from the right direction
                        approaching = False
                        if portal_facing == 0 and dy > 0:  # North-facing portal, approaching from south
                            approaching = True
                        elif portal_facing == 1 and dx < 0:  # East-facing portal, approaching from west
                            approaching = True
                        elif portal_facing == 2 and dy < 0:  # South-facing portal, approaching from north
                            approaching = True
                        elif portal_facing == 3 and dx > 0:  # West-facing portal, approaching from east
                            approaching = True
                        
                        # If we're approaching the portal
                        if approaching:
                            portal_found = True  # Mark that we found a portal
                            
                            # Get the linked portal
                            linked_idx = portal['linked_to']
                            linked_portal = portal_pair[linked_idx]
                            
                            # Calculate the offset to apply to the position
                            offset_x = linked_portal['x'] - portal_x
                            offset_y = linked_portal['y'] - portal_y
                            
                            # Calculate rotation to apply (difference in facing directions)
                            rotation = (linked_portal['facing'] - portal_facing) * math.pi/2
                            
                            # Apply the portal transformation to position
                            new_x += offset_x
                            new_y += offset_y
                            
                            # Apply rotation to movement direction if portals face different directions
                            if rotation != 0:
                                # Calculate the vector from portal to player's new position
                                rel_x = new_x - linked_portal['x']
                                rel_y = new_y - linked_portal['y']
                                
                                # Rotate this vector
                                rot_x = rel_x * math.cos(rotation) - rel_y * math.sin(rotation)
                                rot_y = rel_x * math.sin(rotation) + rel_y * math.cos(rotation)
                                
                                # Apply the rotated vector to get the new position
                                new_x = linked_portal['x'] + rot_x
                                new_y = linked_portal['y'] + rot_y
                                
                                # Also rotate the player's viewing angle
                                player_angle += rotation
                            
                            # Apply a subtle reality distortion effect when walking through portals
                            reality_distortion_timer = current_time
                            player_state['reality_level'] = max(0.8, player_state['reality_level'] - 0.05)
                            break  # Stop checking other portals in this pair
            
            # Check for non-Euclidean space entrances
            if 0 <= int(new_x) < MAP_SIZE and 0 <= int(new_y) < MAP_SIZE:
                wall_type = MAP[int(new_y), int(new_x)]
                if wall_type == 3:  # Non-Euclidean space entrance
                    # Enter non-Euclidean space
                    player_state['in_normal_space'] = False
                    player_state['current_space'] = 'non_euclidean'
                    player_state['non_euclidean_map_id'] = (int(new_x), int(new_y))
                    player_state['space_position'] = [2.0, 2.0]  # Start position in inner space
                    player_state['non_euclidean_center'] = [new_x, new_y]
                    continue  # Skip collision check
                elif wall_type == 4:  # Reality distortion wall
                    # Distort reality when near these walls
                    reality_distortion_timer = current_time
                    player_state['reality_level'] = max(0.3, player_state['reality_level'] - 0.1)
                elif wall_type == 5:  # Perspective shift wall
                    # Change gravity direction when hitting these walls
                    player_state['gravity_direction'] = (player_state['gravity_direction'] + 1) % 4
                elif wall_type == 6:  # 4D hypercube entrance
                    # Enter hypercube
                    player_state['in_normal_space'] = False
                    player_state['current_space'] = 'hypercube'
                    player_state['current_hypercube_id'] = (int(new_x), int(new_y))
                    player_state['hypercube_room'] = 0  # Start in first room
                    player_state['space_position'] = [2.0, 2.0]  # Start position in hypercube
                    continue  # Skip collision check
            
            # Check for collisions in normal space
            if 0 <= int(new_x) < MAP_SIZE and 0 <= int(new_y) < MAP_SIZE:
                if MAP[int(new_y), int(player_x)] != 1:  # Not a wall
                    player_y = new_y
                if MAP[int(player_y), int(new_x)] != 1:  # Not a wall
                    player_x = new_x
        else:
            # Movement in special spaces
            new_x = player_state['space_position'][0] + dx
            new_y = player_state['space_position'][1] + dy
            
            if player_state['current_space'] == 'non_euclidean':
                # Get the current non-Euclidean space
                for space in NON_EUCLIDEAN_SPACES:
                    if player_state['non_euclidean_map_id'] == space['entrance']:
                        current_space = space
                        break
                
                inner_map = current_space['map']
                inner_width = current_space['width']
                inner_height = current_space['height']
                
                # Check for exits back to normal space
                if int(new_x) < 0 or int(new_x) >= inner_width or int(new_y) < 0 or int(new_y) >= inner_height:
                    # Exit back to normal space
                    player_state['in_normal_space'] = True
                    player_state['current_space'] = 'normal'
                    player_x, player_y = player_state['non_euclidean_center']
                    player_x += 1.0  # Move slightly away from entrance
                    continue  # Skip collision check
                
                # Check for collisions in non-Euclidean space
                if 0 <= int(new_x) < inner_width and 0 <= int(new_y) < inner_height:
                    wall_type = inner_map[int(new_y), int(new_x)]
                    if wall_type == 0:  # Empty space
                        player_state['space_position'] = [new_x, new_y]
                    elif wall_type == 3:  # Exit back to normal space
                        player_state['in_normal_space'] = True
                        player_state['current_space'] = 'normal'
                        player_x, player_y = player_state['non_euclidean_center']
                        player_x += 1.0  # Move slightly away from entrance
            
            elif player_state['current_space'] == 'hypercube':
                # Get the current hypercube
                for cube in HYPERCUBES:
                    if player_state['current_hypercube_id'] == cube['entrance']:
                        current_cube = cube
                        break
                
                current_room = current_cube['rooms'][player_state['hypercube_room']]
                room_map = current_room['map']
                room_size = current_room['size']
                
                # Check for exits back to normal space
                if int(new_x) < 0 or int(new_x) >= room_size or int(new_y) < 0 or int(new_y) >= room_size:
                    # Exit back to normal space
                    player_state['in_normal_space'] = True
                    player_state['current_space'] = 'normal'
                    player_x, player_y = player_state['current_hypercube_id']
                    player_y += 1.0  # Move slightly away from entrance
                    continue  # Skip collision check
                
                # Check for collisions and connections in hypercube
                if 0 <= int(new_x) < room_size and 0 <= int(new_y) < room_size:
                    wall_type = room_map[int(new_y), int(new_x)]
                    if wall_type == 0:  # Empty space
                        player_state['space_position'] = [new_x, new_y]
                    elif wall_type == 6:  # Exit back to normal space
                        player_state['in_normal_space'] = True
                        player_state['current_space'] = 'normal'
                        player_x, player_y = player_state['current_hypercube_id']
                        player_y += 1.0  # Move slightly away from entrance
                    elif wall_type >= 20 and wall_type < 36:  # Connection to another room (20-35)
                        connection_id = wall_type - 20
                        if connection_id in current_room['connections']:
                            # Move to connected room
                            new_room_id = current_room['connections'][current_room['connections'].index(connection_id)]
                            player_state['hypercube_room'] = new_room_id
                            # Position in new room (opposite side)
                            if new_x < 1:
                                player_state['space_position'] = [room_size - 1.5, new_y]
                            elif new_x > room_size - 1:
                                player_state['space_position'] = [1.5, new_y]
                            elif new_y < 1:
                                player_state['space_position'] = [new_x, room_size - 1.5]
                            elif new_y > room_size - 1:
                                player_state['space_position'] = [new_x, 1.5]
                    elif wall_type >= 10 and wall_type < 15:  # Recursive portal (10-14)
                        # These are the brain-breaking recursive portals
                        portal_id = wall_type - 10
                        
                        # Find the matching portal in the current room's portal list
                        for rx1, ry1, rx2, ry2 in current_room['portals']:
                            if (int(new_x) == rx1 and int(new_y) == ry1) or (int(new_x) == rx2 and int(new_y) == ry2):
                                # Found the portal - teleport to the other end
                                if int(new_x) == rx1 and int(new_y) == ry1:
                                    # Teleport to the second portal
                                    new_pos_x, new_pos_y = rx2 + 0.5, ry2 + 0.5
                                else:
                                    # Teleport to the first portal
                                    new_pos_x, new_pos_y = rx1 + 0.5, ry1 + 0.5
                                
                                # Apply a reality distortion effect when using portals
                                reality_distortion_timer = current_time
                                player_state['reality_level'] = max(0.3, player_state['reality_level'] - 0.2)
                                
                                # Randomly decide if we should change rooms for a truly mind-bending effect
                                if random.random() < 0.3 and len(current_cube['rooms']) > 1:
                                    # 30% chance to jump to a random room while using a portal
                                    # This creates impossible connections that shouldn't exist
                                    new_room = random.randint(0, len(current_cube['rooms']) - 1)
                                    if new_room != player_state['hypercube_room']:
                                        player_state['hypercube_room'] = new_room
                                        # The portal leads to the same coordinates but in a different room
                                        # This is physically impossible and breaks the brain
                                
                                # Set the new position
                                player_state['space_position'] = [new_pos_x, new_pos_y]
                                break
                    elif wall_type == 7:  # Reality fracture
                        # Reality fractures cause severe reality distortion
                        reality_distortion_timer = current_time
                        player_state['reality_level'] = max(0.1, player_state['reality_level'] - 0.3)
                        
                        # Allow movement through the fracture
                        player_state['space_position'] = [new_x, new_y]
                        
                        # Small chance to teleport to a random location in the current room
                        if random.random() < 0.1:
                            player_state['space_position'] = [
                                random.uniform(1, room_size - 1),
                                random.uniform(1, room_size - 1)
                            ]
                    elif wall_type == 8:  # Dimensional shift
                        # Dimensional shifts change gravity direction
                        player_state['gravity_direction'] = (player_state['gravity_direction'] + 1) % 4
                        
                        # Allow movement through the shift
                        player_state['space_position'] = [new_x, new_y]
                        
                        # Small chance to move to the central room if it exists
                        if random.random() < 0.2:
                            for i, room in enumerate(current_cube['rooms']):
                                if room.get('is_central', False):
                                    player_state['hypercube_room'] = i
                                    player_state['space_position'] = [room['size'] / 2, room['size'] / 2]
                                    break
        
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
        
        # Gradually restore reality level
        if current_time - reality_distortion_timer > 5.0 and player_state['reality_level'] < 1.0:
            player_state['reality_level'] = min(1.0, player_state['reality_level'] + 0.01 * dt)
        
        # Render the frame
        current_distortion = distortion_level if distortion_enabled else 0.0
        if player_state['in_normal_space']:
            render_frame(player_x, player_y, player_angle, current_distortion)
        else:
            render_frame(player_state['space_position'][0], player_state['space_position'][1], player_angle, current_distortion)
        
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
        
        # Display game state
        if player_state['in_normal_space']:
            space_text = "Normal Space"
        elif player_state['current_space'] == 'non_euclidean':
            space_text = "Non-Euclidean Space"
        elif player_state['current_space'] == 'hypercube':
            space_text = f"4D Hypercube Room {player_state['hypercube_room']}"
        
        status_text = f"{space_text} | Reality: {player_state['reality_level']:.1f} | Gravity: {['Down', 'Right', 'Up', 'Left'][player_state['gravity_direction']]}"
        text_surface = font.render(status_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        # Display controls
        controls_text = f"Distortion: {'ON' if distortion_enabled else 'OFF'} (SPACE) | Level: {distortion_level:.1f} (+/-) | R: Toggle Reality | G: Change Gravity"
        text_surface = font.render(controls_text, True, WHITE)
        screen.blit(text_surface, (10, HEIGHT - 30))
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(144)
    
    pygame.quit()

if __name__ == "__main__":
    main()
