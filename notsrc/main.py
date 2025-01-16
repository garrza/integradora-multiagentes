import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys
from notsrc.CleaningBot import CleaningBot
from notsrc.Trash import Trash

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

# Initialize lists for bots and trash
bots = []
trash_objects = []
n_bots = 5
n_trash = 50  # Increased number of trash objects


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
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # Initialize bots and trash
    for i in range(n_bots):
        bots.append(CleaningBot(DimBoard))
    for i in range(n_trash):
        trash_objects.append(Trash(DimBoard))


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

        # Render scene
        display()

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
