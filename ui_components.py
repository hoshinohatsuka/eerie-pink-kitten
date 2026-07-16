import math
import random
import logging
from PySide6 import QtCore, QtWidgets, QtGui, QtOpenGLWidgets

logger = logging.getLogger("UIComponents")

class ChatBubble(QtWidgets.QWidget):
    """
    A stylized floating chat bubble that displays the companion's dialogue.
    Uses glassmorphism/translucent background styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.SubWindow)
        
        # Setup layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        
        # Label to display dialog text
        self.label = QtWidgets.QLabel(self)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            "QLabel {"
            "  color: #FFFFFF;"
            "  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;"
            "  font-size: 13px;"
            "  font-weight: 500;"
            "  line-height: 1.4;"
            "}"
        )
        layout.addWidget(self.label)
        
        # Style the bubble widget
        self.setStyleSheet(
            "ChatBubble {"
            "  background-color: rgba(30, 30, 45, 0.85);"
            "  border: 1px solid rgba(255, 255, 255, 0.15);"
            "  border-radius: 12px;"
            "}"
        )
        self.setFixedWidth(220)
        self.hide()

    def show_text(self, text: str):
        self.label.setText(text)
        self.adjustSize()
        # Position bubble directly above the mascot
        if self.parentWidget():
            parent_w = self.parentWidget().width()
            bubble_h = self.height()
            # Center the bubble horizontally and place it above
            self.move((parent_w - self.width()) // 2, -bubble_h - 10)
        self.show()
        
    def fade_out(self, duration_ms: int = 3000):
        QtCore.QTimer.singleShot(duration_ms, self.hide)


class MascotVisualWidget(QtWidgets.QWidget):
    """
    Interactive rendering widget representing the digital mascot.
    Implements real-time animations for breathing, eye blinking, and lip-sync (mouth opening).
    Designed to easily interface with Live2D parameter mappings (e.g. MouthOpenY, EyeBlinkY).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        
        # Mascot animation parameters
        self.parameter_mouth_open_y = 0.0  # Range: 0.0 (closed) to 1.0 (fully open)
        self.parameter_eye_blink_y = 1.0   # Range: 0.0 (closed) to 1.0 (fully open)
        self.breathing_offset = 0.0        # Range: -5.0 to 5.0 pixels
        
        # Timers for procedural animations
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self._update_procedural_animations)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Eye blink controller timer
        self.blink_timer = QtCore.QTimer(self)
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start(3000)  # Blink check every 3 seconds
        
        self.is_blinking = False
        self.blink_step = 0
        self.tick = 0

    def set_mouth_open(self, value: float):
        """Sets the mouth open parameter (ParameterMouthOpenY) in range [0.0, 1.0]"""
        self.parameter_mouth_open_y = max(0.0, min(value, 1.0))
        self.update()

    def set_eye_blink(self, value: float):
        """Sets the eye blink parameter (ParameterEyeBlinkY) in range [0.0, 1.0]"""
        self.parameter_eye_blink_y = max(0.0, min(value, 1.0))
        self.update()

    def _update_procedural_animations(self):
        self.tick += 1
        # 1. Breathing logic (simple slow sine wave)
        self.breathing_offset = 3.0 * math.sin(self.tick * 0.05)
        
        # 2. Eye blinking step-wise transition
        if self.is_blinking:
            self.blink_step += 1
            if self.blink_step <= 3:  # Closing eyes
                self.parameter_eye_blink_y = max(0.0, self.parameter_eye_blink_y - 0.35)
            elif self.blink_step <= 6:  # Opening eyes
                self.parameter_eye_blink_y = min(1.0, self.parameter_eye_blink_y + 0.35)
            else:
                self.parameter_eye_blink_y = 1.0
                self.is_blinking = False
                self.blink_step = 0
                
        self.update()

    def _trigger_blink(self):
        # Randomly decide to blink to feel natural
        if random.random() > 0.3:
            self.is_blinking = True
            self.blink_step = 0

    def paintEvent(self, event: QtGui.QPaintEvent):
        """
        Renders a beautiful cartoon digital entity (a futuristic digital cat/slime mascot)
        with smooth gradients and alpha blending, dynamically responsive to parameters.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Center coordinates
        cx = self.width() / 2
        cy = self.height() / 2 + self.breathing_offset + 10
        
        # Draw Shadow
        shadow_width = 110 + self.breathing_offset * 1.5
        shadow_rect = QtCore.QRectF(cx - shadow_width/2, self.height() - 25, shadow_width, 12)
        shadow_grad = QtGui.QRadialGradient(cx, self.height() - 19, shadow_width/2)
        shadow_grad.setColorAt(0.0, QtGui.QColor(0, 0, 0, 80))
        shadow_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(shadow_grad)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(shadow_rect)

        # Draw Mascot Body (Cute Slime-Cat shape)
        body_path = QtGui.QPainterPath()
        
        # Ears & Head path
        body_path.moveTo(cx - 70, cy - 20)  # Left cheek
        body_path.cubicTo(cx - 85, cy - 80, cx - 80, cy - 90, cx - 50, cy - 80) # Left Ear
        body_path.lineTo(cx - 30, cy - 65) # Top head curve start
        body_path.quadTo(cx, cy - 70, cx + 30, cy - 65) # Top head curve end
        body_path.lineTo(cx + 50, cy - 80) # Right Ear start
        body_path.cubicTo(cx + 80, cy - 90, cx + 85, cy - 80, cx + 70, cy - 20) # Right Ear
        
        body_path.cubicTo(cx + 90, cy + 30, cx + 80, cy + 70, cx + 50, cy + 80) # Right bottom body
        body_path.quadTo(cx, cy + 88, cx - 50, cy + 80) # Bottom center body
        body_path.cubicTo(cx - 80, cy + 70, cx - 90, cy + 30, cx - 70, cy - 20) # Left bottom body
        
        # Gradient Fill: Sleek HSL cyber purple to pink gradient
        body_grad = QtGui.QLinearGradient(cx - 50, cy - 80, cx + 50, cy + 80)
        body_grad.setColorAt(0.0, QtGui.QColor(138, 43, 226))  # Cyber Purple
        body_grad.setColorAt(1.0, QtGui.QColor(255, 20, 147))   # Hot Pink
        painter.setBrush(body_grad)
        
        # Soft outer stroke
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 80), 2))
        painter.drawPath(body_path)
        
        # Cheek Blush
        blush_brush = QtGui.QColor(255, 105, 180, 120)
        painter.setBrush(blush_brush)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QRectF(cx - 55, cy + 10, 16, 8))
        painter.drawEllipse(QtCore.QRectF(cx + 39, cy + 10, 16, 8))
        
        # Draw Eyes (responsive to self.parameter_eye_blink_y)
        eye_color = QtGui.QColor(240, 248, 255) # Cyber White/Blue
        painter.setBrush(eye_color)
        painter.setPen(QtGui.QPen(QtGui.QColor(40, 40, 60), 2))
        
        eye_h = 24 * self.parameter_eye_blink_y
        
        if eye_h > 2.0:
            # Draw open eyes
            # Left Eye
            painter.drawEllipse(QtCore.QRectF(cx - 45, cy - 15 - eye_h/2, 18, eye_h))
            # Right Eye
            painter.drawEllipse(QtCore.QRectF(cx + 27, cy - 15 - eye_h/2, 18, eye_h))
            
            # Eye Pupils (Anime Highlights)
            painter.setBrush(QtGui.QColor(20, 20, 30))
            painter.drawEllipse(QtCore.QRectF(cx - 40, cy - 14 - eye_h/4, 10, eye_h/2))
            painter.drawEllipse(QtCore.QRectF(cx + 30, cy - 14 - eye_h/4, 10, eye_h/2))
            
            painter.setBrush(QtGui.QColor(255, 255, 255))
            painter.drawEllipse(QtCore.QRectF(cx - 39, cy - 15 - eye_h/6, 4, eye_h/4))
            painter.drawEllipse(QtCore.QRectF(cx + 31, cy - 15 - eye_h/6, 4, eye_h/4))
        else:
            # Draw closed/blinking eyes (simple curved line)
            painter.setPen(QtGui.QPen(QtGui.QColor(20, 20, 30), 3, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap))
            painter.drawArc(QtCore.QRectF(cx - 45, cy - 20, 18, 10), 0, -180 * 16)
            painter.drawArc(QtCore.QRectF(cx + 27, cy - 20, 18, 10), 0, -180 * 16)
            
        # Draw Mouth (responsive to self.parameter_mouth_open_y)
        painter.setPen(QtGui.QPen(QtGui.QColor(20, 20, 30), 2))
        mouth_w = 14
        mouth_h = 16 * self.parameter_mouth_open_y
        
        if mouth_h > 1.5:
            # Open mouth (drawn as a rounded capsule or ellipse)
            painter.setBrush(QtGui.QColor(220, 20, 60)) # Crimson inside mouth
            painter.drawEllipse(QtCore.QRectF(cx - mouth_w/2, cy + 2, mouth_w, mouth_h))
            # Tiny white fang
            painter.setBrush(QtGui.QColor(255, 255, 255))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            fang_path = QtGui.QPainterPath()
            fang_path.moveTo(cx - 3, cy + 3)
            fang_path.lineTo(cx, cy + 7)
            fang_path.lineTo(cx + 3, cy + 3)
            fang_path.closeSubpath()
            painter.drawPath(fang_path)
        else:
            # Closed mouth (w-shaped smile line)
            painter.setPen(QtGui.QPen(QtGui.QColor(20, 20, 30), 2.5, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap))
            # Draw left arc
            painter.drawArc(QtCore.QRectF(cx - 10, cy, 10, 8), 0, -180 * 16)
            # Draw right arc
            painter.drawArc(QtCore.QRectF(cx, cy, 10, 8), 0, -180 * 16)

        # Highlight Core on chest (soft neon orb)
        glow_grad = QtGui.QRadialGradient(cx, cy + 35, 12)
        glow_grad.setColorAt(0.0, QtGui.QColor(0, 255, 255, 220)) # Neon Cyan
        glow_grad.setColorAt(1.0, QtGui.QColor(0, 255, 255, 0))
        painter.setBrush(glow_grad)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QRectF(cx - 12, cy + 23, 24, 24))


class LipSyncController(QtCore.QObject):
    """
    Triggers lip sync animations (mouth opening values) synchronized with the token speed
    and text length emitted by the agent.
    """
    def __init__(self, mascot_widget: MascotVisualWidget):
        super().__init__()
        self.mascot = mascot_widget
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._step_sync)
        self.duration_counter = 0
        self.is_active = False

    def start_speaking(self, text: str):
        # Calculate duration based on character count (~120ms per character for natural dialogue feel)
        char_count = len(text)
        self.duration_counter = max(10, char_count * 8) # number of timer frames (50ms each)
        self.is_active = True
        self.timer.start(50) # Update mouth sync every 50ms

    def _step_sync(self):
        if not self.is_active or self.duration_counter <= 0:
            self.mascot.set_mouth_open(0.0)
            self.timer.stop()
            self.is_active = False
            return
            
        self.duration_counter -= 1
        
        # Procedurally fluctuate mouth opening parameter to mimic speaking
        # Alternate opening size to create talking sync effect
        open_val = 0.5 + 0.4 * math.sin(self.duration_counter * 1.5)
        # Random micro-disturbances
        open_val = max(0.0, min(open_val + random.uniform(-0.15, 0.15), 1.0))
        self.mascot.set_mouth_open(open_val)


class TransparentMascotWindow(QtWidgets.QWidget):
    """
    The main translucent overlay container that floats on the screen.
    Handles user click-drag movements and supports mouse transparency click-through.
    """
    def __init__(self):
        super().__init__()
        
        # Configure frameless stays-on-top tool window
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        
        # Configure transparency
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Initialize UI elements
        self.mascot = MascotVisualWidget(self)
        self.chat_bubble = ChatBubble(self)
        self.lip_sync = LipSyncController(self.mascot)
        
        # Setup layouts
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mascot)
        self.setLayout(layout)
        
        # Size window to fit mascot and bubble space
        self.resize(250, 250)
        
        # Position at the bottom-right portion of the user's primary screen
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(screen.width() - 300, screen.height() - 320)
        
        # Internal drag-and-drop mouse handling variables
        self.drag_position = QtCore.QPoint()

    def speak(self, text: str):
        """Displays text in bubble and drives lip sync mouth parameter"""
        logger.info(f"Mascot speaking: {text}")
        self.chat_bubble.show_text(text)
        self.lip_sync.start_speaking(text)
        self.chat_bubble.fade_out(4000) # Hide chat bubble after 4 seconds

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Check if user clicked on mascot or fully transparent region
            # We can sample the alpha channel of the widget at this pixel for true click-through
            pixel_color = self.grab(QtCore.QRect(event.position().toPoint(), QtCore.QSize(1, 1))).toImage().pixelColor(0, 0)
            if pixel_color.alpha() < 30:
                # Transparent click-through - forward click event to system below
                event.ignore()
                return
                
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.drag_position = QtCore.QPoint()
        event.accept()
