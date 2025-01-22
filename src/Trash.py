import numpy as np
from OpenGL.GL import *
import random
import math

class Trash:
    def __init__(self, dim):
        # Vertices of the cube (burger)
        size = 4.0  # Doubled base size of the burger
        self.points = np.array([
            [-size, 0.0, size],    # Bottom layer vertices
            [size, 0.0, size],
            [size, 0.0, -size],
            [-size, 0.0, -size],
            [-size, size*2, size], # Top layer vertices
            [size, size*2, size],
            [size, size*2, -size],
            [-size, size*2, -size],
        ])

        self.DimBoard = dim
        # Use a smaller area for trash distribution
        usable_area = dim * 0.8
        # Initialize random position on the board
        self.Position = [
            random.uniform(-usable_area, usable_area),
            0.0,  # On the ground
            random.uniform(-usable_area, usable_area),
        ]
        self.is_collected = False
        self.rotation = random.uniform(0, 360)  # Random rotation for variety

        # Colors for different burger parts
        self.bun_color = (0.85, 0.65, 0.30)      # Light brown for bun
        self.patty_color = (0.45, 0.25, 0.15)    # Dark brown for meat
        self.lettuce_color = (0.40, 0.80, 0.20)  # Green for lettuce
        self.tomato_color = (0.90, 0.20, 0.10)   # Red for tomato
        self.cheese_color = (0.95, 0.75, 0.20)   # Yellow for cheese
        
        # Layer heights (as percentage of total height)
        self.layer_heights = [
            0.0,    # Bottom bun
            0.25,   # Patty
            0.4,    # Cheese
            0.55,   # Tomato
            0.7,    # Lettuce
            1.0     # Top bun
        ]

    def draw(self):
        if not self.is_collected:
            glPushMatrix()
            glTranslatef(self.Position[0], self.Position[1], self.Position[2])
            glRotatef(self.rotation, 0, 1, 0)  # Rotate around Y axis
            
            total_height = self.points[4][1]  # Height of the burger
            
            # Draw bottom bun
            glColor3f(*self.bun_color)
            self.draw_layer(0, self.layer_heights[1], True)  # Rounded bottom
            
            # Draw patty
            glColor3f(*self.patty_color)
            self.draw_layer(self.layer_heights[1], self.layer_heights[2])
            
            # Draw cheese
            glColor3f(*self.cheese_color)
            self.draw_layer(self.layer_heights[2], self.layer_heights[3])
            
            # Draw tomato
            glColor3f(*self.tomato_color)
            self.draw_layer(self.layer_heights[3], self.layer_heights[4])
            
            # Draw lettuce
            glColor3f(*self.lettuce_color)
            self.draw_layer(self.layer_heights[4], self.layer_heights[5])
            
            # Draw top bun
            glColor3f(*self.bun_color)
            self.draw_layer(self.layer_heights[4], self.layer_heights[5], True)  # Rounded top
            
            # Draw sesame seeds on top bun
            self.draw_sesame_seeds()
            
            glPopMatrix()

    def draw_layer(self, start_height, end_height, is_bun=False):
        size = self.points[1][0]  # Size of the burger (x-coordinate of right side)
        height = self.points[4][1]  # Total height
        start_y = start_height * height
        end_y = end_height * height
        
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-size, start_y, size)
        glVertex3f(size, start_y, size)
        glVertex3f(size, end_y, size)
        glVertex3f(-size, end_y, size)
        
        # Back face
        glVertex3f(-size, start_y, -size)
        glVertex3f(size, start_y, -size)
        glVertex3f(size, end_y, -size)
        glVertex3f(-size, end_y, -size)
        
        # Left face
        glVertex3f(-size, start_y, -size)
        glVertex3f(-size, start_y, size)
        glVertex3f(-size, end_y, size)
        glVertex3f(-size, end_y, -size)
        
        # Right face
        glVertex3f(size, start_y, -size)
        glVertex3f(size, start_y, size)
        glVertex3f(size, end_y, size)
        glVertex3f(size, end_y, -size)
        
        # Top face
        if is_bun:
            # Create a slightly domed top for buns
            center_lift = 0.3  # How much the center is lifted
            glVertex3f(-size, end_y, -size)
            glVertex3f(size, end_y, -size)
            glVertex3f(size, end_y + center_lift, size)
            glVertex3f(-size, end_y + center_lift, size)
        else:
            glVertex3f(-size, end_y, -size)
            glVertex3f(size, end_y, -size)
            glVertex3f(size, end_y, size)
            glVertex3f(-size, end_y, size)
        
        # Bottom face
        glVertex3f(-size, start_y, -size)
        glVertex3f(size, start_y, -size)
        glVertex3f(size, start_y, size)
        glVertex3f(-size, start_y, size)
        
        glEnd()

    def draw_sesame_seeds(self):
        size = self.points[1][0]
        height = self.points[4][1]
        top_y = height
        
        # Slightly lighter color for seeds
        seed_color = (0.95, 0.85, 0.60)
        glColor3f(*seed_color)
        
        # Draw several small seeds in a pattern
        for i in range(5):
            for j in range(5):
                if (i + j) % 2 == 0:  # Checker pattern
                    glPushMatrix()
                    # Position seed on top of bun
                    x = (i - 2) * (size * 0.4)
                    z = (j - 2) * (size * 0.4)
                    glTranslatef(x, top_y + 0.1, z)
                    
                    # Draw a small elongated cube for each seed
                    glBegin(GL_QUADS)
                    seed_size = 0.2
                    seed_height = 0.15
                    # Draw all faces of the seed
                    self.draw_seed(seed_size, seed_height)
                    glEnd()
                    
                    glPopMatrix()

    def draw_seed(self, size, height):
        # Front face
        glVertex3f(-size, 0, size)
        glVertex3f(size, 0, size)
        glVertex3f(size, height, size)
        glVertex3f(-size, height, size)
        
        # Back face
        glVertex3f(-size, 0, -size)
        glVertex3f(size, 0, -size)
        glVertex3f(size, height, -size)
        glVertex3f(-size, height, -size)
        
        # Left face
        glVertex3f(-size, 0, -size)
        glVertex3f(-size, 0, size)
        glVertex3f(-size, height, size)
        glVertex3f(-size, height, -size)
        
        # Right face
        glVertex3f(size, 0, -size)
        glVertex3f(size, 0, size)
        glVertex3f(size, height, size)
        glVertex3f(size, height, -size)
        
        # Top face
        glVertex3f(-size, height, -size)
        glVertex3f(size, height, -size)
        glVertex3f(size, height, size)
        glVertex3f(-size, height, size)
        
        # Bottom face
        glVertex3f(-size, 0, -size)
        glVertex3f(size, 0, -size)
        glVertex3f(size, 0, size)
        glVertex3f(-size, 0, size)
