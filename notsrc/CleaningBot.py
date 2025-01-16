import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import pygame


class CleaningBot:
    def __init__(self, dim):
        # Load and setup texture
        self.texture = self.load_texture("albert.jpeg")

        # Main body vertices (larger square shape)
        self.body_points = np.array(
            [
                [-1.0, -1.0, 1.0],  # Front face points (0-3)
                [1.0, -1.0, 1.0],
                [1.0, 1.0, 1.0],
                [-1.0, 1.0, 1.0],
                [-1.0, -1.0, -1.0],  # Back face points (4-7)
                [1.0, -1.0, -1.0],
                [1.0, 1.0, -1.0],
                [-1.0, 1.0, -1.0],
            ]
        )

        # Arm vertices (thicker and longer)
        self.arm_points = np.array(
            [
                [-0.2, 0.0, 0.2],  # Base of arm
                [0.2, 0.0, 0.2],
                [0.2, 0.0, -0.2],
                [-0.2, 0.0, -0.2],
                [-0.2, 2.0, 0.2],  # Top of arm (longer)
                [0.2, 2.0, 0.2],
                [0.2, 2.0, -0.2],
                [-0.2, 2.0, -0.2],
            ]
        )

        self.DimBoard = dim
        self.Position = [0.0, 8.0, 0.0]
        self.Direction = [1.0, 0.0, 0.0]
        self.speed = 1.0  # Slower movement speed
        self.carrying_trash = None
        self.state = "searching"

        # Arm animation parameters
        self.arm_angle = 0.0
        self.target_arm_angle = 0.0
        self.arm_speed = 1.5  # Slightly slower arm movement

    def load_texture(self, filename):
        """Load texture from image file"""
        textureSurface = pygame.image.load(filename)
        textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
        width = textureSurface.get_width()
        height = textureSurface.get_height()

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            textureData,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return texture

    def update(self, trash_objects):
        self.update_arms()

        if self.state == "searching":
            self.search_trash(trash_objects)
        elif self.state == "returning":
            self.return_to_base()
        elif self.state == "dumping":
            self.dump_trash()

    def update_arms(self):
        if self.carrying_trash:
            self.target_arm_angle = 90.0  # Arms pointing up when holding trash
        else:
            self.target_arm_angle = 0.0  # Arms forward when empty

        if self.arm_angle < self.target_arm_angle:
            self.arm_angle = min(self.arm_angle + self.arm_speed, self.target_arm_angle)
        elif self.arm_angle > self.target_arm_angle:
            self.arm_angle = max(self.arm_angle - self.arm_speed, self.target_arm_angle)

    def draw_body(self):
        glPushMatrix()
        glRotatef(90, 0, 1, 0)  # Rotate body so textured face is front

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        # Front face (textured)
        glColor3f(1.0, 1.0, 1.0)  # White base color
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3fv(self.body_points[0])
        glTexCoord2f(1.0, 0.0)
        glVertex3fv(self.body_points[1])
        glTexCoord2f(1.0, 1.0)
        glVertex3fv(self.body_points[2])
        glTexCoord2f(0.0, 1.0)
        glVertex3fv(self.body_points[3])
        glEnd()

        glDisable(GL_TEXTURE_2D)

        # Other faces (white)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        # Back
        glVertex3fv(self.body_points[4])
        glVertex3fv(self.body_points[5])
        glVertex3fv(self.body_points[6])
        glVertex3fv(self.body_points[7])
        # Top
        glVertex3fv(self.body_points[3])
        glVertex3fv(self.body_points[2])
        glVertex3fv(self.body_points[6])
        glVertex3fv(self.body_points[7])
        # Bottom
        glVertex3fv(self.body_points[0])
        glVertex3fv(self.body_points[1])
        glVertex3fv(self.body_points[5])
        glVertex3fv(self.body_points[4])
        # Left
        glVertex3fv(self.body_points[0])
        glVertex3fv(self.body_points[3])
        glVertex3fv(self.body_points[7])
        glVertex3fv(self.body_points[4])
        # Right
        glVertex3fv(self.body_points[1])
        glVertex3fv(self.body_points[2])
        glVertex3fv(self.body_points[6])
        glVertex3fv(self.body_points[5])
        glEnd()
        glPopMatrix()

    def draw_arm(self, is_left, angle):
        glPushMatrix()
        # Position arms on front face
        offset = -1.2 if is_left else 1.2
        glTranslatef(offset, 0.0, 1.0)  # Move arms to front face
        glRotatef(self.arm_angle, 1.0, 0.0, 0.0)  # Lift animation

        # Draw arm in blue
        glColor3f(0.0, 0.0, 1.0)
        glBegin(GL_QUADS)
        # All faces of the arm
        for i in range(6):
            if i == 0:  # Bottom
                vertices = [0, 1, 2, 3]
            elif i == 1:  # Top
                vertices = [4, 5, 6, 7]
            elif i == 2:  # Front
                vertices = [0, 1, 5, 4]
            elif i == 3:  # Back
                vertices = [2, 3, 7, 6]
            elif i == 4:  # Left
                vertices = [0, 3, 7, 4]
            else:  # Right
                vertices = [1, 2, 6, 5]

            for v in vertices:
                glVertex3fv(self.arm_points[v])
        glEnd()

        # Draw carried trash if this is the right arm
        if not is_left and self.carrying_trash:
            glTranslatef(0.0, 1.5, 0.0)  # Adjusted position to match ground trash
            glRotatef(-90, 0, 1, 0)  # Reset rotation to match world orientation
            glRotatef(-self.arm_angle, 1.0, 0.0, 0.0)
            glRotatef(angle - 90, 0, 1, 0)
            # Scale and color the carried trash to match Trash.py
            glPushMatrix()
            glScaled(
                0.625, 0.625, 0.625
            )  # Compensate for bot's scale (5/8 to match Trash.py when bot is scaled 8x)
            glColor3f(1.0, 0.4, 0.7)  # Pink color to match Trash.py
            self.carrying_trash.drawFaces()
            glPopMatrix()

        glPopMatrix()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])

        # Calculate angle to face direction of movement
        angle = math.degrees(math.atan2(self.Direction[2], self.Direction[0]))
        glRotatef(angle - 90, 0, 1, 0)

        glScaled(8, 8, 8)

        # Draw components
        self.draw_body()
        self.draw_arm(True, angle)  # Left arm
        self.draw_arm(False, angle)  # Right arm

        glPopMatrix()

    def search_trash(self, trash_objects):
        # Find nearest uncollected trash
        nearest_trash = None
        min_distance = float("inf")
        for trash in trash_objects:
            if not trash.is_collected:
                distance = np.linalg.norm(
                    np.array(trash.Position) - np.array(self.Position)
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_trash = trash

        if nearest_trash:
            # Move towards the nearest trash
            direction_vector = np.array(nearest_trash.Position) - np.array(
                self.Position
            )
            distance = np.linalg.norm(direction_vector)
            direction_vector /= distance  # Normalize

            # Check if within pickup distance
            if distance < 1.5:  # Pickup threshold
                self.carrying_trash = nearest_trash
                self.carrying_trash.is_collected = True
                self.state = "returning"
            else:
                # Move bot towards trash
                self.Position += direction_vector * self.speed

            # Update the bot's direction
            self.Direction = direction_vector

    def return_to_base(self):
        base_position = np.array([0.0, 8.0, 0.0])
        direction_vector = base_position - np.array(self.Position)
        distance = np.linalg.norm(direction_vector)
        direction_vector /= distance  # Normalize

        if distance < 1.0:  # Near base
            self.state = "dumping"
        else:
            # Move bot towards base
            self.Position += direction_vector * self.speed
            self.Direction = direction_vector

    def dump_trash(self):
        if self.carrying_trash:
            # Trash dumping animation logic
            self.carrying_trash = None
            self.state = "searching"
