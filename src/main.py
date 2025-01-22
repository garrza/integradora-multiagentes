import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from CleaningBot import CleaningBot
from Trash import Trash
from Toilet import Toilet
import os
from PIL import Image
import sys
import random
import math

# Window dimensions
screen_width = 800
screen_height = 800

# Viewing parameters
FOVY = 60.0
ZNEAR = 1.0
ZFAR = 900.0

# Observer position parameters
EYE_X = 300.0
EYE_Y = 200.0
EYE_Z = 300.0
CENTER_X = 0
CENTER_Y = 0
CENTER_Z = 0
UP_X = 0
UP_Y = 1
UP_Z = 0

# Axis drawing boundaries
X_MIN = -500
X_MAX = 500
Y_MIN = -500
Y_MAX = 500
Z_MIN = -500
Z_MAX = 500

# Board dimensions
DimBoard = 200

# Usable area for trash (slightly smaller than board dimensions)
TRASH_AREA = DimBoard * 0.8  # 80% of board size

# Global variables
bots = []
trash_objects = []
toilet = None
n_bots = 5
n_trash = 20

# Texture ID for bot face
bot_face_texture = None

def load_texture(image_path):
    # Load image using PIL
    image = Image.open(image_path)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL expects textures flipped
    
    # Convert image to RGBA if it's not already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get image data as bytes
    img_data = image.tobytes()
    
    # Generate texture ID
    texture_id = glGenTextures(1)
    
    # Bind and set up texture
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    
    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    return texture_id

def Axis():
    """Draw coordinate axes"""
    glShadeModel(GL_FLAT)
    glLineWidth(3.0)

    # X axis in red
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN, 0.0, 0.0)
    glVertex3f(X_MAX, 0.0, 0.0)
    glEnd()

    # Y axis in green
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, Y_MIN, 0.0)
    glVertex3f(0.0, Y_MAX, 0.0)
    glEnd()

    # Z axis in blue
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, Z_MIN)
    glVertex3f(0.0, 0.0, Z_MAX)
    glEnd()

    glLineWidth(1.0)


def Init():
    """Initialize OpenGL context and objects"""
    global bot_face_texture
    global toilet
    
    screen = pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Trash Cleaning Simulation")
    
    # Set up the projection matrix
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width / screen_height, ZNEAR, ZFAR)

    # Set up the modelview matrix
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)

    # Set up the rendering context
    glClearColor(0, 0, 0, 0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)  # Enable texturing
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # Load bot face texture
    texture_path = os.path.join(os.path.dirname(__file__), 'assets', 'close.jpg')
    bot_face_texture = load_texture(texture_path)
    
    # Load open mouth texture
    open_texture_path = os.path.join(os.path.dirname(__file__), 'assets', 'open.jpg')
    bot_face_open_texture = load_texture(open_texture_path)
    
    # Initialize bots and trash
    for i in range(n_bots):
        bot = CleaningBot(DimBoard, i, n_bots, bot_face_texture)
        bot.face_texture_open = bot_face_open_texture
        bots.append(bot)
    for i in range(n_trash):
        trash_objects.append(Trash(DimBoard))
    
    toilet = Toilet()


def display():
    """Render the scene"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw coordinate axes
    Axis()

    # Draw floor
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3d(-DimBoard, 0, -DimBoard)
    glVertex3d(-DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, -DimBoard)
    glEnd()

    # Draw base station
    glColor3f(0.5, 0.5, 1.0)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glScaled(10, 1, 10)
    glBegin(GL_QUADS)
    glVertex3d(-1, 0, -1)
    glVertex3d(-1, 0, 1)
    glVertex3d(1, 0, 1)
    glVertex3d(1, 0, -1)
    glEnd()
    glPopMatrix()

    # Draw toilet
    toilet.draw()

    # Draw and update all objects
    for trash in trash_objects:
        trash.draw()

    for bot in bots:
        bot.update(trash_objects)
        bot.draw()


def main():
    """Main program loop"""
    pygame.init()
    Init()

    clock = pygame.time.Clock()
    done = False

    while not done:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == pygame.K_f:
                    toilet.flush()  # Manual flush with 'F' key
                elif event.key == pygame.K_t:
                    # Create a new Trash object when 'T' is pressed
                    new_trash = Trash(DimBoard)
                    trash_objects.append(new_trash)
        
        display()

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
