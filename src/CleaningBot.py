import numpy as np
from OpenGL.GL import *
import math
import random


class CleaningBot:
    def __init__(self, dim, bot_index=0, total_bots=1, face_texture=None, toilet=None):
        # Make front face a perfect square (12x12)
        self.body_points = np.array(
            [
                [-6.0, 0.0, 12.0],
                [6.0, 0.0, 12.0],
                [6.0, 0.0, -12.0],
                [-6.0, 0.0, -12.0],
                [-6.0, 12.0, 12.0],
                [6.0, 12.0, 12.0],
                [6.0, 12.0, -12.0],
                [-6.0, 12.0, -12.0],
            ]
        )

        # Scale up the front marker
        self.front_points = np.array(
            [
                [0.0, 6.0, 30.0],  # Front point
                [-6.0, 6.0, 24.0],  # Left base
                [6.0, 6.0, 24.0],  # Right base
            ]
        )

        self.DimBoard = dim

        # Position bots in a circle around the center
        if total_bots == 1:
            # If there's only one bot, put it at the center
            self.Position = [0.0, 0.0, 0.0]
            self.rotation = 0.0
        else:
            # Calculate position in a circle
            radius = 30.0  # Half the radius for smaller bots
            angle = (2 * math.pi * bot_index) / total_bots
            self.Position = [
                radius * math.cos(angle),  # X coordinate
                0.0,  # Y coordinate (on the ground)
                radius * math.sin(angle),  # Z coordinate
            ]
            # Make bots face outward from the center
            self.rotation = math.degrees(angle) + 180

        self.speed = 1.6  # Half the speed for smaller bots
        self.base_speed = 1.6  # Store the base speed
        self.carrying_trash = None
        self.state = "searching"
        self.fatness = 1.0  # Scale factor for body width (1.0 = normal, 1.4 = fat)
        self.target_fatness = 1.0  # Target fatness for smooth animation
        self.fatness_change_speed = 0.02  # How fast the bot gets fat or thin
        self.dump_animation_progress = 0.0  # Progress of dumping animation (0.0 to 1.0)
        self.dump_block_size = 4.0  # Half the size of dumping block

        self.face_texture = face_texture
        self.face_texture_open = None  # Will store the open mouth texture
        self.eating_animation_progress = 0.0
        self.eating_animation_state = "closed"  # Can be "closed" or "open"
        self.eating_animation_speed = 0.2  # Controls how fast the mouth opens/closes
        self.eating_cycles = 0  # Count how many times we've opened/closed the mouth
        self.toilet = toilet  # Store toilet reference

    def update(self, trash_objects):
        # Update fatness animation
        if self.fatness < self.target_fatness:
            self.fatness = min(
                self.fatness + self.fatness_change_speed, self.target_fatness
            )
        elif self.fatness > self.target_fatness:
            self.fatness = max(
                self.fatness - self.fatness_change_speed, self.target_fatness
            )

        # Update speed based on fatness
        if self.carrying_trash:
            self.speed = self.base_speed * 0.6  # 40% slower when carrying trash
        else:
            self.speed = self.base_speed

        if self.state == "searching":
            closest_trash = self.search_trash(trash_objects)
            if closest_trash:
                # Calculate direction to trash
                dx = closest_trash.Position[0] - self.Position[0]
                dz = closest_trash.Position[2] - self.Position[2]
                dist = math.sqrt(dx * dx + dz * dz)

                if dist < 10.0:  # Half the collection range
                    # Immediately collect the trash
                    closest_trash.is_collected = True
                    self.carrying_trash = closest_trash
                    # Start eating animation and get fat
                    self.state = "eating"
                    self.eating_animation_progress = 0.0
                    self.eating_animation_state = "closed"
                    self.eating_cycles = 0
                    self.target_fatness = 1.4  # Start getting fat
                else:
                    # Calculate angle in degrees
                    target_angle = math.degrees(math.atan2(dx, dz))
                    # Update rotation to face the trash
                    self.rotation = target_angle

                    # Move towards trash
                    self.Position[0] += self.speed * math.sin(
                        math.radians(self.rotation)
                    )
                    self.Position[2] += self.speed * math.cos(
                        math.radians(self.rotation)
                    )
        elif self.state == "eating":
            # Update eating animation
            self.eating_animation_progress += self.eating_animation_speed

            if (
                self.eating_animation_state == "closed"
                and self.eating_animation_progress >= 1.0
            ):
                self.eating_animation_state = "open"
                self.eating_animation_progress = 0.0
                self.eating_cycles += 0.5
            elif (
                self.eating_animation_state == "open"
                and self.eating_animation_progress >= 1.0
            ):
                self.eating_animation_state = "closed"
                self.eating_animation_progress = 0.0
                self.eating_cycles += 0.5

            # After 3 complete cycles, move on
            if self.eating_cycles >= 3:
                self.state = "returning"
                self.eating_animation_progress = 0.0
                self.eating_animation_state = "closed"
                self.eating_cycles = 0
        elif self.state == "returning":
            self.return_to_base()
        elif self.state == "dumping":
            self.dump_trash()
        elif self.state == "dumping_animation":
            self.dump_animation_progress += 0.03  # Slightly faster animation
            if self.dump_animation_progress >= 1.0:
                self.dump_animation_progress = 0.0
                self.carrying_trash = None
                self.state = "searching"
                self.target_fatness = 1.0  # Return to normal size after dumping

    def draw_body(self):
        glColor3f(0.0, 0.7, 0.0)  # Green color for body

        # Enable texture for front face
        if self.face_texture is not None:
            glEnable(GL_TEXTURE_2D)
            # Choose texture based on eating animation state
            if (
                self.state == "eating"
                and self.eating_animation_state == "open"
                and self.face_texture_open is not None
            ):
                glBindTexture(GL_TEXTURE_2D, self.face_texture_open)
            else:
                glBindTexture(GL_TEXTURE_2D, self.face_texture)

        glPushMatrix()
        # Apply fatness scale only to X axis (width)
        glScalef(self.fatness, 1.0, 1.0)

        glBegin(GL_QUADS)

        # Front face (with texture)
        if self.face_texture is not None:
            glTexCoord2f(0.0, 0.0)
            glVertex3f(
                self.body_points[0][0], self.body_points[0][1], self.body_points[0][2]
            )
            glTexCoord2f(1.0, 0.0)
            glVertex3f(
                self.body_points[1][0], self.body_points[1][1], self.body_points[1][2]
            )
            glTexCoord2f(1.0, 1.0)
            glVertex3f(
                self.body_points[5][0], self.body_points[5][1], self.body_points[5][2]
            )
            glTexCoord2f(0.0, 1.0)
            glVertex3f(
                self.body_points[4][0], self.body_points[4][1], self.body_points[4][2]
            )
        else:
            glVertex3f(
                self.body_points[0][0], self.body_points[0][1], self.body_points[0][2]
            )
            glVertex3f(
                self.body_points[1][0], self.body_points[1][1], self.body_points[1][2]
            )
            glVertex3f(
                self.body_points[5][0], self.body_points[5][1], self.body_points[5][2]
            )
            glVertex3f(
                self.body_points[4][0], self.body_points[4][1], self.body_points[4][2]
            )

        # Back face
        glVertex3f(
            self.body_points[2][0], self.body_points[2][1], self.body_points[2][2]
        )
        glVertex3f(
            self.body_points[3][0], self.body_points[3][1], self.body_points[3][2]
        )
        glVertex3f(
            self.body_points[7][0], self.body_points[7][1], self.body_points[7][2]
        )
        glVertex3f(
            self.body_points[6][0], self.body_points[6][1], self.body_points[6][2]
        )

        # Top face
        glVertex3f(
            self.body_points[4][0], self.body_points[4][1], self.body_points[4][2]
        )
        glVertex3f(
            self.body_points[5][0], self.body_points[5][1], self.body_points[5][2]
        )
        glVertex3f(
            self.body_points[6][0], self.body_points[6][1], self.body_points[6][2]
        )
        glVertex3f(
            self.body_points[7][0], self.body_points[7][1], self.body_points[7][2]
        )

        # Bottom face
        glVertex3f(
            self.body_points[0][0], self.body_points[0][1], self.body_points[0][2]
        )
        glVertex3f(
            self.body_points[1][0], self.body_points[1][1], self.body_points[1][2]
        )
        glVertex3f(
            self.body_points[2][0], self.body_points[2][1], self.body_points[2][2]
        )
        glVertex3f(
            self.body_points[3][0], self.body_points[3][1], self.body_points[3][2]
        )

        # Left face
        glVertex3f(
            self.body_points[0][0], self.body_points[0][1], self.body_points[0][2]
        )
        glVertex3f(
            self.body_points[3][0], self.body_points[3][1], self.body_points[3][2]
        )
        glVertex3f(
            self.body_points[7][0], self.body_points[7][1], self.body_points[7][2]
        )
        glVertex3f(
            self.body_points[4][0], self.body_points[4][1], self.body_points[4][2]
        )

        # Right face
        glVertex3f(
            self.body_points[1][0], self.body_points[1][1], self.body_points[1][2]
        )
        glVertex3f(
            self.body_points[2][0], self.body_points[2][1], self.body_points[2][2]
        )
        glVertex3f(
            self.body_points[6][0], self.body_points[6][1], self.body_points[6][2]
        )
        glVertex3f(
            self.body_points[5][0], self.body_points[5][1], self.body_points[5][2]
        )

        glEnd()

        glPopMatrix()

        # Disable texture after drawing
        if self.face_texture is not None:
            glDisable(GL_TEXTURE_2D)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        glRotatef(self.rotation, 0, 1, 0)  # Rotate around Y axis

        # Draw the main body
        self.draw_body()

        # Draw the front marker (triangle)
        glColor3f(1.0, 0.0, 0.0)  # Red color for the front marker
        glBegin(GL_TRIANGLES)
        for point in self.front_points:
            glVertex3f(point[0], point[1], point[2])
        glEnd()

        # Draw dumping animation if active
        if self.state == "dumping_animation":
            self.draw_dump_animation()

        glPopMatrix()

    def draw_dump_animation(self):
        # Draw a brown block coming out from behind the bot
        glColor3f(0.6, 0.3, 0.0)  # Brown color

        # Calculate block position and size based on animation progress
        progress = self.dump_animation_progress

        # Block starts small and gets bigger as it drops
        block_size = self.dump_block_size * (0.3 + progress * 0.7)

        # Calculate position relative to toilet
        angle_rad = math.radians(self.rotation)

        # Start position (from bot's back)
        start_x = self.Position[0] - math.sin(angle_rad) * 12.0
        start_z = self.Position[2] - math.cos(angle_rad) * 12.0
        start_y = 12.0  # Start even higher for longer projectile

        # End position (toilet bowl)
        end_x = 0
        end_z = 0
        end_y = 0

        # Calculate distance to toilet for velocity adjustment
        dist_to_toilet = math.sqrt(start_x * start_x + start_z * start_z)

        # Projectile motion with increased power
        t = progress  # Time parameter (0 to 1)
        gravity = 45.0  # Increased gravity for faster drop

        # Calculate initial velocities based on distance
        initial_speed = dist_to_toilet * 1.2  # Scale speed with distance

        # Interpolate x and z with distance-based velocity
        horizontal_speed = 2.2  # Increased horizontal speed
        block_x = start_x + (end_x - start_x) * t * horizontal_speed
        block_z = start_z + (end_z - start_z) * t * horizontal_speed

        # Parabolic motion for y with adjusted initial velocity
        initial_vy = 35.0  # Increased initial vertical velocity
        block_y = start_y + initial_vy * t - 0.5 * gravity * t * t

        # Add slight curve to trajectory for more natural motion
        curve_factor = math.sin(t * math.pi) * 2.0
        block_x += curve_factor * math.cos(angle_rad)
        block_z += curve_factor * math.sin(angle_rad)

        # Scale gets slightly squished when hitting the ground
        y_scale = 1.0
        if progress > 0.8:
            impact_progress = (progress - 0.8) * 5
            y_scale = (
                1.0
                - (impact_progress * 0.3)
                + (impact_progress * impact_progress * 0.3)
            )

        glPushMatrix()
        glTranslatef(block_x, block_y, block_z)
        glScalef(1.0, y_scale, 1.0)

        # Draw the dumping block with rounded corners effect
        def draw_block(size):
            glBegin(GL_QUADS)
            # Front face
            glVertex3f(-size, 0, size)
            glVertex3f(size, 0, size)
            glVertex3f(size, size * 2, size)
            glVertex3f(-size, size * 2, size)
            # Back face
            glVertex3f(-size, 0, -size)
            glVertex3f(size, 0, -size)
            glVertex3f(size, size * 2, -size)
            glVertex3f(-size, size * 2, -size)
            # Top face
            glVertex3f(-size, size * 2, size)
            glVertex3f(size, size * 2, size)
            glVertex3f(size, size * 2, -size)
            glVertex3f(-size, size * 2, -size)
            # Bottom face
            glVertex3f(-size, 0, size)
            glVertex3f(size, 0, size)
            glVertex3f(size, 0, -size)
            glVertex3f(-size, 0, -size)
            # Left face
            glVertex3f(-size, 0, -size)
            glVertex3f(-size, 0, size)
            glVertex3f(-size, size * 2, size)
            glVertex3f(-size, size * 2, -size)
            # Right face
            glVertex3f(size, 0, -size)
            glVertex3f(size, 0, size)
            glVertex3f(size, size * 2, size)
            glVertex3f(size, size * 2, -size)
            glEnd()

        # Draw main block
        draw_block(block_size)

        # Draw a slightly darker outline
        glColor3f(0.5, 0.25, 0.0)  # Slightly darker brown
        draw_block(block_size * 1.02)  # Slightly larger

        glPopMatrix()

        # Notify toilet when waste hits
        if progress > 0.9 and not hasattr(self, "_notified_toilet"):
            if self.toilet:  # Check if toilet reference exists
                self.toilet.receive_waste()
                self._notified_toilet = True
        elif progress == 0:
            if hasattr(self, "_notified_toilet"):
                del self._notified_toilet

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

        return nearest_trash

    def return_to_base(self):
        # Move towards center (0,0,0)
        if self.state == "returning":
            # Calculate distance to center
            dx = -self.Position[0]
            dz = -self.Position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            if dist < 10.0:  # Half the distance for dumping
                # Calculate angle to face away from center
                self.rotation = math.degrees(
                    math.atan2(self.Position[0], self.Position[2])
                )
                self.state = "dumping_animation"
            else:
                self.rotation = math.degrees(math.atan2(dx, dz))

                # Move towards center with increased speed
                self.Position[0] += self.speed * math.sin(math.radians(self.rotation))
                self.Position[2] += self.speed * math.cos(math.radians(self.rotation))

            if self.carrying_trash:
                self.carrying_trash.Position[0] = self.Position[0]
                self.carrying_trash.Position[1] = self.Position[1]
                self.carrying_trash.Position[2] = self.Position[2]

    def is_colliding_with_toilet(self):
        # Get bot's dimensions
        bot_radius = max(self.width, self.height) / 2

        # Toilet dimensions (based on scale from Toilet class)
        toilet_radius = 15.0  # Toilet scale
        bowl_radius = toilet_radius * 0.8  # Bowl is 80% of scale

        # Calculate distance from bot center to toilet center
        dx = self.Position[0]  # Toilet is at origin
        dz = self.Position[2]
        distance = math.sqrt(dx * dx + dz * dz)

        # Check if bot's radius overlaps with toilet's bowl plus a large safety margin
        return distance < (
            bowl_radius + bot_radius + 15.0
        )  # Increased safety margin to 15 units

    def dump_trash(self):
        if self.carrying_trash:
            # Calculate distance to toilet (which is at center)
            dx = -self.Position[0]
            dz = -self.Position[2]
            dist = math.sqrt(dx * dx + dz * dz)

            # First check if we're too close to the toilet
            if self.is_colliding_with_toilet():
                # Move away from toilet
                angle = math.atan2(
                    self.Position[0], self.Position[2]
                )  # Angle away from toilet
                self.Position[0] += (
                    math.sin(angle) * self.speed * 3
                )  # Move away even faster
                self.Position[2] += math.cos(angle) * self.speed * 3
                return  # Don't proceed with dumping until we're at a safe distance

            # Keep a much safer distance from toilet (50-55 units)
            if dist < 55.0 and dist > 50.0:
                # Calculate angle to face toilet
                target_angle = math.degrees(
                    math.atan2(self.Position[0], self.Position[2])
                )
                angle_diff = (target_angle - self.rotation) % 360
                if angle_diff > 180:
                    angle_diff -= 360

                if abs(angle_diff) < 5:  # Facing roughly towards toilet
                    self.state = "dumping_animation"
                else:
                    # Turn to face toilet
                    if angle_diff < 0:
                        self.rotation += 2
                    else:
                        self.rotation -= 2
            else:
                # Only move if we're not colliding with the toilet
                if not self.is_colliding_with_toilet():
                    # Move towards ideal distance from toilet
                    target_dist = 52.5  # Target distance from toilet
                    current_dist = math.sqrt(
                        self.Position[0] ** 2 + self.Position[2] ** 2
                    )

                    # Calculate direction to or from toilet
                    angle = math.atan2(-self.Position[0], -self.Position[2])

                    # Calculate new position
                    new_x = self.Position[0]
                    new_z = self.Position[2]

                    if current_dist < target_dist - 0.5:  # Too close
                        new_x -= math.sin(angle) * self.speed
                        new_z -= math.cos(angle) * self.speed
                    elif current_dist > target_dist + 0.5:  # Too far
                        new_x += math.sin(angle) * self.speed
                        new_z += math.cos(angle) * self.speed

                    # Update position only if it won't cause collision
                    self.Position[0] = new_x
                    self.Position[2] = new_z
