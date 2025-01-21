from OpenGL.GL import *
import numpy as np
import math
import random


class Toilet:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]  # Center of the world
        self.scale = 15.0  # Base size of toilet
        self.water_level = 0.2  # Start with some water
        self.flush_progress = 0.0  # Animation progress for flushing
        self.is_flushing = False
        self.waste_particles = []  # List of waste particles
        self.flush_rotation = 0.0  # Current rotation angle for swirl

        # Colors
        self.porcelain_color = (0.95, 0.95, 0.95)  # Almost white
        self.water_color = (0.2, 0.6, 1.0, 0.6)  # Light blue, semi-transparent
        self.waste_color = (0.4, 0.2, 0.0)  # Brown
        self.rim_color = (0.9, 0.9, 0.9)  # Slightly darker than porcelain
        self.tank_color = (0.93, 0.93, 0.93)  # Tank color

    def update(self):
        if self.is_flushing:
            self.flush_progress += 0.02
            self.flush_rotation += 15.0  # Rotate 15 degrees per update

            # Update waste particles during flush
            for particle in self.waste_particles:
                # Move particles in a spiral pattern
                angle = math.radians(self.flush_rotation + particle["offset"])
                radius = particle["radius"] * (1.0 - self.flush_progress)
                particle["x"] = math.cos(angle) * radius
                particle["z"] = math.sin(angle) * radius
                particle["y"] = particle["base_y"] * (1.0 - self.flush_progress)

            if self.flush_progress >= 1.0:
                self.flush_progress = 0.0
                self.is_flushing = False
                self.water_level = max(0.2, self.water_level - 0.3)  # Keep some water
                self.waste_particles = []  # Clear waste particles

        # Slowly settle waste particles
        if not self.is_flushing:
            for particle in self.waste_particles:
                if particle["y"] > 0.1:
                    particle["y"] = max(0.1, particle["y"] - 0.05)

    def receive_waste(self):
        # Add new waste particles
        for _ in range(5):  # Add multiple particles for each waste
            angle = random.uniform(0, 360)
            radius = random.uniform(0, self.scale * 0.3)
            self.waste_particles.append(
                {
                    "x": math.cos(math.radians(angle)) * radius,
                    "y": 2.0,  # Start above water
                    "z": math.sin(math.radians(angle)) * radius,
                    "size": random.uniform(0.8, 1.2),
                    "color": (
                        random.uniform(0.3, 0.5),
                        random.uniform(0.15, 0.25),
                        0.0,
                    ),
                    "radius": radius,
                    "offset": random.uniform(0, 360),
                    "base_y": random.uniform(0.1, 0.5),
                }
            )

        self.water_level = min(1.0, self.water_level + 0.1)
        if self.water_level > 0.8:
            self.flush()

    def flush(self):
        if not self.is_flushing:
            self.is_flushing = True
            self.flush_progress = 0.0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])

        # Draw base pedestal
        self.draw_pedestal()

        # Draw main bowl
        glColor3f(*self.porcelain_color)
        self.draw_bowl()

        # Draw water
        self.draw_water()

        # Draw tank
        self.draw_tank()

        glPopMatrix()

    def draw_pedestal(self):
        glColor3f(*self.porcelain_color)
        glPushMatrix()

        # Base of pedestal
        base_width = self.scale * 0.8
        base_height = self.scale * 0.3

        glBegin(GL_QUADS)
        # Front
        glVertex3f(-base_width / 2, 0, base_width / 2)
        glVertex3f(base_width / 2, 0, base_width / 2)
        glVertex3f(base_width / 2, base_height, base_width / 2)
        glVertex3f(-base_width / 2, base_height, base_width / 2)

        # Back
        glVertex3f(-base_width / 2, 0, -base_width / 2)
        glVertex3f(base_width / 2, 0, -base_width / 2)
        glVertex3f(base_width / 2, base_height, -base_width / 2)
        glVertex3f(-base_width / 2, base_height, -base_width / 2)

        # Left
        glVertex3f(-base_width / 2, 0, -base_width / 2)
        glVertex3f(-base_width / 2, 0, base_width / 2)
        glVertex3f(-base_width / 2, base_height, base_width / 2)
        glVertex3f(-base_width / 2, base_height, -base_width / 2)

        # Right
        glVertex3f(base_width / 2, 0, -base_width / 2)
        glVertex3f(base_width / 2, 0, base_width / 2)
        glVertex3f(base_width / 2, base_height, base_width / 2)
        glVertex3f(base_width / 2, base_height, -base_width / 2)

        # Top
        glVertex3f(-base_width / 2, base_height, -base_width / 2)
        glVertex3f(base_width / 2, base_height, -base_width / 2)
        glVertex3f(base_width / 2, base_height, base_width / 2)
        glVertex3f(-base_width / 2, base_height, base_width / 2)
        glEnd()

        glPopMatrix()

    def draw_bowl(self):
        glPushMatrix()
        glTranslatef(0, self.scale * 0.3, 0)  # Move up to top of pedestal

        # Bowl is oval-shaped and tapered
        segments = 32
        height = self.scale * 0.4

        # Draw outer surface
        glBegin(GL_QUAD_STRIP)
        for i in range(segments + 1):
            angle = (2.0 * math.pi * i) / segments
            x = math.cos(angle)
            z = math.sin(angle)

            # Bottom vertex (wider)
            glVertex3f(x * self.scale * 0.7, 0, z * self.scale * 0.6)
            # Top vertex (narrower)
            glVertex3f(x * self.scale * 0.6, height, z * self.scale * 0.5)
        glEnd()

        # Draw inner bowl surface (slightly darker)
        glColor3f(0.9, 0.9, 0.9)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, height * 0.7, 0)  # Center point
        for i in range(segments + 1):
            angle = (2.0 * math.pi * i) / segments
            x = math.cos(angle) * self.scale * 0.55
            z = math.sin(angle) * self.scale * 0.45
            glVertex3f(x, height, z)
        glEnd()

        glPopMatrix()

    def draw_water(self):
        bowl_height = self.scale * 0.7
        water_height = bowl_height * 0.4 + (bowl_height * 0.3 * self.water_level)

        glPushMatrix()
        glTranslatef(0, water_height, 0)

        # Enable transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw water surface with swirl effect
        segments = 32
        if self.is_flushing:
            glRotatef(self.flush_rotation, 0, 1, 0)

        # Draw main water surface
        glColor4f(*self.water_color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)  # Center

        for i in range(segments + 1):
            angle = (2.0 * math.pi * i) / segments
            x = math.cos(angle) * self.scale * 0.45
            z = math.sin(angle) * self.scale * 0.35

            # Add wave effect
            if self.is_flushing:
                wave = math.sin(angle * 4 + self.flush_rotation * 0.1) * 0.5
                x *= 1.0 + wave * 0.1
                z *= 1.0 + wave * 0.1

            glVertex3f(x, 0, z)
        glEnd()

        # Draw waste particles
        for particle in self.waste_particles:
            glPushMatrix()
            glTranslatef(particle["x"], -particle["y"], particle["z"])

            glColor3f(*particle["color"])

            # Draw waste particle as a small sphere
            sphere_segments = 8
            size = particle["size"] * self.scale * 0.05

            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, size, 0)  # Top vertex
            for i in range(sphere_segments + 1):
                angle = (2.0 * math.pi * i) / sphere_segments
                x = math.cos(angle) * size
                z = math.sin(angle) * size
                glVertex3f(x, 0, z)
            glEnd()

            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, -size, 0)  # Bottom vertex
            for i in range(sphere_segments + 1):
                angle = (2.0 * math.pi * i) / sphere_segments
                x = math.cos(angle) * size
                z = math.sin(angle) * size
                glVertex3f(x, 0, z)
            glEnd()

            glPopMatrix()

        glDisable(GL_BLEND)
        glPopMatrix()

    def draw_tank(self):
        glColor3f(*self.tank_color)
        glPushMatrix()

        # Position tank behind bowl
        tank_width = self.scale * 0.8
        tank_height = self.scale * 0.8
        tank_depth = self.scale * 0.4
        tank_offset = self.scale * 0.6  # Distance behind bowl center

        glTranslatef(0, self.scale * 0.3, -tank_offset)  # Move up and back

        # Draw tank box
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-tank_width / 2, 0, tank_depth / 2)
        glVertex3f(tank_width / 2, 0, tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, tank_depth / 2)
        glVertex3f(-tank_width / 2, tank_height, tank_depth / 2)

        # Back
        glVertex3f(-tank_width / 2, 0, -tank_depth / 2)
        glVertex3f(tank_width / 2, 0, -tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, -tank_depth / 2)
        glVertex3f(-tank_width / 2, tank_height, -tank_depth / 2)

        # Left
        glVertex3f(-tank_width / 2, 0, -tank_depth / 2)
        glVertex3f(-tank_width / 2, 0, tank_depth / 2)
        glVertex3f(-tank_width / 2, tank_height, tank_depth / 2)
        glVertex3f(-tank_width / 2, tank_height, -tank_depth / 2)

        # Right
        glVertex3f(tank_width / 2, 0, -tank_depth / 2)
        glVertex3f(tank_width / 2, 0, tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, -tank_depth / 2)

        # Top
        glVertex3f(-tank_width / 2, tank_height, -tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, -tank_depth / 2)
        glVertex3f(tank_width / 2, tank_height, tank_depth / 2)
        glVertex3f(-tank_width / 2, tank_height, tank_depth / 2)
        glEnd()

        # Draw tank lid (slightly darker)
        glColor3f(*[c * 0.95 for c in self.tank_color])
        glBegin(GL_QUADS)
        lid_overhang = self.scale * 0.05
        glVertex3f(
            -tank_width / 2 - lid_overhang, tank_height, -tank_depth / 2 - lid_overhang
        )
        glVertex3f(
            tank_width / 2 + lid_overhang, tank_height, -tank_depth / 2 - lid_overhang
        )
        glVertex3f(
            tank_width / 2 + lid_overhang, tank_height, tank_depth / 2 + lid_overhang
        )
        glVertex3f(
            -tank_width / 2 - lid_overhang, tank_height, tank_depth / 2 + lid_overhang
        )
        glEnd()

        glPopMatrix()
