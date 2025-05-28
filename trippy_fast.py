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
PLAYER_SPEED = 1.0  # Walking pace
MOUSE_SENSITIVITY = 0.2

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Trippy Raycaster - Optimized')

# Set up the clock
clock = pygame.time.Clock()

# Initialize font
font = pygame.font.SysFont('Arial', 18)

# Player state dictionary to track various conditions
player_state = {
    'in_normal_space': True,
    'current_space': None,
    'space_position': [0, 0],
    'non_euclidean_map_id': None,
    'hypercube_room': 0,
    'current_hypercube_id': None,
    'reality_level': 1.0,
    'gravity_direction': 0,  # 0: down, 1: right, 2: up, 3: left
    'show_map': True
}

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Create a map with impossible spaces
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
# 2 = portal
# 3 = non-Euclidean space entrance
# 4 = reality distortion wall
# 5 = perspective shift wall
# 6 = 4D hypercube entrance
# 7 = reality fracture
# 8 = dimensional shift
# 9 = recursive boundary
# 10 = recursive portal
# 11 = mirror wall

# Define non-Euclidean spaces with emergent gameplay mechanics
NON_EUCLIDEAN_SPACES = [
    {
        'entrance': 1,  # Map ID for the entrance
        'exit_pos': [8, 8],  # Exit position in the normal map
        'width': 10,
        'height': 10,
        'map': np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 4, 4, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 5, 0, 11, 11, 0, 5, 0, 1],
            [1, 0, 5, 0, 11, 11, 0, 5, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 4, 4, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 3, 1],  # Exit at [8, 8]
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]),
        'mechanics': {
            'reality_bleed': 0.8,  # Reality level gradually decreases to this value
            'time_dilation': 1.2,  # Time moves slightly faster here
            'perspective_inversion': True  # Occasional perspective inversions
        }
    },
    {
        'entrance': 2,  # Map ID for the entrance
        'exit_pos': [15, 8],  # Exit position in the normal map
        'width': 15,
        'height': 15,
        'map': np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 9, 9, 9, 9, 9, 9, 9, 0, 1, 0, 1],
            [1, 0, 0, 0, 9, 0, 0, 0, 0, 0, 9, 0, 0, 0, 1],
            [1, 0, 1, 0, 9, 0, 10, 10, 10, 0, 9, 0, 1, 0, 1],
            [1, 0, 1, 0, 9, 0, 10, 0, 10, 0, 9, 0, 1, 0, 1],
            [1, 0, 1, 0, 9, 0, 10, 10, 10, 0, 9, 0, 1, 0, 1],
            [1, 0, 0, 0, 9, 0, 0, 0, 0, 0, 9, 0, 0, 0, 1],
            [1, 0, 1, 0, 9, 9, 9, 9, 9, 9, 9, 0, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],  # Exit at [13, 13]
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]),
        'mechanics': {
            'reality_bleed': 0.6,  # Reality level decreases more here
            'recursive_scaling': True,  # Enable recursive scaling
            'gravity_flux': True  # Gravity changes based on position
        },
        'recursive_rooms': [
            {'x': 6, 'y': 6, 'size': 3, 'scale': 0.5},  # Central recursive room
            {'x': 4, 'y': 4, 'size': 7, 'scale': 0.8}   # Larger outer recursive room
        ]
    },
    {
        'entrance': 3,  # Map ID for the entrance
        'exit_pos': [5, 15],  # Exit position in the normal map
        'width': 20,
        'height': 20,
        'map': np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 10, 10, 10, 10, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 0, 0, 0, 0, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 0, 5, 5, 0, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 0, 5, 5, 0, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 0, 0, 0, 0, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 10, 10, 10, 10, 10, 10, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # Exit at [9, 18]
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]),
        'mechanics': {
            'reality_bleed': 0.5,  # Reality level decreases significantly
            'recursive_scaling': True,  # Enable recursive scaling
            'time_dilation': 0.7,  # Time moves slower here
            'perspective_inversion': True,  # Enable perspective inversion
            'gravity_flux': True  # Gravity changes based on position
        },
        'recursive_rooms': [
            {'x': 6, 'y': 6, 'size': 6, 'scale': 0.6},  # Central recursive room
            {'x': 8, 'y': 8, 'size': 2, 'scale': 0.3}   # Small inner recursive room
        ],
        'mirror_dimension': True  # This is a mirror dimension
    },
    {
        'entrance': 4,  # Map ID for the entrance
        'exit_pos': [18, 18],  # Exit position in the normal map
        'width': 25,
        'height': 25,
        'map': np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 9, 9, 9, 9, 9, 9, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 4, 4, 4, 4, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 10, 10, 10, 10, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 10, 5, 5, 10, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 10, 5, 5, 10, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 10, 10, 10, 10, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 4, 4, 4, 4, 4, 4, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 9, 9, 9, 9, 9, 9, 9, 9, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # Exit at [12, 23]
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]),
        'mechanics': {
            'reality_bleed': 0.3,  # Reality level decreases dramatically
            'recursive_scaling': True,  # Enable recursive scaling
            'time_dilation': 0.5,  # Time moves very slowly here
            'perspective_inversion': True,  # Enable perspective inversion
            'gravity_flux': True  # Gravity changes based on position
        },
        'recursive_rooms': [
            {'x': 10, 'y': 10, 'size': 4, 'scale': 0.4},  # Central recursive room
            {'x': 8, 'y': 8, 'size': 8, 'scale': 0.7},   # Medium recursive room
            {'x': 9, 'y': 9, 'size': 2, 'scale': 0.2}    # Tiny recursive room
        ]
    }
]
# 4 = reality distortion wall
# 5 = perspective shift wall
# 6 = 4D hypercube entrance
# 7 = reality fracture
# 8 = dimensional shift

# Precompute sin/cos tables for faster lookups
SIN_TABLE = [math.sin(i * 0.01) for i in range(629)]  # 2*PI*100
COS_TABLE = [math.cos(i * 0.01) for i in range(629)]

def fast_sin(angle):
    idx = int(angle * 100) % 629
    return SIN_TABLE[idx]

def fast_cos(angle):
    idx = int(angle * 100) % 629
    return COS_TABLE[idx]

# Create seamless portals
PORTALS = []
for _ in range(3):
    # Create portals that are not just single points but entire doorways
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
        # Store the portal information
        portal1 = {'x': x1, 'y': y1, 'facing': facing1, 'linked_to': 1}
        portal2 = {'x': x2, 'y': y2, 'facing': facing2, 'linked_to': 0}
        PORTALS.append([portal1, portal2])
        
        # Mark portals with special values in the map
        MAP[y1, x1] = 2
        MAP[y2, x2] = 2

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

# Add 4D hypercube entrances
HYPERCUBES = []
for _ in range(2):
    x, y = random.randint(2, MAP_SIZE-3), random.randint(2, MAP_SIZE-3)
    if MAP[y, x] == 0:
        MAP[y, x] = 6  # Mark as hypercube entrance
        
        # Create a fractal-like pattern in the outer map
        outer_size = MAP_SIZE * 2  # Twice the size of the normal map
        outer_map = np.zeros((outer_size, outer_size), dtype=np.int32)
        
        # Create a fractal-like pattern in the outer map
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
        
        # Create recursive portals within the hypercube
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
        
        # Create hypercube rooms
        rooms = []
        for i in range(8):  # 8 rooms in the hypercube
            # Each room is a section of the outer map
            section_size = 8
            start_x = (i % 4) * section_size
            start_y = (i // 4) * section_size
            
            # Extract a section of the outer map
            room_map = np.copy(outer_map[start_y:start_y+section_size, start_x:start_x+section_size])
            
            # Add connections based on hypercube topology
            connections = []
            for j in range(8):
                if bin(i ^ j).count('1') == 1:  # XOR to check if they differ by exactly one bit
                    connections.append(j)
                    # Add a special wall that marks the connection
                    edge_x = 0 if (j % 4) < (i % 4) else section_size-1
                    edge_y = 0 if (j // 4) < (i // 4) else section_size-1
                    # Only add if it's not already a portal
                    if room_map[edge_y, edge_x] < 10:
                        room_map[edge_y, edge_x] = 20 + j  # Connection IDs start at 20
            
            # Add some special features to each room
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
                'position': (start_x, start_y)
            })
        
        # Add a special central room that connects to all others
        central_map = np.zeros((8, 8), dtype=np.int32)
        # Add walls in a maze-like pattern
        for cx in range(8):
            for cy in range(8):
                if (cx + cy) % 3 == 0 and cx > 0 and cx < 7 and cy > 0 and cy < 7:
                    central_map[cy, cx] = 1
        
        # Add connections to all other rooms
        central_connections = list(range(8))
        
        # Add the central room
        rooms.append({
            'map': central_map,
            'size': 8,
            'connections': central_connections,
            'position': (outer_size//2, outer_size//2),
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

# Add perspective shift walls
for _ in range(5):
    x, y = random.randint(2, MAP_SIZE-3), random.randint(2, MAP_SIZE-3)
    if MAP[y, x] == 0:
        MAP[y, x] = 5  # Perspective shift wall

# Create distortion fields
DISTORTION_FIELDS = []
for _ in range(4):
    x = random.randint(1, MAP_SIZE-2)
    y = random.randint(1, MAP_SIZE-2)
    radius = random.uniform(1.5, 3.0)
    strength = random.uniform(0.2, 0.8)
    DISTORTION_FIELDS.append((x, y, radius, strength))

# Player state
player_state = {
    'in_normal_space': True,
    'current_space': None,  # 'hypercube', 'non_euclidean'
    'space_position': [0, 0],  # Position in the current space
    'hypercube_id': 0,  # Current hypercube ID
    'non_euclidean_map_id': 0,  # Current non-Euclidean map ID
    'last_normal_pos': [0, 0],  # Last position in normal space
    'reality_level': 1.0,  # 1.0 = normal reality, 0.0 = complete unreality
    'gravity_direction': 0,  # 0 = normal, 1 = right, 2 = upside down, 3 = left
    'last_reality_check': 0  # Time of last reality check
}

# Wall colors
WALL_COLORS = {
    1: (200, 70, 60),    # Normal wall - brick red
    2: (0, 200, 200),    # Portal - cyan
    3: (200, 0, 200),    # Non-Euclidean space - magenta
    4: (255, 150, 0),    # Reality distortion - orange
    5: (100, 255, 100),  # Perspective shift - light green
    6: (150, 150, 255),  # 4D hypercube - light blue
    7: (255, 50, 50),    # Reality fracture - bright red
    8: (50, 255, 255)    # Dimensional shift - bright cyan
}

# Fast trigonometric functions using lookup tables for better performance
TRIG_TABLE_SIZE = 1024
sin_table = [math.sin(i * 2 * math.pi / TRIG_TABLE_SIZE) for i in range(TRIG_TABLE_SIZE)]
cos_table = [math.cos(i * 2 * math.pi / TRIG_TABLE_SIZE) for i in range(TRIG_TABLE_SIZE)]

def fast_sin(angle):
    # Convert angle to index in the lookup table
    index = int((angle % (2 * math.pi)) * TRIG_TABLE_SIZE / (2 * math.pi))
    return sin_table[index]

def fast_cos(angle):
    # Convert angle to index in the lookup table
    index = int((angle % (2 * math.pi)) * TRIG_TABLE_SIZE / (2 * math.pi))
    return cos_table[index]

# Define portals
PORTALS = [
    # Each portal pair connects two locations
    [
        {'x': 3, 'y': 3, 'facing': 0, 'linked_to': 1},  # Portal A
        {'x': 12, 'y': 12, 'facing': 2, 'linked_to': 0}   # Portal B
    ],
    [
        {'x': 3, 'y': 12, 'facing': 1, 'linked_to': 1},  # Portal C
        {'x': 12, 'y': 3, 'facing': 3, 'linked_to': 0}    # Portal D
    ]
]

# Add portals to the map
for portal_pair in PORTALS:
    for portal in portal_pair:
        MAP[portal['y'], portal['x']] = 2  # Portal type

# Define non-Euclidean spaces with emergent gameplay mechanics
NON_EUCLIDEAN_SPACES = [
    {
        'entrance': (5, 5),
        'exit_pos': (6, 5),
        'start_x': 1.5,
        'start_y': 1.5,
        'width': 15,  # Larger inner space
        'height': 15,
        'map': np.ones((15, 15), dtype=np.int32),  # All walls initially
        'mechanics': {
            'recursive_scaling': True,  # Space gets smaller as you go deeper
            'time_dilation': 0.5,       # Time flows differently inside
            'gravity_flux': True,        # Gravity direction shifts based on position
            'reality_bleed': 0.7,        # Reality level decreases in certain areas
            'perspective_inversion': True # Perspective can invert
        },
        'recursive_rooms': [
            # Room within a room within a room...
            {'x': 7, 'y': 7, 'size': 3, 'scale': 0.5},
            {'x': 3, 'y': 3, 'size': 2, 'scale': 0.3},
            {'x': 11, 'y': 3, 'size': 2, 'scale': 0.3},
            {'x': 3, 'y': 11, 'size': 2, 'scale': 0.3},
            {'x': 11, 'y': 11, 'size': 2, 'scale': 0.3}
        ]
    },
    {
        'entrance': (10, 5),
        'exit_pos': (11, 5),
        'start_x': 1.5,
        'start_y': 1.5,
        'width': 12,
        'height': 12,
        'map': np.ones((12, 12), dtype=np.int32),
        'mechanics': {
            'recursive_scaling': False,
            'time_dilation': 1.5,
            'gravity_flux': True,
            'reality_bleed': 0.8,
            'perspective_inversion': True
        },
        'mirror_dimension': True  # Everything is mirrored
    }
]

# Carve out the inner spaces with emergent gameplay features
for space in NON_EUCLIDEAN_SPACES:
    inner_map = space['map']
    w, h = space['width'], space['height']
    
    # Clear the center
    inner_map[1:h-1, 1:w-1] = 0
    
    # Add exit
    inner_map[1, w//2] = 3
    
    # Add reality distortion walls that create visual anomalies
    inner_map[h//2, 1] = 4
    inner_map[h//2, w-2] = 4
    
    # Add perspective shift walls that invert the player's view
    inner_map[1, w//4] = 5
    inner_map[1, 3*w//4] = 5
    
    # Add recursive rooms if specified
    if 'recursive_rooms' in space:
        for room in space['recursive_rooms']:
            rx, ry, size = room['x'], room['y'], room['size']
            # Create a room within a room
            for i in range(size):
                for j in range(size):
                    if i == 0 or j == 0 or i == size-1 or j == size-1:
                        # Wall of the recursive room
                        inner_map[ry+i, rx+j] = 9  # New wall type: recursive boundary
                    else:
                        # Inside of the recursive room
                        inner_map[ry+i, rx+j] = 0
            
            # Add a special portal in the center of the recursive room
            if size > 2:
                inner_map[ry+size//2, rx+size//2] = 10  # Recursive portal
    
    # Add mirror walls if it's a mirror dimension
    if space.get('mirror_dimension', False):
        # Add mirror walls along the diagonal
        for i in range(2, min(w, h)-2):
            inner_map[i, i] = 11  # Mirror wall type
        
        # Add some mirror fragments in random locations
        for _ in range(5):
            mx = random.randint(2, w-3)
            my = random.randint(2, h-3)
            inner_map[my, mx] = 11
    
    # Add the entrance to the map
    x, y = space['entrance']
    MAP[y, x] = 3  # Non-Euclidean space entrance

# Define hypercubes - enhanced for 4D seamless connections
HYPERCUBES = [
    {
        'id': 0,
        'entrance': (8, 8),
        'exit_pos': (9, 8),
        'start_x': 2.5,
        'start_y': 2.5,
        'outer_size': 16,
        'outer_map': np.ones((16, 16), dtype=np.int32),  # Outer map structure
        'rooms': [
            # Room 0 - Central hub
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'is_central': True,
                'connections': {0: 1, 1: 2, 2: 3, 3: 4},
                '4d_connections': {
                    0: {'cube': 1, 'room': 0, 'face': 2, 'rotation': 0},
                    1: {'cube': 1, 'room': 1, 'face': 3, 'rotation': 1},
                    2: {'cube': 1, 'room': 2, 'face': 0, 'rotation': 2},
                    3: {'cube': 1, 'room': 3, 'face': 1, 'rotation': 3}
                }
            },
            # Room 1 - Reality fracture room
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {0: 0, 2: 5},
                '4d_connections': {
                    0: {'cube': 1, 'room': 5, 'face': 2, 'rotation': 0},
                    1: {'cube': 1, 'room': 1, 'face': 3, 'rotation': 1},
                    2: {'cube': 0, 'room': 5, 'face': 0, 'rotation': 2},
                    3: {'cube': 0, 'room': 0, 'face': 1, 'rotation': 3}
                }
            },
            # Room 2 - Dimensional shift room
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (10, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {1: 0, 3: 6},
                '4d_connections': {
                    0: {'cube': 0, 'room': 6, 'face': 2, 'rotation': 1},
                    1: {'cube': 0, 'room': 0, 'face': 1, 'rotation': 3},
                    2: {'cube': 1, 'room': 2, 'face': 0, 'rotation': 2},
                    3: {'cube': 1, 'room': 6, 'face': 1, 'rotation': 0}
                }
            },
            # Room 3 - Recursive portal room
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {2: 0, 0: 7},
                '4d_connections': {
                    0: {'cube': 0, 'room': 7, 'face': 2, 'rotation': 0},
                    1: {'cube': 1, 'room': 7, 'face': 3, 'rotation': 1},
                    2: {'cube': 0, 'room': 0, 'face': 2, 'rotation': 0},
                    3: {'cube': 1, 'room': 3, 'face': 1, 'rotation': 3}
                }
            },
            # Room 4 - Exit room
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {3: 0},
                '4d_connections': {
                    0: {'cube': 1, 'room': 0, 'face': 2, 'rotation': 2},
                    1: {'cube': 1, 'room': 4, 'face': 3, 'rotation': 0},
                    2: {'cube': 0, 'room': 0, 'face': 3, 'rotation': 0},
                    3: {'cube': 0, 'room': 0, 'face': 3, 'rotation': 0}
                }
            },
            # Room 5 - Nested room 1
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (10, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {2: 1},
                '4d_connections': {
                    0: {'cube': 1, 'room': 5, 'face': 2, 'rotation': 1},
                    1: {'cube': 0, 'room': 1, 'face': 2, 'rotation': 2},
                    2: {'cube': 0, 'room': 1, 'face': 0, 'rotation': 0},
                    3: {'cube': 1, 'room': 1, 'face': 1, 'rotation': 3}
                }
            },
            # Room 6 - Nested room 2
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 10),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {3: 2},
                '4d_connections': {
                    0: {'cube': 0, 'room': 2, 'face': 0, 'rotation': 3},
                    1: {'cube': 1, 'room': 6, 'face': 3, 'rotation': 2},
                    2: {'cube': 1, 'room': 2, 'face': 0, 'rotation': 1},
                    3: {'cube': 0, 'room': 2, 'face': 3, 'rotation': 0}
                }
            },
            # Room 7 - Nested room 3
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 10),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {0: 3},
                '4d_connections': {
                    0: {'cube': 0, 'room': 3, 'face': 0, 'rotation': 0},
                    1: {'cube': 1, 'room': 3, 'face': 1, 'rotation': 3},
                    2: {'cube': 1, 'room': 7, 'face': 0, 'rotation': 3},
                    3: {'cube': 0, 'room': 3, 'face': 1, 'rotation': 1}
                }
            }
        ]
    },
    {
        'id': 1,
        'entrance': (12, 8),
        'exit_pos': (13, 8),
        'start_x': 2.5,
        'start_y': 2.5,
        'outer_size': 16,
        'outer_map': np.ones((16, 16), dtype=np.int32),  # Outer map structure
        'rooms': [
            # Room 0 - Central hub (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'is_central': True,
                'connections': {0: 1, 1: 2, 2: 3, 3: 4},
                '4d_connections': {
                    0: {'cube': 1, 'room': 4, 'face': 0, 'rotation': 2},
                    1: {'cube': 1, 'room': 5, 'face': 3, 'rotation': 1},
                    2: {'cube': 0, 'room': 0, 'face': 0, 'rotation': 0},
                    3: {'cube': 1, 'room': 3, 'face': 1, 'rotation': 3}
                }
            },
            # Room 1 - Reality fracture room (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {0: 0, 2: 5},
                '4d_connections': {
                    0: {'cube': 1, 'room': 0, 'face': 0, 'rotation': 0},
                    1: {'cube': 0, 'room': 5, 'face': 3, 'rotation': 1},
                    2: {'cube': 1, 'room': 5, 'face': 0, 'rotation': 2},
                    3: {'cube': 0, 'room': 1, 'face': 1, 'rotation': 1}
                }
            },
            # Room 2 - Dimensional shift room (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (10, 0),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {1: 0, 3: 6},
                '4d_connections': {
                    0: {'cube': 0, 'room': 2, 'face': 2, 'rotation': 2},
                    1: {'cube': 1, 'room': 0, 'face': 1, 'rotation': 0},
                    2: {'cube': 1, 'room': 6, 'face': 0, 'rotation': 1},
                    3: {'cube': 0, 'room': 6, 'face': 1, 'rotation': 3}
                }
            },
            # Room 3 - Recursive portal room (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {2: 0, 0: 7},
                '4d_connections': {
                    0: {'cube': 1, 'room': 7, 'face': 2, 'rotation': 0},
                    1: {'cube': 0, 'room': 3, 'face': 3, 'rotation': 3},
                    2: {'cube': 1, 'room': 0, 'face': 2, 'rotation': 0},
                    3: {'cube': 0, 'room': 0, 'face': 3, 'rotation': 1}
                }
            },
            # Room 4 - Exit room (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {3: 0},
                '4d_connections': {
                    0: {'cube': 0, 'room': 4, 'face': 0, 'rotation': 2},
                    1: {'cube': 1, 'room': 5, 'face': 3, 'rotation': 1},
                    2: {'cube': 1, 'room': 0, 'face': 0, 'rotation': 2},
                    3: {'cube': 0, 'room': 4, 'face': 1, 'rotation': 0}
                }
            },
            # Room 5 - Nested room 1 (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (10, 5),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {2: 1},
                '4d_connections': {
                    0: {'cube': 0, 'room': 1, 'face': 1, 'rotation': 3},
                    1: {'cube': 1, 'room': 4, 'face': 1, 'rotation': 3},
                    2: {'cube': 0, 'room': 5, 'face': 0, 'rotation': 1},
                    3: {'cube': 1, 'room': 1, 'face': 0, 'rotation': 0}
                }
            },
            # Room 6 - Nested room 2 (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (0, 10),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {3: 2},
                '4d_connections': {
                    0: {'cube': 1, 'room': 2, 'face': 2, 'rotation': 1},
                    1: {'cube': 0, 'room': 2, 'face': 1, 'rotation': 0},
                    2: {'cube': 1, 'room': 7, 'face': 0, 'rotation': 3},
                    3: {'cube': 0, 'room': 6, 'face': 1, 'rotation': 2}
                }
            },
            # Room 7 - Nested room 3 (mirrored)
            {
                'map': np.ones((5, 5), dtype=np.int32),
                'size': 5,
                'position': (5, 10),
                'start_x': 2.5,
                'start_y': 2.5,
                'connections': {0: 3},
                '4d_connections': {
                    0: {'cube': 0, 'room': 7, 'face': 2, 'rotation': 3},
                    1: {'cube': 1, 'room': 3, 'face': 0, 'rotation': 0},
                    2: {'cube': 1, 'room': 6, 'face': 2, 'rotation': 1},
                    3: {'cube': 0, 'room': 3, 'face': 0, 'rotation': 0}
                }
            }
        ]
    }
]

# Carve out the hypercube rooms
for cube in HYPERCUBES:
    # Add the entrance to the map
    x, y = cube['entrance']
    MAP[y, x] = 6  # Hypercube entrance
    
    # Also add the exit position
    ex, ey = cube['exit_pos']
    MAP[ey, ex] = 1  # Normal wall at exit position
    
    # Setup each room
    for room in cube['rooms']:
        room_map = room['map']
        size = room['size']
        
        # Clear the center of the room
        room_map[1:size-1, 1:size-1] = 0
        
        # Add connections to other rooms
        for direction, target_room in room['connections'].items():
            # Place connection on the appropriate wall
            if direction == 0:  # North
                room_map[1, size//2] = 20 + direction  # 20-27 are connection types
            elif direction == 1:  # East
                room_map[size//2, size-2] = 20 + direction
            elif direction == 2:  # South
                room_map[size-2, size//2] = 20 + direction
            elif direction == 3:  # West
                room_map[size//2, 1] = 20 + direction
                
        # Add 4D connections to other hypercubes
        if '4d_connections' in room:
            for direction, connection in room['4d_connections'].items():
                # Place 4D connection on the appropriate wall - make them wider and more visible
                if direction == 0:  # North
                    # Create a wider portal (5 cells wide) for better visibility and easier access
                    portal_width = min(size-2, 5)  # Make sure it doesn't exceed room size
                    start_pos = max(1, size//2 - portal_width//2)
                    end_pos = min(size-1, start_pos + portal_width)
                    room_map[0, start_pos:end_pos] = 30  # Special wall type for 4D connections
                    # Add visual indicators around the portal
                    if start_pos > 1:
                        room_map[0, start_pos-1] = 4  # Reality distortion wall as marker
                    if end_pos < size-1:
                        room_map[0, end_pos] = 4  # Reality distortion wall as marker
                elif direction == 1:  # East
                    portal_width = min(size-2, 5)
                    start_pos = max(1, size//2 - portal_width//2)
                    end_pos = min(size-1, start_pos + portal_width)
                    room_map[start_pos:end_pos, size-1] = 30
                    if start_pos > 1:
                        room_map[start_pos-1, size-1] = 4
                    if end_pos < size-1:
                        room_map[end_pos, size-1] = 4
                elif direction == 2:  # South
                    portal_width = min(size-2, 5)
                    start_pos = max(1, size//2 - portal_width//2)
                    end_pos = min(size-1, start_pos + portal_width)
                    room_map[size-1, start_pos:end_pos] = 30
                    if start_pos > 1:
                        room_map[size-1, start_pos-1] = 4
                    if end_pos < size-1:
                        room_map[size-1, end_pos] = 4
                elif direction == 3:  # West
                    portal_width = min(size-2, 5)
                    start_pos = max(1, size//2 - portal_width//2)
                    end_pos = min(size-1, start_pos + portal_width)
                    room_map[start_pos:end_pos, 0] = 30
                    if start_pos > 1:
                        room_map[start_pos-1, 0] = 4
                    if end_pos < size-1:
                        room_map[end_pos, 0] = 4
        
        # Add special features to rooms
        if 'is_central' in room and room['is_central']:
            # Add exit in central room
            room_map[1, 1] = 6  # Exit to normal space
            
            # Add recursive portals
            room_map[size-2, 1] = 10  # Recursive portal type 0
            room_map[size-2, size-2] = 11  # Recursive portal type 1
        
        # Add reality fracture to room 1
        if room is cube['rooms'][1]:  # Use 'is' for identity comparison instead of '=='
            room_map[2, 2] = 7  # Reality fracture
        
        # Add dimensional shift to room 2
        if room is cube['rooms'][2]:  # Use 'is' for identity comparison instead of '=='
            room_map[2, 2] = 8  # Dimensional shift

# Optimized raycasting function with portal viewing
# Pre-allocate arrays to avoid recreation each frame
_wall_heights = [0] * WIDTH
_wall_colors = [(0, 0, 0) for _ in range(WIDTH)]
_wall_types = [0] * WIDTH
_wall_effects = [None] * WIDTH

def raycast(player_x, player_y, player_angle):
    # Reuse pre-allocated arrays
    wall_heights = _wall_heights
    wall_colors = _wall_colors
    wall_types = _wall_types
    wall_effects = _wall_effects
    
    # Clear arrays
    for i in range(WIDTH):
        wall_heights[i] = 0
        wall_colors[i] = (0, 0, 0)
        wall_types[i] = 0
        wall_effects[i] = None
    
    # Check if player is in a special space
    if not player_state['in_normal_space']:
        if player_state['current_space'] == 'non_euclidean':
            return raycast_non_euclidean(player_state['space_position'][0], player_state['space_position'][1], player_angle)
        elif player_state['current_space'] == 'hypercube':
            return raycast_hypercube(player_state['hypercube_room'], player_state['space_position'][0], player_state['space_position'][1], player_angle)
    
    # Cast rays for each screen column
    for x in range(WIDTH):
        # Precompute values outside the raycasting loop
        reality_level = player_state['reality_level']
        reality_distortion = 1.0 - reality_level
        time_factor = time.time()
        
        # Calculate ray angle with distortion
        ray_angle = (player_angle - math.radians(HALF_FOV)) + (x * (math.radians(FOV) / WIDTH))
        distortion = math.sin(time_factor * 3 + x * 0.05) * reality_distortion * 0.2
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
        
        # Portal tracking
        max_portal_recursion = 2  # Limit portal recursion for performance
        portal_recursion = 0
        portals_traversed = set()  # Track which portals we've gone through
        
        # Step size - larger for better performance
        step_size = 0.05
        
        # Cast the ray
        while not hit_wall and distance < 20 and portal_recursion <= max_portal_recursion:
            # Move the ray
            ray_x += ray_dir_x * step_size
            ray_y += ray_dir_y * step_size
            distance += step_size
            
            # Check if we hit a wall
            map_x = int(ray_x)
            map_y = int(ray_y)
            
            # Check if we're in bounds
            if 0 <= map_x < MAP_SIZE and 0 <= map_y < MAP_SIZE:
                wall_type = MAP[map_y, map_x]
                
                # Handle portals - allow seeing through them
                if wall_type == 2:  # Portal
                    # Find which portal we hit
                    portal_found = False
                    for portal_pair in PORTALS:
                        for i, portal in enumerate(portal_pair):
                            portal_x, portal_y = portal['x'], portal['y']
                            
                            if map_x == portal_x and map_y == portal_y:
                                # Skip if we've already gone through this portal
                                portal_id = (portal_x, portal_y)
                                if portal_id in portals_traversed:
                                    continue
                                
                                # We hit a portal - get the linked portal
                                linked_idx = portal['linked_to']
                                linked_portal = portal_pair[linked_idx]
                                
                                # Calculate the offset to apply to the ray
                                offset_x = linked_portal['x'] - portal_x
                                offset_y = linked_portal['y'] - portal_y
                                
                                # Calculate rotation to apply (difference in facing directions)
                                rotation = (linked_portal['facing'] - portal['facing']) * math.pi/2
                                
                                # Apply the portal transformation
                                ray_x += offset_x
                                ray_y += offset_y
                                
                                # Apply rotation to ray direction if portals face different directions
                                if rotation != 0:
                                    old_dir_x = ray_dir_x
                                    old_dir_y = ray_dir_y
                                    ray_dir_x = old_dir_x * math.cos(rotation) - old_dir_y * math.sin(rotation)
                                    ray_dir_y = old_dir_x * math.sin(rotation) + old_dir_y * math.cos(rotation)
                                
                                # Mark this portal as traversed
                                portals_traversed.add(portal_id)
                                portal_recursion += 1
                                portal_found = True
                                break
                        
                        if portal_found:
                            break
                    
                    # If we found a portal, continue ray casting
                    if portal_found:
                        continue
                
                # Handle non-portal walls
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
                    elif wall_type == 7:  # Reality fracture
                        special_effect = 'reality_fracture'
                    elif wall_type == 8:  # Dimensional shift
                        special_effect = 'dimensional_shift'
            else:
                # Out of bounds
                hit_wall = True
                wall_type = 1  # Treat as a normal wall
        
        # Calculate wall height and color
        if hit_wall:
            # Apply fish-eye correction
            correct_distance = distance * math.cos(ray_angle - player_angle)
            
            # Calculate wall height
            wall_height = int(HEIGHT / correct_distance)
            
            # Apply special effects
            if special_effect == 'perspective_shift':
                shift = math.sin(time.time() * 2 + x * 0.1) * 0.3
                wall_height = int(wall_height * (1.0 + shift))
            
            # Store results
            wall_heights[x] = min(wall_height, HEIGHT)  # Clamp to screen height
            wall_colors[x] = WALL_COLORS.get(wall_type, (200, 200, 200))
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Apply shading and effects in a single pass
            shade = 1.0 - min(1.0, distance / 20.0)
            r, g, b = wall_colors[x]
            
            # Apply distance shading
            r = int(r * shade)
            g = int(g * shade)
            b = int(b * shade)
            
            # Apply trippy effects if needed
            if reality_distortion > 0:
                distortion = reality_distortion * 0.5
                r = min(255, int(r * (1 + math.sin(time_factor * 2 + x * 0.1) * distortion)))
                g = min(255, int(g * (1 + math.sin(time_factor * 2 + x * 0.05) * distortion)))
                b = min(255, int(b * (1 + math.sin(time_factor * 2 + x * 0.02) * distortion)))
            
            wall_colors[x] = (r, g, b)
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Optimized raycasting for non-Euclidean spaces with emergent gameplay mechanics
def raycast_non_euclidean(pos_x, pos_y, angle):
    # Find which non-Euclidean space we're in
    current_space = None
    for space in NON_EUCLIDEAN_SPACES:
        if player_state['non_euclidean_map_id'] == space['entrance']:
            current_space = space
            break
    
    if not current_space:
        # Fallback to normal raycasting
        return raycast(pos_x, pos_y, angle)
    
    # Results
    wall_heights = [0] * WIDTH
    wall_colors = [(0, 0, 0)] * WIDTH
    wall_types = [0] * WIDTH
    wall_effects = [None] * WIDTH
    
    inner_map = current_space['map']
    inner_width = current_space['width']
    inner_height = current_space['height']
    mechanics = current_space.get('mechanics', {})
    
    # Apply mechanics to the player
    if 'reality_bleed' in mechanics:
        # Gradually reduce reality level while in this space
        reality_target = mechanics['reality_bleed']
        player_state['reality_level'] = max(reality_target, player_state['reality_level'] - 0.001)
    
    # Apply gravity flux if enabled
    if mechanics.get('gravity_flux', False):
        # Change gravity direction based on position in the space
        center_x, center_y = inner_width / 2, inner_height / 2
        dist_from_center = math.sqrt((pos_x - center_x)**2 + (pos_y - center_y)**2)
        angle_to_center = math.atan2(pos_y - center_y, pos_x - center_x)
        
        # Determine gravity direction based on position
        if dist_from_center > inner_width / 4:
            # Outer area - gravity points toward center
            gravity_angle = (angle_to_center + math.pi) % (2 * math.pi)  # Opposite of angle to center
            gravity_direction = int((gravity_angle / (math.pi/2)) % 4)  # Convert to 0,1,2,3
            
            # Only update if it's different to avoid constant changes
            if gravity_direction != player_state['gravity_direction']:
                player_state['gravity_direction'] = gravity_direction
    
    # Apply time dilation
    time_dilation = mechanics.get('time_dilation', 1.0)
    current_time = time.time() * time_dilation
    
    # Apply perspective inversion if enabled
    perspective_inversion = mechanics.get('perspective_inversion', False) and player_state['reality_level'] < 0.8
    if perspective_inversion:
        # Invert the angle periodically for a mind-bending effect
        if math.sin(current_time * 0.2) > 0.9:
            angle = (angle + math.pi) % (2 * math.pi)  # Invert view direction
    
    # Check if we're in a mirror dimension
    mirror_dimension = current_space.get('mirror_dimension', False)
    
    # Cast rays in the inner space
    for x in range(WIDTH):
        # Calculate ray angle
        ray_angle = (angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Apply non-Euclidean bending to ray direction
        bend_factor = math.sin(current_time * 0.5 + x * 0.01) * 0.05
        if perspective_inversion:
            # More extreme bending when perspective is inverted
            bend_factor *= 3.0
        
        temp_x = ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        ray_dir_x = ray_dir_x * math.cos(bend_factor) - ray_dir_y * math.sin(bend_factor)
        ray_dir_y = temp_x * math.sin(bend_factor) + ray_dir_y * math.cos(bend_factor)
        
        # Apply mirror effect if in mirror dimension
        if mirror_dimension and x > WIDTH/2:
            ray_dir_x = -ray_dir_x  # Mirror the x-component for half the screen
        
        # Current position
        ray_x = pos_x
        ray_y = pos_y
        
        # Distance traveled
        distance = 0.0
        hit_wall = False
        wall_type = 0
        special_effect = None
        
        # Track if we're in a recursive room
        in_recursive_room = False
        recursive_scale = 1.0
        recursive_level = 0
        
        # Cast the ray
        max_distance = inner_width + inner_height
        step_size = 0.05
        
        while not hit_wall and distance < max_distance:
            # Apply recursive scaling if enabled
            if mechanics.get('recursive_scaling', False) and 'recursive_rooms' in current_space:
                # Check if we're in a recursive room
                for room in current_space['recursive_rooms']:
                    rx, ry, size, scale = room['x'], room['y'], room['size'], room.get('scale', 0.5)
                    
                    # Check if ray is in this room
                    if rx <= ray_x < rx + size and ry <= ray_y < ry + size:
                        in_recursive_room = True
                        recursive_scale = scale
                        recursive_level += 1
                        
                        # Adjust step size based on recursive scale
                        step_size = 0.05 * recursive_scale
                        break
            
            # Move the ray with potentially adjusted step size
            ray_x += ray_dir_x * step_size
            ray_y += ray_dir_y * step_size
            distance += step_size
            
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
                    elif wall_type == 30:  # 4D hypercube connection
                        special_effect = '4d_transition'
                        # Make the wall visible but allow passing through
                        hit_wall = True  # Make it visible
                        # Don't set hit_wall to false here as we want to see the wall
                        # The player movement code will handle the transition
                    elif wall_type == 9:  # Recursive boundary
                        special_effect = 'recursive_boundary'
                        # If we're in a recursive room, this is a portal to a deeper level
                        if in_recursive_room and mechanics.get('recursive_scaling', False):
                            hit_wall = False  # Continue through the boundary
                            in_recursive_room = True
                            recursive_level += 1
                            recursive_scale *= 0.5  # Scale down further
                    elif wall_type == 10:  # Recursive portal
                        special_effect = 'recursive_portal'
                    elif wall_type == 11:  # Mirror wall
                        special_effect = 'mirror'
                        # Reflect the ray direction
                        normal_x, normal_y = 0, 0
                        
                        # Determine the normal vector of the mirror surface
                        if map_x == map_y:  # Diagonal mirror
                            normal_x = normal_y = 0.7071  # 1/sqrt(2)
                        else:  # Random mirror fragment
                            # Randomize the normal but keep it consistent
                            random.seed(map_x * 1000 + map_y)
                            angle = random.random() * 2 * math.pi
                            normal_x = math.cos(angle)
                            normal_y = math.sin(angle)
                        
                        # Calculate reflection
                        dot = 2 * (ray_dir_x * normal_x + ray_dir_y * normal_y)
                        ray_dir_x = ray_dir_x - dot * normal_x
                        ray_dir_y = ray_dir_y - dot * normal_y
                        
                        # Continue raycasting with reflected direction
                        hit_wall = False
                        ray_x += ray_dir_x * 0.1  # Move away from mirror slightly
                        ray_y += ray_dir_y * 0.1
            else:
                # Hit the boundary of the inner space, return to normal space
                hit_wall = True
                wall_type = 3  # Non-Euclidean space exit
                special_effect = 'non_euclidean_exit'
        
        # Calculate wall height
        if hit_wall:
            # Apply fish-eye correction
            correct_distance = distance * math.cos(ray_angle - angle)
            
            # Calculate wall height with adjustments for recursive scaling
            base_height = (1.0 / correct_distance) * HEIGHT * 0.5
            if in_recursive_room:
                # Scale the wall height based on recursive level
                base_height *= (1.0 + recursive_level * 0.2)
            
            wall_height = min(HEIGHT, int(base_height))
            
            # Apply perspective shifts for special walls
            if special_effect == 'perspective_shift':
                shift = math.sin(current_time * 2 + x * 0.1) * 0.3
                wall_height = int(wall_height * (1.0 + shift))
            elif special_effect == 'recursive_boundary':
                # Pulsing effect for recursive boundaries
                pulse = math.sin(current_time * 3 + recursive_level) * 0.2
                wall_height = int(wall_height * (1.0 + pulse))
            elif special_effect == 'recursive_portal':
                # Swirling effect for recursive portals
                swirl = math.sin(current_time * 4 + x * 0.2) * 0.4
                wall_height = int(wall_height * (1.0 + swirl))
            elif special_effect == 'mirror':
                # Shimmering effect for mirrors
                shimmer = math.sin(current_time * 5 + x * 0.3) * 0.15
                wall_height = int(wall_height * (1.0 + shimmer))
            
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color based on distance, type, and effects
            if wall_type == 1:  # Regular wall
                base_color = (150, 50, 150)  # Purple for inner space walls
            elif wall_type == 3:  # Exit
                base_color = (200, 0, 200)  # Magenta
            elif wall_type == 4:  # Reality distortion
                base_color = (255, 150, 0)  # Orange
            elif wall_type == 5:  # Perspective shift
                base_color = (100, 255, 100)  # Light green
            elif wall_type == 30:  # 4D hypercube connection
                # Shifting cosmic colors for 4D connections
                time_factor = time.time() * 2
                r = int(128 + 127 * math.sin(time_factor))
                g = int(128 + 127 * math.sin(time_factor + 2*math.pi/3))
                b = int(200 + 55 * math.sin(time_factor + 4*math.pi/3))  # More blue to make it stand out
                base_color = (r, g, b)
            elif wall_type == 9:  # Recursive boundary
                # Color based on recursive level
                hue = (recursive_level * 0.2) % 1.0
                r = int(128 + 127 * math.sin(hue * 2 * math.pi))
                g = int(128 + 127 * math.sin(hue * 2 * math.pi + 2*math.pi/3))
                b = int(128 + 127 * math.sin(hue * 2 * math.pi + 4*math.pi/3))
                base_color = (r, g, b)
            elif wall_type == 10:  # Recursive portal
                # Shifting colors for portals
                portal_hue = current_time * 0.1
                r = int(128 + 127 * math.sin(portal_hue))
                g = int(128 + 127 * math.sin(portal_hue + 2*math.pi/3))
                b = int(128 + 127 * math.sin(portal_hue + 4*math.pi/3))
                base_color = (r, g, b)
            elif wall_type == 11:  # Mirror
                # Reflective silver color
                mirror_pulse = math.sin(current_time * 3 + x * 0.1) * 0.3 + 0.7
                base_color = (int(200 * mirror_pulse), int(200 * mirror_pulse), int(220 * mirror_pulse))
            else:
                base_color = (150, 150, 150)  # Gray
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / max_distance)
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply trippy color effect based on reality level
            reality_factor = 1.0 - player_state['reality_level']
            time_factor = current_time * 2
            r = min(255, int(wall_color[0] * (1 + math.sin(time_factor + x * 0.1) * 0.2 * reality_factor)))
            g = min(255, int(wall_color[1] * (1 + math.sin(time_factor + x * 0.05) * 0.2 * reality_factor)))
            b = min(255, int(wall_color[2] * (1 + math.sin(time_factor + x * 0.02) * 0.2 * reality_factor)))
            
            # In mirror dimension, invert colors on one side
            if mirror_dimension and x > WIDTH/2:
                r, g, b = 255-r, 255-g, 255-b
            
            wall_colors[x] = (r, g, b)
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Optimized raycasting for hypercube spaces with seamless 4D connections
def raycast_hypercube(room_id, pos_x, pos_y, angle):
    # Find the current hypercube
    current_cube = None
    for cube in HYPERCUBES:
        if player_state['current_hypercube_id'] == cube['entrance']:
            current_cube = cube
            break
    
    if not current_cube:
        # Fallback to normal raycasting
        return raycast(pos_x, pos_y, angle)
    
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
    room_x, room_y = current_room['position']
    
    # Cast rays in the hypercube room
    for x in range(WIDTH):
        # Calculate ray angle
        ray_angle = (angle - math.radians(HALF_FOV)) + (x / WIDTH) * math.radians(FOV)
        
        # Ray direction
        ray_dir_x = fast_cos(ray_angle)
        ray_dir_y = fast_sin(ray_angle)
        
        # Apply 4D rotation to ray direction
        w_coord = room_id / 8.0  # Normalize to 0-1 range
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
        
        # 4D traversal tracking
        current_cube_id = current_cube['id']
        current_room_id = room_id
        current_ray_x = ray_x
        current_ray_y = ray_y
        current_ray_dir_x = ray_dir_x
        current_ray_dir_y = ray_dir_y
        
        # Track 4D transitions to avoid infinite loops
        max_4d_transitions = 3
        transitions_count = 0
        traversed_spaces = set([(current_cube_id, current_room_id)])
        
        # Cast the ray
        max_distance = room_size * 2
        while not hit_wall and distance < max_distance and transitions_count <= max_4d_transitions:
            # Move the ray
            current_ray_x += current_ray_dir_x * 0.05
            current_ray_y += current_ray_dir_y * 0.05
            distance += 0.05
            
            # Check if we hit a wall in the room
            map_x = int(current_ray_x)
            map_y = int(current_ray_y)
            
            # Get the current room map
            current_room = HYPERCUBES[current_cube_id]['rooms'][current_room_id]
            room_map = current_room['map']
            room_size = current_room['size']
            
            if 0 <= map_x < room_size and 0 <= map_y < room_size:
                wall_type = room_map[map_y, map_x]
                if wall_type > 0:
                    # Check for 4D connections first
                    if '4d_connections' in current_room and map_x in (0, room_size-1) or map_y in (0, room_size-1):
                        # Determine which face we're on
                        face = -1
                        if map_y == 0: face = 0  # North
                        elif map_x == room_size-1: face = 1  # East
                        elif map_y == room_size-1: face = 2  # South
                        elif map_x == 0: face = 3  # West
                        
                        # Check if this face has a 4D connection
                        if face in current_room['4d_connections']:
                            # We hit a 4D connection - seamless transition to another hypercube
                            connection = current_room['4d_connections'][face]
                            target_cube_id = connection['cube']
                            target_room_id = connection['room']
                            target_face = connection['face']
                            rotation = connection['rotation']
                            
                            # Skip if we've already traversed this space
                            if (target_cube_id, target_room_id) in traversed_spaces:
                                hit_wall = True
                                special_effect = '4d_loop'
                                continue
                            
                            # Calculate new position in the target room
                            target_room = HYPERCUBES[target_cube_id]['rooms'][target_room_id]
                            target_size = target_room['size']
                            
                            # Map coordinates from one face to the opposite face
                            if face == 0:  # North to South
                                new_x = map_x
                                new_y = target_size - 1
                            elif face == 1:  # East to West
                                new_x = 0
                                new_y = map_y
                            elif face == 2:  # South to North
                                new_x = map_x
                                new_y = 0
                            elif face == 3:  # West to East
                                new_x = target_size - 1
                                new_y = map_y
                            
                            # Apply rotation based on the connection
                            for _ in range(rotation):
                                new_x, new_y = target_size - 1 - new_y, new_x
                            
                            # Apply rotation to ray direction
                            new_dir_x, new_dir_y = current_ray_dir_x, current_ray_dir_y
                            for _ in range(rotation):
                                new_dir_x, new_dir_y = new_dir_y, -new_dir_x
                            
                            # Update current state to the new hypercube/room
                            current_cube_id = target_cube_id
                            current_room_id = target_room_id
                            current_ray_x = new_x + 0.1 * new_dir_x  # Offset slightly to avoid boundary issues
                            current_ray_y = new_y + 0.1 * new_dir_y
                            current_ray_dir_x = new_dir_x
                            current_ray_dir_y = new_dir_y
                            
                            # Track this transition
                            traversed_spaces.add((target_cube_id, target_room_id))
                            transitions_count += 1
                            special_effect = '4d_transition'
                            continue
                    
                    # If not a 4D connection, handle regular wall types
                    hit_wall = True
                    
                    # Check for different wall types
                    if wall_type >= 20 and wall_type < 28:  # Connections to other rooms
                        connection_id = wall_type - 20
                        if connection_id in current_room['connections']:
                            special_effect = f'hypercube_connection_{connection_id}'
                    elif wall_type >= 10 and wall_type < 15:  # Recursive portals
                        portal_id = wall_type - 10
                        special_effect = f'recursive_portal_{portal_id}'
                    elif wall_type == 6:  # Exit back to normal space
                        special_effect = 'hypercube_exit'
                    elif wall_type == 7:  # Reality fracture
                        special_effect = 'reality_fracture'
                    elif wall_type == 8:  # Dimensional shift
                        special_effect = 'dimensional_shift'
            else:
                # We've hit the boundary of the current room section
                # Check if we should do a 4D transition
                face = -1
                if map_y < 0: face = 0  # North
                elif map_x >= room_size: face = 1  # East
                elif map_y >= room_size: face = 2  # South
                elif map_x < 0: face = 3  # West
                
                if face in current_room.get('4d_connections', {}):
                    # 4D transition at boundary
                    connection = current_room['4d_connections'][face]
                    target_cube_id = connection['cube']
                    target_room_id = connection['room']
                    target_face = connection['face']
                    rotation = connection['rotation']
                    
                    # Skip if we've already traversed this space
                    if (target_cube_id, target_room_id) in traversed_spaces:
                        hit_wall = True
                        special_effect = '4d_loop'
                        continue
                    
                    # Calculate new position in the target room
                    target_room = HYPERCUBES[target_cube_id]['rooms'][target_room_id]
                    target_size = target_room['size']
                    
                    # Map coordinates from one face to the opposite face
                    if face == 0:  # North to South
                        new_x = current_ray_x
                        new_y = target_size - 0.1
                    elif face == 1:  # East to West
                        new_x = 0.1
                        new_y = current_ray_y
                    elif face == 2:  # South to North
                        new_x = current_ray_x
                        new_y = 0.1
                    elif face == 3:  # West to East
                        new_x = target_size - 0.1
                        new_y = current_ray_y
                    
                    # Apply rotation based on the connection
                    for _ in range(rotation):
                        new_x, new_y = target_size - 1 - new_y, new_x
                    
                    # Apply rotation to ray direction
                    new_dir_x, new_dir_y = current_ray_dir_x, current_ray_dir_y
                    for _ in range(rotation):
                        new_dir_x, new_dir_y = new_dir_y, -new_dir_x
                    
                    # Update current state to the new hypercube/room
                    current_cube_id = target_cube_id
                    current_room_id = target_room_id
                    current_ray_x = new_x
                    current_ray_y = new_y
                    current_ray_dir_x = new_dir_x
                    current_ray_dir_y = new_dir_y
                    
                    # Track this transition
                    traversed_spaces.add((target_cube_id, target_room_id))
                    transitions_count += 1
                    special_effect = '4d_transition'
                    continue
                else:
                    # Calculate position in the outer map
                    room_x, room_y = current_room['position']
                    outer_x = room_x + map_x
                    outer_y = room_y + map_y
                    
                    # Check if this position is within the outer map
                    outer_size = HYPERCUBES[current_cube_id]['outer_size']
                    if 0 <= outer_x < outer_size and 0 <= outer_y < outer_size:
                        # We can see into the outer map - truly impossible space
                        wall_type = HYPERCUBES[current_cube_id]['outer_map'][outer_y, outer_x]
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
            w_coord = current_room_id / 8.0  # Use current room for w-coordinate
            w_height_effect = 1.0 + 0.2 * math.sin(w_coord * math.pi * 4 + time.time())
            
            # Add additional effects for special walls
            if special_effect == 'reality_fracture':
                fracture = math.sin(time.time() * 3 + x * 0.2) * 0.4
                w_height_effect *= (1.0 + fracture)
            elif special_effect == 'dimensional_shift':
                shift = math.sin(time.time() * 2 + distance * 0.5) * 0.5
                w_height_effect *= (1.0 + shift)
            elif special_effect == '4d_transition':
                # Special effect for 4D transitions
                transition_effect = math.sin(time.time() * 4 + x * 0.1) * 0.3
                w_height_effect *= (1.0 + transition_effect)
            elif special_effect == '4d_loop':
                # Special effect for 4D loops
                loop_effect = math.sin(time.time() * 6 + x * 0.2) * 0.5
                w_height_effect *= (1.0 + loop_effect)
            
            wall_height = min(HEIGHT, int((1.0 / distance) * HEIGHT * 0.5 * w_height_effect))
            
            wall_heights[x] = wall_height
            wall_types[x] = wall_type
            wall_effects[x] = special_effect
            
            # Determine wall color based on distance, type, and 4D position
            if wall_type == 1:  # Regular wall
                # Color based on 4D coordinate and current cube
                cube_hue = current_cube_id * 0.5
                r = 100 + int(w_coord * 100)
                g = 50 + int(math.sin(w_coord * math.pi * 2 + cube_hue) * 50)
                b = 150 + int(math.cos(w_coord * math.pi * 2 + cube_hue) * 50)
                base_color = (r, g, b)
            elif wall_type >= 20 and wall_type < 28:  # Connection to another room
                # Color based on connection ID
                hue = (wall_type - 20) / 8.0  # Normalize to 0-1
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
            elif special_effect == '4d_transition' or special_effect == '4d_loop':
                # Special colors for 4D transitions
                time_factor = time.time() * 3
                r = int(128 + 127 * math.sin(time_factor))
                g = int(128 + 127 * math.sin(time_factor + 2*math.pi/3))
                b = int(128 + 127 * math.sin(time_factor + 4*math.pi/3))
                base_color = (r, g, b)
            else:
                base_color = WALL_COLORS.get(wall_type, (150, 150, 150))
            
            # Apply distance shading
            shade = 1.0 - min(1.0, distance / max_distance)
            wall_color = tuple(int(c * shade) for c in base_color)
            
            # Apply 4D color shifting effect
            time_factor = time.time() * 2
            w_factor = math.sin(w_coord * math.pi * 4 + time_factor) * 0.3
            r = min(255, int(wall_color[0] * (1 + math.sin(time_factor + x * 0.1 + w_factor) * 0.3)))
            g = min(255, int(wall_color[1] * (1 + math.sin(time_factor + x * 0.05 + w_factor) * 0.3)))
            b = min(255, int(wall_color[2] * (1 + math.sin(time_factor + x * 0.02 + w_factor) * 0.3)))
            
            wall_colors[x] = (min(255, r), min(255, g), min(255, b))
    
    return wall_heights, wall_colors, wall_types, wall_effects

# Render a frame
# Pre-allocate surfaces for sky and floor
_sky_surface = pygame.Surface((WIDTH, HEIGHT//2))
_floor_surface = pygame.Surface((WIDTH, HEIGHT//2))

def _draw_gradient(surface, x, y_start, width, y_end, color_top, color_bottom, 
                  distortion, time_factor, max_wave, wave_freq, time_scale):
    """Draw a vertical gradient with optional wave distortion."""
    height = y_end - y_start
    if height <= 0:
        return
    
    # Create a temporary surface for the gradient
    temp_surface = pygame.Surface((width, height))
    
    # Draw the gradient
    for y in range(height):
        t = y / height
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        
        # Apply color distortion if needed
        if distortion > 0.1:
            r = min(255, max(0, int(r * (1 + math.sin(time_factor * 0.5 + y * 0.1) * 0.2 * distortion))))
            g = min(255, max(0, int(g * (1 + math.sin(time_factor * 0.3 + y * 0.1) * 0.2 * distortion))))
            b = min(255, max(0, int(b * (1 + math.sin(time_factor * 0.7 + y * 0.1) * 0.2 * distortion))))
        
        pygame.draw.line(temp_surface, (r, g, b), (0, y), (width, y))
    
    # Apply wave distortion if needed
    if distortion > 0.1:
        # Create a wave distortion effect
        wave_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            wave_offset = int(math.sin(y * wave_freq + time_factor * time_scale) * max_wave * distortion)
            if wave_offset != 0:
                # Only draw the visible portion
                src_x = max(0, -wave_offset)
                src_width = width - abs(wave_offset)
                if src_width > 0:
                    dest_x = max(0, wave_offset)
                    wave_surface.blit(temp_surface, (dest_x, y), 
                                    (src_x, y, src_width, 1))
            else:
                wave_surface.blit(temp_surface, (0, y), (0, y, width, 1))
        surface.blit(wave_surface, (x, y_start))
    else:
        surface.blit(temp_surface, (x, y_start))

def render_frame(player_x, player_y, player_angle, distortion_level=0.0):
    # Clear screen
    screen.fill((0, 0, 0))
    
    # Get reality level once
    reality_level = player_state['reality_level']
    reality_distortion = 1.0 - reality_level
    time_factor = time.time()
    
    # Apply gravity direction to the view angle if not in normal space
    adjusted_angle = player_angle
    if player_state['current_space'] == 'non_euclidean' and player_state['gravity_direction'] != 0:
        # Adjust the view angle based on gravity direction
        gravity_rotation = player_state['gravity_direction'] * (math.pi/2)  # 90 degrees per direction
        adjusted_angle = (player_angle + gravity_rotation) % (2 * math.pi)
    
    # Determine which raycasting function to use
    if player_state['in_normal_space']:
        # Use normal raycasting
        wall_heights, wall_colors, wall_types, wall_effects = raycast(player_x, player_y, adjusted_angle)
    elif player_state['current_space'] == 'hypercube':
        # Use hypercube raycasting
        wall_heights, wall_colors, wall_types, wall_effects = raycast_hypercube(
            player_state['hypercube_id'], 
            player_state['space_position'][0], 
            player_state['space_position'][1], 
            adjusted_angle
        )
    elif player_state['current_space'] == 'non_euclidean':
        # Use non-Euclidean raycasting
        wall_heights, wall_colors, wall_types, wall_effects = raycast_non_euclidean(
            player_state['space_position'][0], 
            player_state['space_position'][1], 
            adjusted_angle
        )
    else:
        # Fallback to normal raycasting
        wall_heights, wall_colors, wall_types, wall_effects = raycast(player_x, player_y, adjusted_angle)
    
    # Calculate sky and floor regions based on gravity
    if player_state['gravity_direction'] == 2:  # Upside down
        sky_start, sky_end = HEIGHT // 2, HEIGHT
        floor_start, floor_end = 0, HEIGHT // 2
    else:  # Normal orientation
        sky_start, sky_end = 0, HEIGHT // 2
        floor_start, floor_end = HEIGHT // 2, HEIGHT
    
    # Draw sky with gradient and distortion
    _draw_gradient(screen, 0, sky_start, WIDTH, sky_end, 
                  (0, 0, 50), (50, 50, 150), 
                  reality_distortion, time_factor, 10, 0.1, 2.0)
    
    _draw_gradient(screen, 0, floor_start, WIDTH, floor_end,
                  (50, 50, 50), (20, 20, 20),
                  reality_distortion, time_factor, 8, 0.1, 1.5)
    
    # Draw walls with adjusted rendering based on gravity direction
    for x in range(WIDTH):
        if wall_heights[x] > 0:
            # Calculate wall position based on gravity direction
            if player_state['gravity_direction'] == 0:  # Normal
                wall_top = (HEIGHT - wall_heights[x]) // 2
                wall_bottom = wall_top + wall_heights[x]
            elif player_state['gravity_direction'] == 2:  # Upside down
                wall_bottom = (HEIGHT + wall_heights[x]) // 2
                wall_top = wall_bottom - wall_heights[x]
            else:  # Sideways (1 = right, 3 = left)
                # For sideways gravity, we'll still render walls normally but with a visual tilt
                wall_top = (HEIGHT - wall_heights[x]) // 2
                wall_bottom = wall_top + wall_heights[x]
                
                # Apply a visual tilt based on gravity direction
                tilt_factor = 0.2 * reality_distortion  # More noticeable with lower reality
                if player_state['gravity_direction'] == 1:  # Right
                    wall_top += int(x * tilt_factor)
                    wall_bottom += int(x * tilt_factor)
                else:  # Left
                    wall_top += int((WIDTH - x) * tilt_factor)
                    wall_bottom += int((WIDTH - x) * tilt_factor)
            
            # Apply reality distortion to wall positions
            if reality_distortion > 0.1:
                distort_amount = int(math.sin(x * 0.1 + time.time() * 3) * 5 * reality_distortion)
                wall_top += distort_amount
                wall_bottom += distort_amount
            
            # Ensure walls stay within screen bounds
            wall_top = max(0, min(HEIGHT-1, wall_top))
            wall_bottom = max(0, min(HEIGHT-1, wall_bottom))
            
            # Draw the wall
            pygame.draw.line(screen, wall_colors[x], (x, wall_top), (x, wall_bottom), 1)
            
            # Apply special effects for certain wall types
            if wall_effects[x] == 'portal':
                # Draw portal effect (pulsing glow)
                glow_intensity = (math.sin(time.time() * 5) + 1) * 0.5  # 0 to 1
                glow_color = (int(100 * glow_intensity), int(200 * glow_intensity), int(255 * glow_intensity))
                pygame.draw.line(screen, glow_color, (x, wall_top), (x, wall_bottom), 1)
            elif wall_effects[x] == 'hypercube_exit':
                # Draw hypercube exit effect (rainbow pulse)
                hue = (time.time() * 0.5) % 1.0
                r = int(128 + 127 * math.sin(hue * 2 * math.pi))
                g = int(128 + 127 * math.sin(hue * 2 * math.pi + 2*math.pi/3))
                b = int(128 + 127 * math.sin(hue * 2 * math.pi + 4*math.pi/3))
                pygame.draw.line(screen, (r, g, b), (x, wall_top), (x, wall_bottom), 1)
            elif wall_effects[x] == 'non_euclidean_exit':
                # Draw non-Euclidean exit effect (pulsing magenta)
                pulse = (math.sin(time.time() * 3) + 1) * 0.5  # 0 to 1
                exit_color = (int(200 * pulse), int(50 * pulse), int(200 * pulse))
                pygame.draw.line(screen, exit_color, (x, wall_top), (x, wall_bottom), 1)
            elif wall_effects[x] == 'reality_distortion':
                # Draw reality distortion effect (shifting colors)
                time_factor = time.time() * 2
                r = int(128 + 127 * math.sin(time_factor + x * 0.1))
                g = int(128 + 127 * math.sin(time_factor + x * 0.05 + 2))
                b = int(128 + 127 * math.sin(time_factor + x * 0.02 + 4))
                pygame.draw.line(screen, (r, g, b), (x, wall_top), (x, wall_bottom), 1)
            elif wall_effects[x] == 'recursive_boundary':
                # Draw recursive boundary effect (pulsing with depth illusion)
                pulse = (math.sin(time.time() * 2.5) + 1) * 0.5  # 0 to 1
                depth = int(10 * pulse * reality_distortion)
                for d in range(depth):
                    d_factor = d / depth if depth > 0 else 0
                    boundary_color = (
                        int(200 * (1-d_factor)),
                        int(100 * (1-d_factor) + 100 * d_factor),
                        int(200 * d_factor)
                    )
                    offset = d * 2
                    if x + offset < WIDTH:
                        pygame.draw.line(screen, boundary_color, (x + offset, wall_top), (x + offset, wall_bottom), 1)
            elif wall_effects[x] == 'recursive_portal':
                # Draw recursive portal effect (spiral pattern)
                for i in range(5):
                    angle = time.time() * 3 + i * math.pi/3
                    spiral_x = int(math.cos(angle) * i * 2)
                    spiral_y = int(math.sin(angle) * i * 2)
                    portal_color = (
                        int(100 + 50 * math.sin(angle)),
                        int(100 + 50 * math.sin(angle + 2*math.pi/3)),
                        int(100 + 50 * math.sin(angle + 4*math.pi/3))
                    )
                    if 0 <= x + spiral_x < WIDTH and wall_top + spiral_y < wall_bottom:
                        y_pos = max(wall_top, min(wall_bottom, (wall_top + wall_bottom)//2 + spiral_y))
                        pygame.draw.circle(screen, portal_color, (x + spiral_x, y_pos), 1)
            elif wall_effects[x] == 'mirror':
                # Draw mirror effect (reflective shimmer)
                shimmer_intensity = (math.sin(time.time() * 7 + x * 0.1) + 1) * 0.5  # 0 to 1
                for y in range(wall_top, wall_bottom, 4):
                    shimmer_color = (
                        int(200 * shimmer_intensity),
                        int(200 * shimmer_intensity),
                        int(255 * shimmer_intensity)
                    )
                    shimmer_length = int(3 * shimmer_intensity)
                    if y + shimmer_length <= wall_bottom:
                        pygame.draw.line(screen, shimmer_color, (x, y), (x, y + shimmer_length), 1)

            elif wall_effects[x] == 'dimensional_shift':
                # Draw dimensional shift effect
                shift_height = wall_bottom - wall_top
                for i in range(0, shift_height, 4):
                    shift_y = wall_top + i
                    shift_color = (int(wall_colors[x][0] * 1.5) % 255, 
                                  int(wall_colors[x][1] * 1.5) % 255, 
                                  int(wall_colors[x][2] * 1.5) % 255)
                    pygame.draw.line(screen, shift_color, (x - 2, shift_y), (x + 2, shift_y), 1)
            elif wall_effects[x] == '4d_transition':
                # Draw 4D transition effect (cosmic ripple pattern)
                time_factor = time.time() * 3
                for i in range(0, wall_bottom - wall_top, 2):
                    y_pos = wall_top + i
                    ripple = math.sin(time_factor + i * 0.1) * 5
                    ripple_x = int(x + ripple)
                    
                    # Create shifting cosmic colors
                    r = int(128 + 127 * math.sin(time_factor + i * 0.05))
                    g = int(128 + 127 * math.sin(time_factor + i * 0.03 + 2*math.pi/3))
                    b = int(200 + 55 * math.sin(time_factor + i * 0.02 + 4*math.pi/3))
                    
                    if 0 <= ripple_x < WIDTH:
                        pygame.draw.line(screen, (r, g, b), (ripple_x, y_pos), (ripple_x + 1, y_pos), 1)
    
    # Draw mini-map if enabled
    if player_state['show_map']:
        # Draw map background
        map_size = 100
        cell_size = map_size // MAP_SIZE
        pygame.draw.rect(screen, (0, 0, 0, 128), (10, 10, map_size, map_size))
        
        # Draw map cells
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                if MAP[y, x] > 0:
                    color = WALL_COLORS.get(MAP[y, x], (200, 200, 200))
                    pygame.draw.rect(screen, color, 
                                    (10 + x * cell_size, 10 + y * cell_size, 
                                     cell_size, cell_size))
        
        # Draw player position
        player_map_x = 10 + int(player_x * cell_size)
        player_map_y = 10 + int(player_y * cell_size)
        pygame.draw.circle(screen, (255, 255, 0), (player_map_x, player_map_y), 2)
        
        # Draw player direction
        dir_x = math.cos(player_angle) * 5
        dir_y = math.sin(player_angle) * 5
        pygame.draw.line(screen, (255, 255, 0), 
                        (player_map_x, player_map_y), 
                        (player_map_x + dir_x, player_map_y + dir_y), 1)
    
    # Draw FPS counter
    fps_text = font.render(f'FPS: {int(clock.get_fps())}', True, (255, 255, 255))
    screen.blit(fps_text, (10, HEIGHT - 30))
    
    # Draw player state info
    if not player_state['in_normal_space']:
        if player_state['current_space'] == 'non_euclidean':
            space_text = font.render('Non-Euclidean Space', True, (200, 100, 200))
        elif player_state['current_space'] == 'hypercube':
            space_text = font.render(f'Hypercube Room {player_state["hypercube_room"]}', True, (100, 100, 255))
        screen.blit(space_text, (WIDTH - 200, HEIGHT - 30))
    
    # Update the display
    pygame.display.flip()

# Main game loop
def main():
    # Initialize player position and angle
    player_x, player_y = 1.5, 1.5
    player_angle = 0.0
    player_state['in_normal_space'] = True
    player_state['reality_level'] = 1.0
    player_state['gravity_direction'] = 0  # 0: down, 1: right, 2: up, 3: left
    player_state['show_map'] = True
    
    # Movement speed - increased for better responsiveness
    move_speed = 0.1
    rot_speed = 0.03
    
    # Mouse look settings
    pygame.mouse.set_visible(False)  # Hide the mouse cursor
    pygame.event.set_grab(True)  # Capture the mouse
    mouse_sensitivity = 0.002  # Adjust sensitivity as needed
    last_mouse_pos = pygame.mouse.get_pos()[0]
    
    # Game loop
    running = True
    while running:
        # Limit frame rate
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        fps = clock.get_fps()
        
        # Adjust movement speed based on framerate for consistent movement
        frame_move_speed = move_speed * (60 / max(fps, 1)) if fps > 0 else move_speed
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    # Toggle mini-map
                    player_state['show_map'] = not player_state['show_map']
                elif event.key == pygame.K_ESCAPE:
                    # Release mouse on escape
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                elif event.key == pygame.K_TAB:
                    # Re-capture mouse on tab
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                elif event.key == pygame.K_SPACE:
                    # Reset player position and state
                    player_x, player_y = 1.5, 1.5
                    player_angle = 0.0
                    player_state['in_normal_space'] = True
                    player_state['current_space'] = None
                    player_state['space_position'] = [0, 0]
                    player_state['non_euclidean_map_id'] = None
                    player_state['hypercube_room'] = 0
                    player_state['current_hypercube_id'] = None
                    player_state['reality_level'] = 1.0
                    player_state['gravity_direction'] = 0
        
        # Get keyboard input
        keys = pygame.key.get_pressed()
        
        # Handle exit
        if keys[pygame.K_q] and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
            running = False
        
        # Mouse look
        if pygame.event.get_grab():
            mouse_pos = pygame.mouse.get_pos()[0]
            mouse_movement = mouse_pos - last_mouse_pos
            player_angle += mouse_movement * mouse_sensitivity
            
            # Reset mouse position to center to allow continuous rotation
            pygame.mouse.set_pos((WIDTH // 2, HEIGHT // 2))
            last_mouse_pos = WIDTH // 2
        
        # Calculate movement direction based on gravity
        forward_x = math.cos(player_angle)
        forward_y = math.sin(player_angle)
        right_x = math.cos(player_angle + math.pi/2)
        right_y = math.sin(player_angle + math.pi/2)
        
        # Apply gravity direction to movement
        if player_state['gravity_direction'] == 1:  # Right
            forward_x, forward_y = forward_y, -forward_x
            right_x, right_y = right_y, -right_x
        elif player_state['gravity_direction'] == 2:  # Up
            forward_x, forward_y = -forward_x, -forward_y
            right_x, right_y = -right_x, -right_y
        elif player_state['gravity_direction'] == 3:  # Left
            forward_x, forward_y = -forward_y, forward_x
            right_x, right_y = -right_y, right_x
        
        # Handle movement with improved WASD controls
        new_x, new_y = player_x, player_y
        movement_occurred = False
        
        # Forward/backward movement
        if keys[pygame.K_w]:
            new_x += forward_x * frame_move_speed
            new_y += forward_y * frame_move_speed
            movement_occurred = True
        if keys[pygame.K_s]:
            new_x -= forward_x * frame_move_speed
            new_y -= forward_y * frame_move_speed
            movement_occurred = True
        
        # Strafe left/right movement
        if keys[pygame.K_a]:
            new_x -= right_x * frame_move_speed
            new_y -= right_y * frame_move_speed
            movement_occurred = True
        if keys[pygame.K_d]:
            new_x += right_x * frame_move_speed
            new_y += right_y * frame_move_speed
            movement_occurred = True
        
        # Handle rotation with keyboard (as backup to mouse)
        if keys[pygame.K_LEFT]:
            player_angle -= rot_speed
        if keys[pygame.K_RIGHT]:
            player_angle += rot_speed
        
        # Check if we can move to the new position
        map_x, map_y = int(new_x), int(new_y)
        
        # Handle collision detection and special wall interactions
        if player_state['in_normal_space']:
            # Normal space collision detection
            if 0 <= map_x < MAP_SIZE and 0 <= map_y < MAP_SIZE:
                wall_type = MAP[map_y, map_x]
                
                if wall_type == 0:  # Empty space
                    player_x, player_y = new_x, new_y
                elif wall_type == 2:  # Portal
                    # Find which portal we hit
                    for portal_pair in PORTALS:
                        for i, portal in enumerate(portal_pair):
                            if map_x == portal['x'] and map_y == portal['y']:
                                # We hit a portal - teleport to the linked portal
                                linked_idx = portal['linked_to']
                                linked_portal = portal_pair[linked_idx]
                                
                                # Calculate the offset to apply
                                offset_x = linked_portal['x'] - portal['x']
                                offset_y = linked_portal['y'] - portal['y']
                                
                                # Calculate rotation to apply
                                rotation = (linked_portal['facing'] - portal['facing']) * math.pi/2
                                
                                # Apply the portal transformation
                                player_x = new_x + offset_x
                                player_y = new_y + offset_y
                                
                                # Apply rotation to player angle if portals face different directions
                                if rotation != 0:
                                    player_angle += rotation
                                break
                elif wall_type == 3:  # Non-Euclidean space entrance
                    # Find the non-Euclidean space we're entering
                    for space in NON_EUCLIDEAN_SPACES:
                        if space['entrance'] == (map_x, map_y):
                            # Enter non-Euclidean space
                            player_state['in_normal_space'] = False
                            player_state['current_space'] = 'non_euclidean'
                            player_state['non_euclidean_map_id'] = (map_x, map_y)
                            player_state['space_position'] = [space['start_x'], space['start_y']]
                            break
                elif wall_type == 6:  # 4D hypercube entrance
                    # Find the hypercube we're entering
                    for cube in HYPERCUBES:
                        if cube['entrance'] == (map_x, map_y):
                            # Enter hypercube
                            player_state['in_normal_space'] = False
                            player_state['current_space'] = 'hypercube'
                            player_state['current_hypercube_id'] = (map_x, map_y)
                            player_state['hypercube_room'] = 0  # Start in room 0
                            player_state['space_position'] = [cube['start_x'], cube['start_y']]
                            break
                elif wall_type == 4:  # Reality distortion wall
                    # Decrease reality level when approaching this wall
                    dx = new_x - player_x
                    dy = new_y - player_y
                    approaching = (dx * forward_x + dy * forward_y) > 0
                    
                    if approaching:
                        player_state['reality_level'] = max(0.5, player_state['reality_level'] - 0.01)
                    else:
                        player_state['reality_level'] = min(1.0, player_state['reality_level'] + 0.01)
                elif wall_type == 5:  # Perspective shift wall
                    # Change gravity direction when approaching this wall
                    dx = new_x - player_x
                    dy = new_y - player_y
                    approaching = (dx * forward_x + dy * forward_y) > 0
                    
                    if approaching and keys[pygame.K_e]:  # Press E to interact
                        # Rotate gravity direction
                        player_state['gravity_direction'] = (player_state['gravity_direction'] + 1) % 4
        else:
            # Handle movement in special spaces
            if player_state['current_space'] == 'non_euclidean':
                # Find which non-Euclidean space we're in
                current_space = None
                for space in NON_EUCLIDEAN_SPACES:
                    if player_state['non_euclidean_map_id'] == space['entrance']:
                        current_space = space
                        break
                
                if current_space:
                    inner_map = current_space['map']
                    inner_width = current_space['width']
                    inner_height = current_space['height']
                    mechanics = current_space.get('mechanics', {})
                    
                    # Apply time dilation to movement
                    time_dilation = mechanics.get('time_dilation', 1.0)
                    if time_dilation != 1.0:
                        # Adjust movement speed based on time dilation
                        movement_scale = 1.0 / time_dilation
                        new_x = player_state['space_position'][0] + (new_x - player_state['space_position'][0]) * movement_scale
                        new_y = player_state['space_position'][1] + (new_y - player_state['space_position'][1]) * movement_scale
                    
                    # Apply recursive scaling if enabled
                    in_recursive_room = False
                    recursive_scale = 1.0
                    if mechanics.get('recursive_scaling', False) and 'recursive_rooms' in current_space:
                        # Check if we're in a recursive room
                        for room in current_space['recursive_rooms']:
                            rx, ry, size, scale = room['x'], room['y'], room['size'], room.get('scale', 0.5)
                            
                            # Check if player is in this room
                            if rx <= new_x < rx + size and ry <= new_y < ry + size:
                                in_recursive_room = True
                                recursive_scale = scale
                                
                                # Apply scaling effect to movement within the recursive room
                                # This creates a feeling of moving slower/faster in recursive spaces
                                center_x, center_y = rx + size/2, ry + size/2
                                dx = new_x - center_x
                                dy = new_y - center_y
                                
                                # Scale movement based on distance from center
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist > 0:
                                    scale_factor = 1.0 - (dist / (size/2)) * (1.0 - recursive_scale)
                                    dx *= scale_factor
                                    dy *= scale_factor
                                    new_x = center_x + dx
                                    new_y = center_y + dy
                                break
                    
                    # Apply mirror dimension effects if enabled
                    if current_space.get('mirror_dimension', False):
                        # Check if crossing the diagonal mirror line
                        old_x, old_y = player_state['space_position']
                        
                        # Detect if we're crossing a diagonal mirror
                        if (old_x < old_y and new_x > new_y) or (old_x > old_y and new_x < new_y):
                            # Swap x and y coordinates to create mirror effect
                            new_x, new_y = new_y, new_x
                            
                            # Also rotate the player's view
                            player_angle = (player_angle + math.pi/2) % (2 * math.pi)
                            
                            # Visual effect for mirror crossing
                            player_state['reality_level'] = max(0.7, player_state['reality_level'] - 0.05)
                    
                    map_x, map_y = int(new_x), int(new_y)
                    if 0 <= map_x < inner_width and 0 <= map_y < inner_height:
                        wall_type = inner_map[map_y, map_x]
                        
                        if wall_type == 0:  # Empty space
                            player_state['space_position'] = [new_x, new_y]
                            
                            # Apply gravity flux if enabled
                            if mechanics.get('gravity_flux', False):
                                # Change gravity direction based on position
                                center_x, center_y = inner_width / 2, inner_height / 2
                                dist_from_center = math.sqrt((new_x - center_x)**2 + (new_y - center_y)**2)
                                
                                if dist_from_center > inner_width / 4:
                                    # Calculate angle to center
                                    angle_to_center = math.atan2(new_y - center_y, new_x - center_x)
                                    
                                    # Determine gravity direction (pointing toward center)
                                    gravity_angle = (angle_to_center + math.pi) % (2 * math.pi)
                                    gravity_direction = int((gravity_angle / (math.pi/2)) % 4)
                                    
                                    # Only update if it's different to avoid constant changes
                                    if gravity_direction != player_state['gravity_direction']:
                                        player_state['gravity_direction'] = gravity_direction
                                        # Visual effect for gravity change
                                        player_state['reality_level'] = max(0.8, player_state['reality_level'] - 0.03)
                            
                            # Apply reality bleed in certain areas
                            if 'reality_bleed' in mechanics:
                                # Reality level decreases more in the center of the space
                                center_x, center_y = inner_width / 2, inner_height / 2
                                dist_from_center = math.sqrt((new_x - center_x)**2 + (new_y - center_y)**2)
                                max_dist = math.sqrt((inner_width/2)**2 + (inner_height/2)**2)
                                
                                # Stronger effect closer to center
                                center_factor = 1.0 - (dist_from_center / max_dist)
                                reality_target = mechanics['reality_bleed'] * (0.8 + 0.2 * center_factor)
                                player_state['reality_level'] = max(reality_target, player_state['reality_level'] - 0.001)
                            
                            # Apply perspective inversion in certain areas
                            if mechanics.get('perspective_inversion', False) and player_state['reality_level'] < 0.8:
                                # Check if we're in a "perspective inversion zone"
                                inversion_zones = [
                                    (inner_width/4, inner_height/4, inner_width/8),
                                    (3*inner_width/4, inner_height/4, inner_width/8),
                                    (inner_width/4, 3*inner_height/4, inner_width/8),
                                    (3*inner_width/4, 3*inner_height/4, inner_width/8)
                                ]
                                
                                for zone_x, zone_y, zone_radius in inversion_zones:
                                    dist = math.sqrt((new_x - zone_x)**2 + (new_y - zone_y)**2)
                                    if dist < zone_radius:
                                        # We're in an inversion zone - randomly invert perspective
                                        if random.random() < 0.01:  # 1% chance per frame
                                            # Invert the player's view
                                            player_angle = (player_angle + math.pi) % (2 * math.pi)
                                            # Visual effect for perspective inversion
                                            player_state['reality_level'] = max(0.6, player_state['reality_level'] - 0.1)
                        elif wall_type == 3:  # Exit back to normal space
                            # Return to normal space
                            player_state['in_normal_space'] = True
                            player_state['current_space'] = None
                            player_state['reality_level'] = min(1.0, player_state['reality_level'] + 0.2)  # Restore some reality
                            
                            # Calculate position in normal space
                            exit_x, exit_y = current_space['exit_pos']
                            player_x = exit_x + 0.5
                            player_y = exit_y + 0.5
                        elif wall_type == 9:  # Recursive boundary
                            # If recursive scaling is enabled, allow passing through
                            if mechanics.get('recursive_scaling', False) and in_recursive_room:
                                player_state['space_position'] = [new_x, new_y]
                                # Visual effect for crossing boundary
                                player_state['reality_level'] = max(0.5, player_state['reality_level'] - 0.05)
                        elif wall_type == 10:  # Recursive portal
                            # Teleport to a random recursive room
                            if 'recursive_rooms' in current_space and len(current_space['recursive_rooms']) > 0:
                                target_room = random.choice(current_space['recursive_rooms'])
                                tx, ty, size = target_room['x'], target_room['y'], target_room['size']
                                
                                # Place player in the center of the target room
                                player_state['space_position'] = [tx + size/2, ty + size/2]
                                
                                # Visual effect for teleportation
                                player_state['reality_level'] = max(0.6, player_state['reality_level'] - 0.1)
                        elif wall_type == 11:  # Mirror
                            # Reflect the player's movement
                            old_x, old_y = player_state['space_position']
                            
                            # Determine the normal vector of the mirror surface
                            normal_x, normal_y = 0, 0
                            if map_x == map_y:  # Diagonal mirror
                                normal_x = normal_y = 0.7071  # 1/sqrt(2)
                            else:  # Random mirror fragment
                                # Randomize the normal but keep it consistent
                                random.seed(map_x * 1000 + map_y)
                                angle = random.random() * 2 * math.pi
                                normal_x = math.cos(angle)
                                normal_y = math.sin(angle)
                            
                            # Calculate movement vector
                            move_x = new_x - old_x
                            move_y = new_y - old_y
                            
                            # Calculate reflection
                            dot = 2 * (move_x * normal_x + move_y * normal_y)
                            reflect_x = move_x - dot * normal_x
                            reflect_y = move_y - dot * normal_y
                            
                            # Apply reflection
                            player_state['space_position'] = [old_x + reflect_x, old_y + reflect_y]
                            
                            # Also reflect the player's view angle
                            angle_normal = math.atan2(normal_y, normal_x)
                            angle_diff = player_angle - angle_normal
                            player_angle = angle_normal - angle_diff
                            
                            # Visual effect for reflection
                            player_state['reality_level'] = max(0.7, player_state['reality_level'] - 0.05)
            elif player_state['current_space'] == 'hypercube':
                # Find the current hypercube
                current_cube = None
                for cube in HYPERCUBES:
                    if player_state['current_hypercube_id'] == cube['entrance']:
                        current_cube = cube
                        break
                
                if current_cube:
                    # Get the current room
                    current_room = current_cube['rooms'][player_state['hypercube_room']]
                    room_map = current_room['map']
                    room_size = current_room['size']
                    
                    map_x, map_y = int(new_x), int(new_y)
                    
                    # Check for 4D transitions at boundaries
                    # First check if we're already at a boundary (for 4D connection walls)
                    face_at_boundary = -1
                    if map_y == 0: face_at_boundary = 0  # North
                    elif map_x == room_size-1: face_at_boundary = 1  # East
                    elif map_y == room_size-1: face_at_boundary = 2  # South
                    elif map_x == 0: face_at_boundary = 3  # West
                    
                    # Then check if we're crossing a boundary
                    face_crossing = -1
                    if map_y < 0: face_crossing = 0  # North
                    elif map_x >= room_size: face_crossing = 1  # East
                    elif map_y >= room_size: face_crossing = 2  # South
                    elif map_x < 0: face_crossing = 3  # West
                    
                    # Use either the boundary face or the crossing face
                    face = face_at_boundary if face_at_boundary != -1 else face_crossing
                    
                    # Check if this face has a 4D connection
                    if face in current_room.get('4d_connections', {}):
                        # 4D transition to another hypercube/room
                        connection = current_room['4d_connections'][face]
                        target_cube_id = connection['cube']
                        target_room_id = connection['room']
                        target_face = connection['face']
                        rotation = connection['rotation']
                        
                        # Calculate new position in the target room
                        target_cube = HYPERCUBES[target_cube_id]
                        target_room = target_cube['rooms'][target_room_id]
                        target_size = target_room['size']
                        
                        # Map coordinates from one face to the opposite face
                        if face == 0:  # North to South
                            new_pos_x = new_x % room_size  # Keep x-coordinate
                            new_pos_y = target_size - 0.1  # Place near south edge
                        elif face == 1:  # East to West
                            new_pos_x = 0.1  # Place near west edge
                            new_pos_y = new_y % room_size  # Keep y-coordinate
                        elif face == 2:  # South to North
                            new_pos_x = new_x % room_size  # Keep x-coordinate
                            new_pos_y = 0.1  # Place near north edge
                        elif face == 3:  # West to East
                            new_pos_x = target_size - 0.1  # Place near east edge
                            new_pos_y = new_y % room_size  # Keep y-coordinate
                        
                        # Apply rotation based on the connection
                        for _ in range(rotation):
                            new_pos_x, new_pos_y = target_size - 1 - new_pos_y, new_pos_x
                        
                        # Apply rotation to player angle
                        new_angle = player_angle
                        for _ in range(rotation):
                            new_angle += math.pi/2  # Rotate 90 degrees for each rotation step
                        
                        # Update player state to the new hypercube/room
                        player_state['current_hypercube_id'] = target_cube['entrance']
                        player_state['hypercube_room'] = target_room_id
                        player_state['space_position'] = [new_pos_x, new_pos_y]
                        player_angle = new_angle % (2 * math.pi)  # Normalize angle
                        
                        # Apply a slight visual distortion effect during transition
                        player_state['reality_level'] = max(0.8, player_state['reality_level'] - 0.05)
                        
                        # Show a message about the transition
                        print(f"4D transition to hypercube {target_cube_id}, room {target_room_id}")
                        continue  # Skip the rest of the movement handling
                    
                    # Regular room movement
                    if 0 <= map_x < room_size and 0 <= map_y < room_size:
                        wall_type = room_map[map_y, map_x]
                        
                        if wall_type == 0:  # Empty space
                            player_state['space_position'] = [new_x, new_y]
                        elif wall_type == 30:  # 4D connection wall
                            # Determine which face this wall is on
                            face = -1
                            if map_y == 0: face = 0  # North
                            elif map_x == room_size-1: face = 1  # East
                            elif map_y == room_size-1: face = 2  # South
                            elif map_x == 0: face = 3  # West
                            
                            # If we couldn't determine the face, try to find the closest face
                            if face == -1:
                                # Find the closest wall
                                dist_to_north = map_y
                                dist_to_east = room_size - 1 - map_x
                                dist_to_south = room_size - 1 - map_y
                                dist_to_west = map_x
                                
                                min_dist = min(dist_to_north, dist_to_east, dist_to_south, dist_to_west)
                                if min_dist == dist_to_north: face = 0
                                elif min_dist == dist_to_east: face = 1
                                elif min_dist == dist_to_south: face = 2
                                elif min_dist == dist_to_west: face = 3
                            
                            # Check if this face has a 4D connection
                            if face in current_room.get('4d_connections', {}):
                                # 4D transition to another hypercube/room
                                connection = current_room['4d_connections'][face]
                                target_cube_id = connection['cube']
                                target_room_id = connection['room']
                                target_face = connection['face']
                                rotation = connection['rotation']
                                
                                # Calculate new position in the target room
                                target_cube = HYPERCUBES[target_cube_id]
                                target_room = target_cube['rooms'][target_room_id]
                                target_size = target_room['size']
                                
                                # Map coordinates from one face to the opposite face
                                if face == 0:  # North to South
                                    new_pos_x = new_x % room_size  # Keep x-coordinate
                                    new_pos_y = target_size - 0.1  # Place near south edge
                                elif face == 1:  # East to West
                                    new_pos_x = 0.1  # Place near west edge
                                    new_pos_y = new_y % room_size  # Keep y-coordinate
                                elif face == 2:  # South to North
                                    new_pos_x = new_x % room_size  # Keep x-coordinate
                                    new_pos_y = 0.1  # Place near north edge
                                elif face == 3:  # West to East
                                    new_pos_x = target_size - 0.1  # Place near east edge
                                    new_pos_y = new_y % room_size  # Keep y-coordinate
                                
                                # Apply rotation based on the connection
                                for _ in range(rotation):
                                    new_pos_x, new_pos_y = target_size - 1 - new_pos_y, new_pos_x
                                
                                # Apply rotation to player angle
                                new_angle = player_angle
                                for _ in range(rotation):
                                    new_angle += math.pi/2  # Rotate 90 degrees for each rotation step
                                
                                # Update player state to the new hypercube/room
                                player_state['current_hypercube_id'] = target_cube['entrance']
                                player_state['hypercube_room'] = target_room_id
                                player_state['space_position'] = [new_pos_x, new_pos_y]
                                player_angle = new_angle % (2 * math.pi)  # Normalize angle
                                
                                # Apply a cosmic visual distortion effect during transition
                                player_state['reality_level'] = max(0.7, player_state['reality_level'] - 0.1)
                                
                                # Show a message about the transition
                                print(f"4D transition to hypercube {target_cube_id}, room {target_room_id} through face {face}")
                        elif wall_type == 6:  # Exit back to normal space
                            # Return to normal space
                            player_state['in_normal_space'] = True
                            player_state['current_space'] = None
                            
                            # Calculate position in normal space
                            exit_x, exit_y = current_cube['exit_pos']
                            player_x = exit_x + 0.5
                            player_y = exit_y + 0.5
                        elif wall_type >= 20 and wall_type < 28:  # Connections to other rooms
                            # Move to another room in the hypercube
                            connection_id = wall_type - 20
                            if connection_id in current_room['connections']:
                                target_room = current_room['connections'][connection_id]
                                player_state['hypercube_room'] = target_room
                                
                                # Set position in the new room
                                new_room = current_cube['rooms'][target_room]
                                player_state['space_position'] = [new_room['start_x'], new_room['start_y']]
        
        # Get current position based on space
        if player_state['in_normal_space']:
            current_x, current_y = player_x, player_y
        else:
            current_x, current_y = player_state['space_position']
        
        # Render the frame
        distortion_level = 0.0
        if player_state['reality_level'] < 1.0:
            distortion_level = (1.0 - player_state['reality_level']) * 0.5
        
        render_frame(current_x, current_y, player_angle, distortion_level)
    
    # Quit pygame
    pygame.quit()

# Run the game
if __name__ == '__main__':
    main()
