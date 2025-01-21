import numpy as np
from OpenGL.GL import *
import math


class CleaningBot:
    def __init__(self, dim):
        self.body_points = np.array(
            [
                [-1.0, 0.0, 2.0],  # Longer body for tank shape
                [1.0, 0.0, 2.0],
                [1.0, 0.0, -2.0],
                [-1.0, 0.0, -2.0],
                [-1.0, 1.0, 2.0],
                [1.0, 1.0, 2.0],
                [1.0, 1.0, -2.0],
                [-1.0, 1.0, -2.0],
            ]
        )

        # Arm vertices (two arms)
        self.arm_points = np.array(
            [
                [-0.2, 0.0, 0.2],
                [0.2, 0.0, 0.2],
                [0.2, 0.0, -0.2],
                [-0.2, 0.0, -0.2],
                [-0.2, 1.0, 0.2],
                [0.2, 1.0, 0.2],
                [0.2, 1.0, -0.2],
                [-0.2, 1.0, -0.2],
            ]
        )

        self.DimBoard = dim
        self.Position = [0.0, 0.0, 0.0]
        self.Direction = [1.0, 0.0, 0.0]
        self.speed = 2.0
        self.carrying_trash = None
        self.state = "searching"

        # Arm animation parameters
        self.arm_angle = 0.0  # Current arm angle
        self.target_arm_angle = 0.0  # Target arm angle
        self.arm_speed = 2.0  # Degrees per update

    def update(self, trash_objects):
        self.update_arms()

        if self.state == "searching":
            self.search_trash(trash_objects)
        elif self.state == "returning":
            self.return_to_base()
        elif self.state == "dumping":
            self.dump_trash()

    def update_arms(self):
        # Update arm angle based on state
        if self.state == "searching":
            self.target_arm_angle = 0.0
        elif self.carrying_trash:
            self.target_arm_angle = 45.0

        # Smoothly animate arms
        if self.arm_angle < self.target_arm_angle:
            self.arm_angle = min(self.arm_angle + self.arm_speed, self.target_arm_angle)
        elif self.arm_angle > self.target_arm_angle:
            self.arm_angle = max(self.arm_angle - self.arm_speed, self.target_arm_angle)

    def draw_body(self):
        # Draw tank body
        glColor3f(0.0, 0.7, 0.0)  # Darker green for body
        glBegin(GL_QUADS)
        # Bottom
        glVertex3fv(self.body_points[0])
        glVertex3fv(self.body_points[1])
        glVertex3fv(self.body_points[2])
        glVertex3fv(self.body_points[3])
        # Top
        glVertex3fv(self.body_points[4])
        glVertex3fv(self.body_points[5])
        glVertex3fv(self.body_points[6])
        glVertex3fv(self.body_points[7])
        # Front
        glVertex3fv(self.body_points[0])
        glVertex3fv(self.body_points[1])
        glVertex3fv(self.body_points[5])
        glVertex3fv(self.body_points[4])
        # Back
        glVertex3fv(self.body_points[2])
        glVertex3fv(self.body_points[3])
        glVertex3fv(self.body_points[7])
        glVertex3fv(self.body_points[6])
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

    def draw_arm(self, is_left):
        glPushMatrix()
        # Position the arm on the side of the body
        offset = -1.0 if is_left else 1.0
        glTranslatef(offset * 0.8, 0.5, 0.0)
        glRotatef(self.arm_angle, 1.0, 0.0, 0.0)  # Rotate around X axis

        # Draw arm
        glColor3f(0.0, 0.8, 0.0)  # Slightly lighter green for arms
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
        glPopMatrix()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        # Rotate to face direction of movement
        angle = math.atan2(self.Direction[2], self.Direction[0])
        glRotatef(math.degrees(angle), 0, 1, 0)
        glScaled(4, 4, 4)  # Scale the entire bot

        # Draw main components
        self.draw_body()
        self.draw_arm(True)  # Left arm
        self.draw_arm(False)  # Right arm

        glPopMatrix()

    def search_trash(self, trash_objects):
        # Find nearest uncollected trash
        nearest_trash = None
        min_dist = float("inf")

        for trash in trash_objects:
            if not trash.is_collected:
                dist = math.sqrt(
                    (self.Position[0] - trash.Position[0]) ** 2
                    + (self.Position[2] - trash.Position[2]) ** 2
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_trash = trash

        if nearest_trash:
            # Move towards nearest trash
            dx = nearest_trash.Position[0] - self.Position[0]
            dz = nearest_trash.Position[2] - self.Position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist < 3.0:  # Collection range
                nearest_trash.is_collected = True
                self.carrying_trash = nearest_trash
                self.state = "returning"
            else:
                # Update position towards trash
                self.Direction = [dx / dist, 0, dz / dist]
                self.Position[0] += self.Direction[0] * self.speed
                self.Position[2] += self.Direction[2] * self.speed

    def return_to_base(self):
        # Move towards center (0,0,0)
        dist = math.sqrt(self.Position[0] ** 2 + self.Position[2] ** 2)

        if dist < 3.0:
            self.state = "dumping"
        else:
            dx = -self.Position[0]
            dz = -self.Position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            self.Direction = [dx / dist, 0, dz / dist]
            self.Position[0] += self.Direction[0] * self.speed
            self.Position[2] += self.Direction[2] * self.speed

            if self.carrying_trash:
                self.carrying_trash.Position[0] = self.Position[0]
                self.carrying_trash.Position[2] = self.Position[2]

    def dump_trash(self):
        if self.carrying_trash:
            self.carrying_trash = None
        self.state = "searching"
