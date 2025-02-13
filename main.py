from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QWheelEvent
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from typing import Optional


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.last_mouse_pos: Optional[QPointF] = None
        self.theta: float = 45.0  # Polar angle for camera orbit
        self.phi: float = 45.0  # Azimuthal angle for camera orbit
        self.zoom: float = 5.0  # Camera distance
        self.pan_offset = np.array([0.0, 0.0, 0.0])  # [X, Y, Z]
        self.hovered_face: Optional[int] = None  # Index of the hovered face


    def initializeGL(self) -> None:
        """Initialize OpenGL settings."""
        glEnable(GL_DEPTH_TEST)  # Enable depth testing
        glClearColor(0.5, 0.5, 0.5, 1.0)  # Set background color
        print(glGetString(GL_VERSION))

    def resizeGL(self, w: int, h: int) -> None:
        """Handle widget resize."""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = w / h if h != 0 else 1.0
        glFrustum(-aspect_ratio, aspect_ratio, -1.0, 1.0, 1.0, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self) -> None:
        """Perform OpenGL rendering."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera orbit
        eye_x = self.zoom * np.sin(np.radians(self.phi)) * np.cos(np.radians(self.theta))
        eye_y = self.zoom * np.sin(np.radians(self.phi)) * np.sin(np.radians(self.theta))
        eye_z = self.zoom * np.cos(np.radians(self.phi))

        # Target position with pan offset
        target = np.array([0.0, 0.0, 0.0]) + self.pan_offset

        gluLookAt(eye_x + target[0], eye_y + target[1], eye_z + target[2],  # Eye position
                target[0], target[1], target[2],  # Target position
                0, 0, 1)  # Up direction

        # Draw reference frame
        self.draw_axes()
        self.draw_grid()

        # Draw the cube
        self.draw_cube()

    def draw_axes(self) -> None:
        """Draw the X, Y, and Z axes for reference."""
        glBegin(GL_LINES)

        # X-axis (Red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-2.0, 0.0, 0.0)
        glVertex3f(2.0, 0.0, 0.0)

        # Y-axis (Green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, -2.0, 0.0)
        glVertex3f(0.0, 2.0, 0.0)

        # Z-axis (Blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, -2.0)
        glVertex3f(0.0, 0.0, 2.0)

        glEnd()

    def draw_grid(self, size: int = 10, step: float = 1.0) -> None:
        """Draw a grid in the XZ plane."""
        glColor3f(0.5, 0.5, 0.5)  # Gray color for the grid
        glBegin(GL_LINES)
        for i in range(-size, size + 1):
            # Lines parallel to Z-axis
            glVertex3f(i * step, 0.0, -size * step)
            glVertex3f(i * step, 0.0, size * step)
            # Lines parallel to X-axis
            glVertex3f(-size * step, 0.0, i * step)
            glVertex3f(size * step, 0.0, i * step)
        glEnd()


    def draw_cube(self) -> None:
        """Draw a cube with optional transparency for the hovered face."""
        vertices = np.array([
            [-1.0, -1.0,  1.0], [1.0, -1.0,  1.0], [1.0,  1.0,  1.0], [-1.0,  1.0,  1.0],  # Front
            [-1.0, -1.0, -1.0], [-1.0,  1.0, -1.0], [1.0,  1.0, -1.0], [1.0, -1.0, -1.0],  # Back
            [-1.0, -1.0, -1.0], [-1.0, -1.0,  1.0], [-1.0,  1.0,  1.0], [-1.0,  1.0, -1.0],  # Left
            [1.0, -1.0, -1.0], [1.0,  1.0, -1.0], [1.0,  1.0,  1.0], [1.0, -1.0,  1.0],  # Right
            [-1.0,  1.0, -1.0], [-1.0,  1.0,  1.0], [1.0,  1.0,  1.0], [1.0,  1.0, -1.0],  # Top
            [-1.0, -1.0, -1.0], [1.0, -1.0,  1.0], [1.0, -1.0, -1.0], [-1.0, -1.0,  1.0]   # Bottom
        ])

        faces = [
            [0, 1, 2, 3],  # Front
            [4, 5, 6, 7],  # Back
            [8, 9, 10, 11],  # Left
            [12, 13, 14, 15],  # Right
            [16, 17, 18, 19],  # Top
            [20, 21, 22, 23],  # Bottom
        ]

        face_colors = [
            (1.0, 0.0, 0.0),  # Front
            (0.0, 1.0, 0.0),  # Back
            (0.0, 0.0, 1.0),  # Left
            (1.0, 1.0, 0.0),  # Right
            (1.0, 0.0, 1.0),  # Top
            (0.0, 1.0, 1.0),  # Bottom
        ]

        for i, face in enumerate(faces):
            if self.hovered_face == i:
                glColor4f(*face_colors[i], 0.5)  # Semi-transparent face
            else:
                glColor4f(*face_colors[i], 1.0)  # Opaque face

            glBegin(GL_QUADS)
            for vertex in face:
                glVertex3f(*vertices[vertex])
            glEnd()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement."""
        print(event.position())
        if self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            if event.buttons() == Qt.LeftButton:
                # Orbit
                self.theta -= delta.x() * 0.5
                self.phi -= delta.y() * 0.5
                self.phi = max(1.0, min(179.0, self.phi))  # Clamp to avoid gimbal lock
            elif event.buttons() == Qt.RightButton:
               # Pan relative to camera orbit
                pan_sensitivity = 0.01  # Adjust to control panning speed

                # Calculate forward and right vectors based on camera angles
                forward = np.array([
                    -np.sin(np.radians(self.phi)) * np.cos(np.radians(self.theta)),
                    -np.sin(np.radians(self.phi)) * np.sin(np.radians(self.theta)),
                    np.cos(np.radians(self.phi)),
                ])
                right = np.array([
                    np.sin(np.radians(self.theta)),
                    -np.cos(np.radians(self.theta)),
                    0.0,
                ])
                up = np.cross(right, forward)

                # Adjust pan based on mouse delta
                self.pan_offset += right * delta.x() * pan_sensitivity
                self.pan_offset += up * -delta.y() * pan_sensitivity  # Y-axis inverted
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        self.last_mouse_pos = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle zoom."""
        delta = event.angleDelta().y()
        self.zoom -= delta * 0.01
        self.zoom = max(2.0, min(20.0, self.zoom))  # Clamp zoom level
        self.update()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Interactive Cube")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.opengl_widget = OpenGLWidget()
        layout.addWidget(self.opengl_widget)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    app.exec()
