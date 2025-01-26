import numpy as np
from OpenGL.GL import *
import math
import random

class CleaningBot:
    def __init__(
        self, 
        dim,
        bot_index=0,
        total_bots=1,
        face_texture=None,
        map_limit=0,
        toilet=None,
        spawn_position=None,      # NEW param
        lawnmower_direction=1     # NEW param
    ):
        # Body points (unchanged)
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

        # Front marker
        self.front_points = np.array(
            [
                [0.0, 6.0, 30.0],
                [-6.0, 6.0, 24.0],
                [6.0, 6.0, 24.0],
            ]
        )

        # Legs definition
        self.leg_points = []
        leg_spacing = 4.0
        leg_length = 10.0
        leg_height = 2.0
        
        # Left side legs
        for i in range(6):
            x_offset = -8.0
            z_offset = 12.0 - (i * leg_spacing)
            self.leg_points.extend([
                [x_offset,  leg_height,      z_offset],
                [x_offset, -leg_height, z_offset - leg_length]
            ])
        
        # Right side legs
        for i in range(6):
            x_offset = 8.0
            z_offset = 12.0 - (i * leg_spacing)
            self.leg_points.extend([
                [x_offset,  leg_height,      z_offset],
                [x_offset, -leg_height, z_offset - leg_length]
            ])

        self.leg_points = np.array(self.leg_points)

        # Leg animation
        self.leg_animation_phase = 0.0
        self.leg_animation_speed = 0.3
        self.leg_max_swing = 3.0
        self.leg_swing_frequency = 2 * math.pi

        # Basic params
        self.DimBoard = dim
        self.map_limit = map_limit

        # New: spawn_position & lawnmower_direction
        if spawn_position is None:
            # If no spawn given, default to bottom-left
            self.spawn_position = [-map_limit + 20, 0, -map_limit + 20]
        else:
            self.spawn_position = spawn_position

        # Current position starts at spawn
        self.Position = [self.spawn_position[0],
                         self.spawn_position[1],
                         self.spawn_position[2]]
        
        self.lawnmower_direction = lawnmower_direction
        self.rotation = 0.0

        # Movement & state
        self.speed = 4
        self.base_speed = 4
        self.state = "searching"
        self.carrying_trash = None

        # Fatness/eating/dumping
        self.fatness = 1.0
        self.target_fatness = 1.0
        self.fatness_change_speed = 0.02
        self.dump_animation_progress = 0.0
        self.dump_block_size = 4.0

        # Textures
        self.face_texture = face_texture
        self.face_texture_open = None
        self.eating_animation_progress = 0.0
        self.eating_animation_state = "closed"
        self.eating_animation_speed = 0.2
        self.eating_cycles = 0

        self.toilet = toilet

    def update(self, trash_objects):
        # Update fatness
        if self.fatness < self.target_fatness:
            self.fatness = min(self.fatness + self.fatness_change_speed, self.target_fatness)
        elif self.fatness > self.target_fatness:
            self.fatness = max(self.fatness - self.fatness_change_speed, self.target_fatness)

        # Speed if carrying trash
        if self.carrying_trash:
            self.speed = self.base_speed * 0.6
        else:
            self.speed = self.base_speed

        is_moving = False

        # State machine
        if self.state == "searching":
            self.lawnmower_movement()
            self.check_trash_collision(trash_objects)
            is_moving = True

        elif self.state == "eating":
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

            if self.eating_cycles >= 3:
                self.state = "returning"
                self.eating_animation_progress = 0.0
                self.eating_animation_state = "closed"
                self.eating_cycles = 0

        elif self.state == "returning":
            self.return_to_base()
            is_moving = True

        elif self.state == "dumping":
            self.dump_trash()

        elif self.state == "dumping_animation":
            self.dump_animation_progress += 0.03
            if self.dump_animation_progress >= 1.0:
                self.dump_animation_progress = 0.0
                self.carrying_trash = None
                self.state = "restart_position"
                self.target_fatness = 1.0

        elif self.state == "restart_position":
            self.restart_position()

        elif self.state == "align":
            self.align()

        # Leg animation
        if is_moving:
            self.leg_animation_phase += self.leg_animation_speed
            if self.leg_animation_phase >= 2 * math.pi:
                self.leg_animation_phase -= 2 * math.pi
        else:
            self.leg_animation_phase = 0.0

    def lawnmower_movement(self):
        # Límites en el eje X (bordes izquierdo y derecho)
        left_bound = -self.map_limit + 20
        right_bound = self.map_limit - 20

        # Distinguimos si el bot está en la parte de arriba (Z > 0) o abajo (Z < 0)
        # para decidir cómo "avanzar la fila" (saltar en Z).
        is_top = (self.spawn_position[2] > 0)

        # Si lawnmower_direction == 1, el bot va de IZQUIERDA -> DERECHA
        if self.lawnmower_direction == 1:
            # Checamos si ya llegó al borde derecho
            if self.Position[0] >= right_bound:
                # Invertir dirección para ir de derecha -> izquierda
                self.lawnmower_direction = -1
                self.rotation = (self.rotation + 180) % 360
                
                # Avanzar una "fila" en Z
                if is_top:
                    # Si está arriba, "bajamos" en Z
                    self.Position[2] -= 10
                else:
                    # Si está abajo, "subimos" en Z
                    self.Position[2] += 10
            else:
                # Continúa moviéndose a la derecha
                self.Position[0] += self.speed

        # Caso contrario: lawnmower_direction == -1, va de DERECHA -> IZQUIERDA
        else:
            # Checamos si llegó al borde izquierdo
            if self.Position[0] <= left_bound:
                # Invertir dirección para ir de izquierda -> derecha
                self.lawnmower_direction = 1
                self.rotation = (self.rotation + 180) % 360
                
                # Avanzar una "fila" en Z
                if is_top:
                    self.Position[2] -= 10
                else:
                    self.Position[2] += 10
            else:
                # Continúa moviéndose a la izquierda
                self.Position[0] -= self.speed


    def draw(self):
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        self.draw_body()

        # Red marker points
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_POINTS)
        for point in self.front_points:
            glVertex3f(point[0], point[1], point[2])
        glEnd()

        self.draw_legs()

        if self.state == "dumping_animation":
            self.draw_dump_animation()

        glPopMatrix()

    def draw_body(self):
        glColor3f(0.0, 0.7, 0.0)
        if self.face_texture is not None:
            glEnable(GL_TEXTURE_2D)
            if (
                self.state == "eating"
                and self.eating_animation_state == "open"
                and self.face_texture_open is not None
            ):
                glBindTexture(GL_TEXTURE_2D, self.face_texture_open)
            else:
                glBindTexture(GL_TEXTURE_2D, self.face_texture)

        glPushMatrix()
        glScalef(self.fatness, 1.0, 1.0)
        glBegin(GL_QUADS)
        # -- front face
        if self.face_texture:
            glTexCoord2f(0.0, 0.0)
            glVertex3f(*self.body_points[0])
            glTexCoord2f(1.0, 0.0)
            glVertex3f(*self.body_points[1])
            glTexCoord2f(1.0, 1.0)
            glVertex3f(*self.body_points[5])
            glTexCoord2f(0.0, 1.0)
            glVertex3f(*self.body_points[4])
        else:
            glVertex3f(*self.body_points[0])
            glVertex3f(*self.body_points[1])
            glVertex3f(*self.body_points[5])
            glVertex3f(*self.body_points[4])

        # -- back
        glVertex3f(*self.body_points[2])
        glVertex3f(*self.body_points[3])
        glVertex3f(*self.body_points[7])
        glVertex3f(*self.body_points[6])

        # -- top
        glVertex3f(*self.body_points[4])
        glVertex3f(*self.body_points[5])
        glVertex3f(*self.body_points[6])
        glVertex3f(*self.body_points[7])

        # -- bottom
        glVertex3f(*self.body_points[0])
        glVertex3f(*self.body_points[1])
        glVertex3f(*self.body_points[2])
        glVertex3f(*self.body_points[3])

        # -- left
        glVertex3f(*self.body_points[0])
        glVertex3f(*self.body_points[3])
        glVertex3f(*self.body_points[7])
        glVertex3f(*self.body_points[4])

        # -- right
        glVertex3f(*self.body_points[1])
        glVertex3f(*self.body_points[2])
        glVertex3f(*self.body_points[6])
        glVertex3f(*self.body_points[5])

        glEnd()
        glPopMatrix()

        if self.face_texture:
            glDisable(GL_TEXTURE_2D)

    def draw_legs(self):
        glColor3f(0.0, 0.7, 0.0)
        glPushMatrix()
        glScalef(self.fatness, 1.0, 1.0)
        glBegin(GL_LINES)
        for i in range(0, len(self.leg_points), 2):
            leg_swing = math.sin(
                self.leg_animation_phase + (i / len(self.leg_points)) * self.leg_swing_frequency
            ) * self.leg_max_swing
            upper_leg_point = [
                self.leg_points[i][0],
                self.leg_points[i][1] + leg_swing,
                self.leg_points[i][2],
            ]
            glVertex3f(*upper_leg_point)
            glVertex3f(*self.leg_points[i+1])
        glEnd()
        glPopMatrix()

    def draw_dump_animation(self):
        glColor3f(0.6, 0.3, 0.0)
        progress = self.dump_animation_progress
        block_size = self.dump_block_size * (0.3 + progress * 0.7)
        angle_rad = math.radians(self.rotation)
        start_x = self.Position[0] - math.sin(angle_rad) * 12.0
        start_z = self.Position[2] - math.cos(angle_rad) * 12.0
        start_y = 12.0

        end_x, end_z, end_y = 0, 0, 0
        dist_to_toilet = math.sqrt(start_x**2 + start_z**2)
        gravity = 45.0
        initial_vy = 35.0
        horizontal_speed = 2.2
        t = progress

        block_x = start_x + (end_x - start_x) * t * horizontal_speed
        block_z = start_z + (end_z - start_z) * t * horizontal_speed
        block_y = start_y + initial_vy * t - 0.5 * gravity * t * t

        curve_factor = math.sin(t * math.pi) * 2.0
        block_x += curve_factor * math.cos(angle_rad)
        block_z += curve_factor * math.sin(angle_rad)

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

        def draw_block(s):
            glBegin(GL_QUADS)
            # front
            glVertex3f(-s, 0, s)
            glVertex3f(s, 0, s)
            glVertex3f(s, s*2, s)
            glVertex3f(-s, s*2, s)
            # back
            glVertex3f(-s, 0, -s)
            glVertex3f(s, 0, -s)
            glVertex3f(s, s*2, -s)
            glVertex3f(-s, s*2, -s)
            # top
            glVertex3f(-s, s*2, s)
            glVertex3f(s, s*2, s)
            glVertex3f(s, s*2, -s)
            glVertex3f(-s, s*2, -s)
            # bottom
            glVertex3f(-s, 0, s)
            glVertex3f(s, 0, s)
            glVertex3f(s, 0, -s)
            glVertex3f(-s, 0, -s)
            # left
            glVertex3f(-s, 0, -s)
            glVertex3f(-s, 0, s)
            glVertex3f(-s, s*2, s)
            glVertex3f(-s, s*2, -s)
            # right
            glVertex3f(s, 0, -s)
            glVertex3f(s, 0, s)
            glVertex3f(s, s*2, s)
            glVertex3f(s, s*2, -s)
            glEnd()

        draw_block(block_size)
        glColor3f(0.5, 0.25, 0.0)
        draw_block(block_size * 1.02)
        glPopMatrix()

        # if near end, notify toilet
        if progress > 0.9 and not hasattr(self, "_notified_toilet"):
            if self.toilet:
                self.toilet.receive_waste()
                self._notified_toilet = True
        elif progress == 0:
            if hasattr(self, "_notified_toilet"):
                del self._notified_toilet

    def check_trash_collision(self, trash_objects):
        for trash in trash_objects:
            if not trash.is_collected:
                if abs(self.Position[0] - trash.Position[0]) <= 5 and abs(self.Position[2] - trash.Position[2]) <= 5:
                    print('collision')
                    trash.is_collected = True
                    self.state = 'eating'

    def return_to_base(self):
        if self.state == "returning":
            dx = -self.Position[0]
            dz = -self.Position[2]
            dist = math.sqrt(dx*dx + dz*dz)

            if dist < 10.0:
                self.rotation = math.degrees(math.atan2(self.Position[0], self.Position[2]))
                self.state = "dumping_animation"
            else:
                self.rotation = math.degrees(math.atan2(dx, dz))
                self.Position[0] += self.speed * math.sin(math.radians(self.rotation))
                self.Position[2] += self.speed * math.cos(math.radians(self.rotation))

            if self.carrying_trash:
                self.carrying_trash.Position[0] = self.Position[0]
                self.carrying_trash.Position[1] = self.Position[1]
                self.carrying_trash.Position[2] = self.Position[2]

    def restart_position(self):
        # Return to self.spawn_position
        dx = self.spawn_position[0] - self.Position[0]
        dz = self.spawn_position[2] - self.Position[2]
        dist = math.sqrt(dx*dx + dz*dz)

        if dist < 5.0:
            self.rotation = math.degrees(math.atan2(dx, dz))
            self.state = "searching"
        else:
            self.rotation = math.degrees(math.atan2(dx, dz))
            self.Position[0] += self.speed * math.sin(math.radians(self.rotation))
            self.Position[2] += self.speed * math.cos(math.radians(self.rotation))

    def align(self):
        self.rotation = 60.0
        self.state = 'searching'
