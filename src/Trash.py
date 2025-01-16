import numpy as np
from OpenGL.GL import *
import random


class Trash:
    def __init__(self, dim):
        # Vertices of the cube (trash)
        self.points = np.array(
            [
                [-1.0, -1.0, 1.0],
                [1.0, -1.0, 1.0],
                [1.0, -1.0, -1.0],
                [-1.0, -1.0, -1.0],
                [-1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0],
                [1.0, 1.0, -1.0],
                [-1.0, 1.0, -1.0],
            ]
        )

        self.DimBoard = dim
        # Use a smaller area for trash distribution
        usable_area = dim * 0.8
        # Initialize random position on the board
        self.Position = [
            random.uniform(-usable_area, usable_area),
            0.0,  # On the ground
            random.uniform(-usable_area, usable_area),
        ]

        # Avoid placing trash too close to the base station
        while abs(self.Position[0]) < 20 and abs(self.Position[2]) < 20:
            self.Position[0] = random.uniform(-usable_area, usable_area)
            self.Position[2] = random.uniform(-usable_area, usable_area)

        self.is_collected = False

    def drawFaces(self):
        # Bottom face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[3])
        glEnd()

        # Top face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[4])
        glVertex3fv(self.points[5])
        glVertex3fv(self.points[6])
        glVertex3fv(self.points[7])
        glEnd()

        # Front face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[5])
        glVertex3fv(self.points[4])
        glEnd()

        # Back face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[3])
        glVertex3fv(self.points[7])
        glVertex3fv(self.points[6])
        glEnd()

        # Left face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[3])
        glVertex3fv(self.points[7])
        glVertex3fv(self.points[4])
        glEnd()

        # Right face
        glBegin(GL_QUADS)
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[6])
        glVertex3fv(self.points[5])
        glEnd()

    def draw(self):
        if not self.is_collected:
            glPushMatrix()
            glTranslatef(self.Position[0], self.Position[1], self.Position[2])
            glScaled(5, 5, 5)  # Much larger trash
            glColor3f(1.0, 0.4, 0.7)  # Pink color for trash
            self.drawFaces()
            glPopMatrix()
