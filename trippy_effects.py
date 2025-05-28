import math
import numpy as np
import pygame
import random

class TrippyEffects:
    """Class to handle various trippy visual and spatial effects for the raycasting engine"""
    
    def __init__(self):
        # Distortion settings
        self.enabled = True
        self.level = 0.5  # 0.0 to 1.0
        self.frequency = 0.1  # How quickly distortion changes
        self.time = 0
        self.wave_amplitude = 0.2  # Amplitude of the sine wave for ray bending
        self.wave_frequency = 0.1  # Frequency of the sine wave for ray bending
        self.color_shift_speed = 0.02  # Speed of color shifting
        
        # Non-Euclidean effects
        self.space_warping = 0.3  # How much space warps around the player
        self.reality_breakdown = 0.0  # Increases over time for escalating effects
        
        # Drunk/trippy movement effects
        self.movement_wobble = 0.2  # How much the player movement wobbles
        self.vision_pulsing = 0.1  # Pulsing effect on vision/FOV
        
        # Visual distortion effects
        self.visual_noise = 0.05  # Static/noise overlay intensity
        self.color_bleeding = 0.2  # How much colors bleed into each other
        self.afterimage_strength = 0.1  # Strength of afterimage effect
        self.afterimages = []  # Store previous frames for afterimage effect
        
        # Time-based effects
        self.time_dilation = 0.0  # Time slowing/speeding effect
        
        # Recursive space effects (rooms inside rooms)
        self.recursive_depth = 0  # Depth of recursive space effect
        
        # Impossible geometry
        self.impossible_angles = []  # List of angles where impossible geometry occurs
        
        # Pulse effects
        self.pulse_time = 0
        self.pulse_speed = 0.05
        self.pulse_strength = 0.2
        
        # Create noise texture for visual effects
        self.noise_texture = self.generate_noise_texture(256, 256)
    
    def update(self, dt):
        """Update all time-based effects"""
        if not self.enabled:
            return
            
        self.time += dt
        self.pulse_time += self.pulse_speed * dt
        
        # Slowly increase reality breakdown over time
        if random.random() < 0.001:  # Occasional random increases
            self.reality_breakdown = min(1.0, self.reality_breakdown + 0.01)
        
        # Update afterimages
        if len(self.afterimages) > 5:
            self.afterimages.pop(0)
    
    def apply_ray_distortion(self, angle, distance):
        """Apply distortion to a ray angle based on distance and time"""
        if not self.enabled:
            return angle
        
        # Basic sine wave distortion
        distortion = math.sin(distance * self.wave_frequency + self.time * self.frequency) * self.wave_amplitude
        
        # Add pulsing effect
        pulse = math.sin(self.pulse_time) * self.pulse_strength
        distortion += pulse * math.sin(distance * 0.2)
        
        # Add reality breakdown effect - more chaotic at higher levels
        if self.reality_breakdown > 0:
            chaos = math.sin(distance * 0.3 + self.time * 0.2) * self.reality_breakdown * 0.3
            distortion += chaos
        
        # Scale by overall distortion level
        distortion *= self.level
        
        return angle + distortion
    
    def apply_movement_distortion(self, dx, dy):
        """Apply drunk/trippy effects to player movement"""
        if not self.enabled or self.movement_wobble <= 0:
            return dx, dy
        
        # Add wobble to movement
        wobble_x = math.sin(self.time * 2.0) * self.movement_wobble
        wobble_y = math.cos(self.time * 1.7) * self.movement_wobble
        
        return dx + wobble_x, dy + wobble_y
    
    def apply_color_distortion(self, color, distance, angle):
        """Apply trippy color effects"""
        if not self.enabled:
            return color
        
        # Unpack color
        r, g, b = color
        
        # Apply color shifting based on time
        color_shift = (math.sin(self.time * self.color_shift_speed) + 1) / 2
        
        # Apply color bleeding between channels
        if self.color_bleeding > 0:
            bleed = self.color_bleeding * (math.sin(self.time * 0.1 + angle) + 1) / 2
            r2 = r * (1 - bleed) + g * bleed
            g2 = g * (1 - bleed) + b * bleed
            b2 = b * (1 - bleed) + r * bleed
            r, g, b = r2, g2, b2
        
        # Apply pulsing effect to colors
        pulse = (math.sin(self.pulse_time) + 1) / 2 * self.pulse_strength
        r = r * (1 + pulse * 0.2)
        g = g * (1 + (1 - pulse) * 0.2)
        
        # Apply reality breakdown effect - more color distortion
        if self.reality_breakdown > 0:
            breakdown = self.reality_breakdown * (math.sin(self.time * 0.3 + angle * 2) + 1) / 2
            r = r * (1 + breakdown * 0.3)
            b = b * (1 + breakdown * 0.3)
        
        # Clamp values
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        
        return (r, g, b)
    
    def apply_visual_noise(self, surface):
        """Apply visual noise/static to the screen"""
        if not self.enabled or self.visual_noise <= 0:
            return
        
        # Create a noise overlay using a separate surface instead of direct pixel manipulation
        width, height = surface.get_size()
        noise_level = self.visual_noise * (1 + self.reality_breakdown)
        
        # Skip if noise level is too low
        if noise_level < 0.01:
            return
            
        # Create a noise surface
        noise_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        noise_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Use pre-generated noise texture and just move/scale it
        noise_offset_x = int(self.time * 50) % 256
        noise_offset_y = int(self.time * 30) % 256
        
        # Apply noise by drawing small semi-transparent rectangles
        for y in range(0, height, 8):  # Larger steps for better performance
            for x in range(0, width, 8):
                if random.random() < noise_level * 0.1:
                    noise_x = (x + noise_offset_x) % 256
                    noise_y = (y + noise_offset_y) % 256
                    noise_value = int(self.noise_texture[noise_y][noise_x])
                    
                    # Create a small rectangle with noise value as alpha
                    alpha = min(200, noise_value * 4)  # Scale up noise for visibility but cap at 200
                    color = (255, 255, 255, alpha)  # White with variable transparency
                    
                    # Draw a small rectangle
                    pygame.draw.rect(noise_surface, color, (x, y, 8, 8))
        
        # Blend the noise surface with the main surface
        surface.blit(noise_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def apply_afterimage(self, surface):
        """Apply afterimage/trailing effect"""
        if not self.enabled or self.afterimage_strength <= 0 or not self.afterimages:
            return
        
        # Blend previous frames with current frame
        for i, (prev_surf, alpha) in enumerate(self.afterimages):
            # Decrease alpha for older frames
            alpha = alpha * 0.8
            self.afterimages[i] = (prev_surf, alpha)
            
            # Skip if alpha is too low
            if alpha < 0.05:
                continue
                
            # Blend with current frame
            prev_surf.set_alpha(int(255 * alpha * self.afterimage_strength))
            surface.blit(prev_surf, (0, 0))
        
        # Add current frame to afterimages
        current_copy = surface.copy()
        self.afterimages.append((current_copy, 0.8))
        
        # Limit number of stored frames
        if len(self.afterimages) > 5:
            self.afterimages.pop(0)
    
    def generate_noise_texture(self, width, height):
        """Generate a noise texture for visual effects"""
        noise = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                noise[y][x] = random.randint(0, 50)
        return noise
    
    def get_fov_distortion(self):
        """Get field of view distortion based on current effects"""
        if not self.enabled:
            return 0
            
        # Basic pulsing of FOV
        fov_change = math.sin(self.time * 0.5) * self.vision_pulsing * 10
        
        # Add reality breakdown effect
        if self.reality_breakdown > 0:
            fov_change += math.sin(self.time * 0.3) * self.reality_breakdown * 15
            
        return fov_change
    
    def toggle(self):
        """Toggle trippy effects on/off"""
        self.enabled = not self.enabled
        return self.enabled
    
    def increase_intensity(self):
        """Increase the intensity of all effects"""
        self.level = min(1.0, self.level + 0.1)
        self.wave_amplitude = min(0.5, self.wave_amplitude + 0.05)
        self.movement_wobble = min(0.5, self.movement_wobble + 0.05)
        self.visual_noise = min(0.2, self.visual_noise + 0.02)
        self.color_bleeding = min(0.5, self.color_bleeding + 0.05)
        self.pulse_strength = min(0.5, self.pulse_strength + 0.05)
        
    def decrease_intensity(self):
        """Decrease the intensity of all effects"""
        self.level = max(0.0, self.level - 0.1)
        self.wave_amplitude = max(0.0, self.wave_amplitude - 0.05)
        self.movement_wobble = max(0.0, self.movement_wobble - 0.05)
        self.visual_noise = max(0.0, self.visual_noise - 0.02)
        self.color_bleeding = max(0.0, self.color_bleeding - 0.05)
        self.pulse_strength = max(0.0, self.pulse_strength - 0.05)
