import random
import math
import numpy as np

class NonEuclideanMap:
    """
    Generates and manages non-Euclidean maps with impossible spaces,
    portals, and other reality-bending features.
    """
    
    def __init__(self, width=16, height=16, cell_size=64):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Initialize empty map (0 = empty, 1 = wall)
        self.grid = np.ones((height, width), dtype=int)
        
        # Portal connections (x1, y1, x2, y2) pairs
        self.portals = []
        
        # Impossible spaces (regions that are bigger on the inside)
        self.impossible_spaces = []
        
        # Reality distortion fields (x, y, radius, strength)
        self.distortion_fields = []
        
        # Wall textures assignment
        self.wall_textures = np.zeros((height, width), dtype=int)
        
        # Generate a basic map
        self.generate_basic_map()
        
    def generate_basic_map(self):
        """Generate a basic map with rooms and corridors"""
        # Clear the interior, keeping the border walls
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                self.grid[y][x] = 0
        
        # Add some random walls to create rooms
        for _ in range(20):
            if random.random() < 0.5:
                # Horizontal wall
                x = random.randint(1, self.width - 3)
                y = random.randint(1, self.height - 2)
                length = random.randint(3, 8)
                for i in range(min(length, self.width - x - 1)):
                    self.grid[y][x + i] = 1
            else:
                # Vertical wall
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 3)
                length = random.randint(3, 8)
                for i in range(min(length, self.height - y - 1)):
                    self.grid[y + i][x] = 1
        
        # Ensure there are some openings in the walls
        self._create_openings()
        
        # Add some portals
        self._add_portals(3)
        
        # Add some impossible spaces
        self._add_impossible_spaces(2)
        
        # Add distortion fields
        self._add_distortion_fields(4)
        
        # Assign wall textures
        self._assign_wall_textures()
    
    def _create_openings(self):
        """Create openings in walls to ensure the map is traversable"""
        # Find walls that aren't border walls
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 1:
                    # Check if this is part of a horizontal wall
                    if (x > 1 and x < self.width - 2 and 
                        self.grid[y][x-1] == 1 and self.grid[y][x+1] == 1):
                        # 20% chance to create an opening
                        if random.random() < 0.2:
                            self.grid[y][x] = 0
                    
                    # Check if this is part of a vertical wall
                    elif (y > 1 and y < self.height - 2 and 
                          self.grid[y-1][x] == 1 and self.grid[y+1][x] == 1):
                        # 20% chance to create an opening
                        if random.random() < 0.2:
                            self.grid[y][x] = 0
    
    def _add_portals(self, count):
        """Add portals that connect different parts of the map"""
        for _ in range(count):
            # Find two empty spaces that are far apart
            attempts = 0
            while attempts < 50:
                x1 = random.randint(1, self.width - 2)
                y1 = random.randint(1, self.height - 2)
                x2 = random.randint(1, self.width - 2)
                y2 = random.randint(1, self.height - 2)
                
                # Check if both locations are empty
                if self.grid[y1][x1] == 0 and self.grid[y2][x2] == 0:
                    # Check if they're far enough apart
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    if distance > 5:
                        self.portals.append((x1, y1, x2, y2))
                        break
                
                attempts += 1
    
    def _add_impossible_spaces(self, count):
        """Add spaces that are bigger on the inside"""
        for _ in range(count):
            # Find a suitable location for an impossible space
            attempts = 0
            while attempts < 50:
                x = random.randint(2, self.width - 3)
                y = random.randint(2, self.height - 3)
                
                # Check if this location and surroundings are empty
                if (self.grid[y][x] == 0 and
                    self.grid[y-1][x] == 0 and self.grid[y+1][x] == 0 and
                    self.grid[y][x-1] == 0 and self.grid[y][x+1] == 0):
                    
                    # Create an impossible space
                    inner_width = random.randint(3, 5)
                    inner_height = random.randint(3, 5)
                    inner_grid = np.zeros((inner_height, inner_width), dtype=int)
                    
                    # Add walls around the inner space
                    for iy in range(inner_height):
                        for ix in range(inner_width):
                            if (iy == 0 or iy == inner_height - 1 or
                                ix == 0 or ix == inner_width - 1):
                                inner_grid[iy][ix] = 1
                    
                    # Add some random walls inside
                    for _ in range(inner_width * inner_height // 4):
                        ix = random.randint(1, inner_width - 2)
                        iy = random.randint(1, inner_height - 2)
                        inner_grid[iy][ix] = 1
                    
                    # Create an entrance/exit
                    entrance_side = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
                    if entrance_side == 0:
                        inner_grid[0][inner_width // 2] = 0
                    elif entrance_side == 1:
                        inner_grid[inner_height // 2][inner_width - 1] = 0
                    elif entrance_side == 2:
                        inner_grid[inner_height - 1][inner_width // 2] = 0
                    else:
                        inner_grid[inner_height // 2][0] = 0
                    
                    self.impossible_spaces.append({
                        'x': x,
                        'y': y,
                        'grid': inner_grid,
                        'width': inner_width,
                        'height': inner_height,
                        'entrance_side': entrance_side
                    })
                    break
                
                attempts += 1
    
    def _add_distortion_fields(self, count):
        """Add reality distortion fields that bend rays"""
        for _ in range(count):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            radius = random.uniform(1.5, 3.0)
            strength = random.uniform(0.2, 0.8)
            field_type = random.choice(['vortex', 'expansion', 'sine_wave'])
            
            self.distortion_fields.append({
                'x': x,
                'y': y,
                'radius': radius,
                'strength': strength,
                'type': field_type
            })
    
    def _assign_wall_textures(self):
        """Assign different textures to walls"""
        # Assign a base texture to all walls
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:
                    self.wall_textures[y][x] = 0  # Default texture
        
        # Assign different textures to some walls
        for _ in range(10):
            # Pick a random wall
            attempts = 0
            while attempts < 50:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                
                if self.grid[y][x] == 1:
                    # Assign a random texture
                    texture = random.randint(1, 3)  # Assuming we have 4 textures (0-3)
                    
                    # Extend the texture to adjacent walls
                    size = random.randint(1, 3)
                    for dy in range(-size, size + 1):
                        for dx in range(-size, size + 1):
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < self.width and 0 <= ny < self.height and
                                self.grid[ny][nx] == 1):
                                self.wall_textures[ny][nx] = texture
                    
                    break
                
                attempts += 1
    
    def is_wall(self, x, y):
        """Check if a world position is inside a wall"""
        # Convert world coordinates to grid coordinates
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        
        # Check if out of bounds
        if grid_x < 0 or grid_x >= self.width or grid_y < 0 or grid_y >= self.height:
            return True
        
        # Check if inside a wall
        return self.grid[grid_y][grid_x] == 1
    
    def get_texture(self, x, y):
        """Get the texture ID for a wall at the given position"""
        # Convert world coordinates to grid coordinates
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        
        # Check if out of bounds
        if grid_x < 0 or grid_x >= self.width or grid_y < 0 or grid_y >= self.height:
            return 0  # Default texture
        
        # Return the texture ID
        return self.wall_textures[grid_y][grid_x]
    
    def check_portal(self, x, y):
        """Check if a world position is near a portal and return the destination"""
        # Convert world coordinates to grid coordinates
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        
        # Check each portal
        for x1, y1, x2, y2 in self.portals:
            if grid_x == x1 and grid_y == y1:
                # Return the destination in world coordinates
                return (x2 * self.cell_size + self.cell_size / 2, 
                        y2 * self.cell_size + self.cell_size / 2)
            elif grid_x == x2 and grid_y == y2:
                # Portals work both ways
                return (x1 * self.cell_size + self.cell_size / 2, 
                        y1 * self.cell_size + self.cell_size / 2)
        
        # Check if inside an impossible space entrance
        for space in self.impossible_spaces:
            if grid_x == space['x'] and grid_y == space['y']:
                # Determine entry point to impossible space
                if space['entrance_side'] == 0:  # top
                    return (space['x'] * self.cell_size + self.cell_size / 2,
                            space['y'] * self.cell_size + self.cell_size * 0.1)
                elif space['entrance_side'] == 1:  # right
                    return (space['x'] * self.cell_size + self.cell_size * 0.9,
                            space['y'] * self.cell_size + self.cell_size / 2)
                elif space['entrance_side'] == 2:  # bottom
                    return (space['x'] * self.cell_size + self.cell_size / 2,
                            space['y'] * self.cell_size + self.cell_size * 0.9)
                else:  # left
                    return (space['x'] * self.cell_size + self.cell_size * 0.1,
                            space['y'] * self.cell_size + self.cell_size / 2)
        
        return None
    
    def get_distortion(self, x, y, angle, distance):
        """Get ray distortion at a given position"""
        # Convert world coordinates to grid coordinates
        grid_x = x / self.cell_size
        grid_y = y / self.cell_size
        
        # Performance optimization: early return if no distortion fields
        if not self.distortion_fields:
            return 0.0
            
        # Performance optimization: only check closest field
        closest_field = None
        min_dist = float('inf')
        
        # Find the closest field
        for field in self.distortion_fields:
            dx = grid_x - field['x']
            dy = grid_y - field['y']
            dist_to_field = dx*dx + dy*dy  # Avoid sqrt for performance
            
            if dist_to_field < min_dist:
                min_dist = dist_to_field
                closest_field = field
        
        # If no field is close enough, return 0
        if not closest_field or min_dist > closest_field['radius'] * closest_field['radius']:
            return 0.0
            
        # Now calculate distortion for the closest field only
        field = closest_field
        dx = grid_x - field['x']
        dy = grid_y - field['y']
        dist_to_field = math.sqrt(min_dist)  # Now use sqrt
        
        # Calculate influence based on distance (stronger closer to center)
        influence = 1.0 - (dist_to_field / field['radius'])
        
        # Apply different distortion types
        if field['type'] == 'vortex':
            # Vortex effect - rays curve around the center
            angle_to_center = math.atan2(dy, dx)
            distortion = math.sin(angle_to_center - angle) * influence * field['strength']
        
        elif field['type'] == 'expansion':
            # Expansion effect - rays bend away from or toward center
            distortion = math.sin(distance * 0.1) * influence * field['strength']
        
        else:  # sine_wave or default
            # Sine wave distortion
            distortion = math.sin(distance * 0.2 + dist_to_field * 2) * influence * field['strength']
        
        return distortion
    
    # Cache for impossible space checks
    _impossible_space_cache = {}
    _cache_hits = 0
    _cache_misses = 0
    _cache_size_limit = 1000  # Limit cache size to prevent memory issues
    
    def is_in_impossible_space(self, x, y):
        """Check if a position is inside an impossible space and handle accordingly"""
        # Performance optimization: early return if no impossible spaces
        if not self.impossible_spaces:
            return False
            
        # Convert world coordinates to grid coordinates
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        
        # Check cache first
        cache_key = (grid_x, grid_y, int(x) % self.cell_size, int(y) % self.cell_size)
        if cache_key in self._impossible_space_cache:
            self._cache_hits += 1
            return self._impossible_space_cache[cache_key]
            
        self._cache_misses += 1
        
        # Check each impossible space
        for space in self.impossible_spaces:
            if grid_x == space['x'] and grid_y == space['y']:
                # We're in an impossible space - need to map to the inner coordinates
                
                # Calculate relative position within the cell (0.0 to 1.0)
                rel_x = (x % self.cell_size) / self.cell_size
                rel_y = (y % self.cell_size) / self.cell_size
                
                # Map to inner grid coordinates
                inner_x = rel_x * space['width']
                inner_y = rel_y * space['height']
                
                # Check if this position is a wall in the inner grid
                inner_grid_x = int(inner_x)
                inner_grid_y = int(inner_y)
                
                # Bounds check
                result = False
                if (0 <= inner_grid_x < space['width'] and 
                    0 <= inner_grid_y < space['height']):
                    result = space['grid'][inner_grid_y][inner_grid_x] == 1
                
                # Cache the result
                if len(self._impossible_space_cache) < self._cache_size_limit:
                    self._impossible_space_cache[cache_key] = result
                    
                return result
        
        # Cache negative result
        if len(self._impossible_space_cache) < self._cache_size_limit:
            self._impossible_space_cache[cache_key] = False
            
        return False
    
    def generate_new_map(self):
        """Generate a completely new map"""
        # Reset the map
        self.grid = np.ones((self.height, self.width), dtype=int)
        self.portals = []
        self.impossible_spaces = []
        self.distortion_fields = []
        
        # Generate a new map
        self.generate_basic_map()
        
    def get_map_data(self):
        """Return map data for rendering"""
        return {
            'grid': self.grid,
            'width': self.width,
            'height': self.height,
            'cell_size': self.cell_size,
            'portals': self.portals,
            'distortion_fields': self.distortion_fields,
            'wall_textures': self.wall_textures
        }
