import agentpy as ap
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from CleaningBot import CleaningBot
from Trash import Trash
from Toilet import Toilet
import random
import os
from PIL import Image
import time
import matplotlib.pyplot as plt

class CleaningBotAgent(ap.Agent):
    def setup(self):
        """Set up the CleaningBot agent."""
        self.bot = CleaningBot(
            self.p['dim'],
            self.id,
            self.p['n_bots'],
            self.p['face_texture'],
            self.p['map_limit'],
            self.p['toilet']
        )
        self.has_delivered_trash = False

    def update(self):
        """Update the agent's state."""
        self.bot.update(self.p['trash_objects'])

        # Check if the bot has delivered trash to the toilet
        if self.bot.state == 'returning' and self.bot.carrying_trash is None and not self.has_delivered_trash:
            self.model.collected_trash += 1
            self.has_delivered_trash = True

        # Reset flag once the bot starts searching again
        if self.bot.state == 'searching':
            self.has_delivered_trash = False

    def draw(self):
        """Draw the bot in the simulation."""
        self.bot.draw()

class CleaningSimulation(ap.Model):
    def setup(self):
        """Initialize the simulation."""
        # Parameters
        self.dim = self.p['dim']
        self.n_bots = self.p['n_bots']
        self.n_trash = self.p['n_trash']
        self.map_limit = self.p['dim']

        # Initialize metrics
        self.start_time = time.time()
        self.total_movements = 0
        self.collected_trash = 0
        self.collisions = 0
        self.movement_history = []  # To store movements over time

        # Initialize visual assets
        texture_path = os.path.join(os.path.dirname(__file__), 'assets', 'close.jpg')
        self.face_texture = self.load_texture(texture_path)

        open_texture_path = os.path.join(os.path.dirname(__file__), 'assets', 'open.jpg')
        self.face_texture_open = self.load_texture(open_texture_path)

        # Create Toilet
        self.toilet = Toilet()

        # Create trash objects
        self.trash_objects = [Trash(self.dim) for _ in range(self.n_trash)]

        # Pass shared attributes to parameters
        self.p['face_texture'] = self.face_texture
        self.p['toilet'] = self.toilet
        self.p['trash_objects'] = self.trash_objects
        self.p['map_limit'] = self.map_limit

        # Create agents
        self.agents = ap.AgentList(self, self.n_bots, CleaningBotAgent)
        for agent in self.agents:
            agent.setup()

    def update(self):
        """Update all agents and record metrics."""
        step_movements = 0
        for agent in self.agents:
            # Update agent
            agent.update()
            # Record movements
            step_movements += agent.bot.speed

        self.total_movements += step_movements
        self.movement_history.append(step_movements)

        # Detect collisions (basic example)
        positions = [tuple(agent.bot.Position) for agent in self.agents]
        if len(positions) > len(set(positions)):
            self.collisions += 1

        # End simulation if all trash is collected
        if self.collected_trash >= self.n_trash:
            self.stop_simulation()

    def stop_simulation(self):
        """Stop the simulation and show results."""
        elapsed_time = time.time() - self.start_time
        print(f"\nSimulación completada:")
        print(f"Tiempo total: {elapsed_time:.2f} segundos")
        print(f"Basura recolectada: {self.collected_trash}/{self.n_trash}")
        print(f"Movimientos totales: {self.total_movements}")
        print(f"Colisiones detectadas: {self.collisions}")

        # Display results with graphs
        self.display_results(elapsed_time)
        pygame.quit()
        exit()

    def display_results(self, elapsed_time):
        """Display simulation results as graphs."""
        plt.figure(figsize=(12, 6))

        # Plot movements over time
        plt.subplot(1, 2, 1)
        plt.plot(self.movement_history, label='Movements per Step', color='blue')
        plt.title('Movimientos por Iteración')
        plt.xlabel('Iteración')
        plt.ylabel('Movimientos')
        plt.legend()

        # Summary bar chart
        plt.subplot(1, 2, 2)
        metrics = ['Tiempo Total (s)', 'Basura Recolectada', 'Colisiones']
        values = [elapsed_time, self.collected_trash, self.collisions]
        plt.bar(metrics, values, color=['green', 'orange', 'red'])
        plt.title('Resumen de la Simulación')

        plt.tight_layout()
        plt.show()

    def load_texture(self, image_path):
        """Helper function to load textures."""
        image = Image.open(image_path)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL expects textures flipped
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        img_data = image.tobytes()
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return texture_id

    def draw(self):
        """Draw all objects in the simulation."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw coordinate axes
        self.draw_axes()

        # Draw floor
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex3d(-self.dim, 0, -self.dim)
        glVertex3d(-self.dim, 0, self.dim)
        glVertex3d(self.dim, 0, self.dim)
        glVertex3d(self.dim, 0, -self.dim)
        glEnd()

        # Draw toilet
        self.toilet.draw()

        # Draw trash objects
        for trash in self.trash_objects:
            trash.draw()

        # Draw agents
        for agent in self.agents:
            agent.draw()

    def draw_axes(self):
        glLineWidth(3.0)
        # X-axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(-self.dim, 0.0, 0.0)
        glVertex3f(self.dim, 0.0, 0.0)
        glEnd()
        # Y-axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, -self.dim, 0.0)
        glVertex3f(0.0, self.dim, 0.0)
        glEnd()
        # Z-axis (blue)
        glColor3f(0.0, 0.0, 1.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, -self.dim)
        glVertex3f(0.0, 0.0, self.dim)
        glEnd()
        glLineWidth(1.0)

    def run_simulation(self):
        """Run the simulation loop."""
        pygame.init()
        screen = pygame.display.set_mode((800, 800), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Trash Cleaning Simulation with AgentPy")

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, (800 / 800), 1, 900)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(300, 200, 300, 0, 0, 0, 0, 1, 0)

        glClearColor(0, 0, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        # Ensure setup is called before running the simulation
        self.setup()

        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    parameters = {
        'dim': 200,
        'n_bots': 5,
        'n_trash': 20
    }

    model = CleaningSimulation(parameters)
    model.run_simulation()
