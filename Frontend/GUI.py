from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy 
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os
import re
# from PyQt5.QtWidgets import (
#     QApplication, QDialog, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
# )

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
import sys
import os
import json

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QGraphicsOpacityEffect

# Path to the JSON file storing credentials
current_dir = os.getcwd()
CREDENTIALS_FILE = rf"{current_dir}\Frontend\Files\credentials.json"

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

class LoginScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)
        self.setStyleSheet("background-color: #121212; color: white;")

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("background-color: #1e1e1e; color: white; border-radius: 5px; padding: 5px;")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("background-color: #1e1e1e; color: white; border-radius: 5px; padding: 5px;")
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("background-color: #1e1e1e; color: white; border-radius: 5px; padding: 5px;")
        self.login_button.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def check_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Load credentials from JSON file
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, "r") as file:
                credentials = json.load(file)
        else:
            credentials = {}

        if username in credentials and credentials[username] == password:
            QMessageBox.information(self, "Success", "Login successful!")
            self.accept()  # Close the dialog and return QDialog.Accepted
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
        file.write(Command)
    # Sync Status.data with appropriate message
    status_message = "Listening..." if Command == "True" else "Not Listening..."
    with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
        file.write(status_message)

def GetMicrophoneStatus():
    with open(rf'{TempDirPath}\Mic.data', "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(rf'{TempDirPath}\Status.data', "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def MicButtonInitialed():
    SetMicrophoneStatus("True")
    SetAssistantStatus("Listening...")



def MicButtonClosed():
    SetMicrophoneStatus("False")
    SetAssistantStatus("Not Listening...")



def GraphicsDirectoryPath(Filename):
    Path = rf'{GraphicsDirPath}\{Filename}'
    return Path

def TempDirectoryPath(Filename):
    Path = rf'{TempDirPath}\{Filename}'
    return Path

def ShowTextToScreen(Text):
    with open(rf'{TempDirPath}\Responses.data', "w", encoding='utf-8') as file:
        file.write(Text)
class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)  # Center all elements

        # Chat display area
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 30, 230);
                color: #ffffff;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: Arial, sans-serif;
                border: 1px solid #444444;
            }
        """)
        layout.addWidget(self.chat_text_edit, stretch=1)

        # Horizontal layout for buttons and microphone
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)  # Center horizontally
        button_layout.setSpacing(15)

        # Clear Chat button
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #ff3d00, stop:1 #ff9100);
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                border: 2px solid #cc7000;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #ff5722, stop:1 #ffab40);
                border: 2px solid #ff9100;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #cc3300, stop:1 #cc7000);
            }
        """)
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)

        # Microphone icon setup
        self.icon_label = QLabel()
        try:
            pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
            if pixmap.isNull():
                raise ValueError("Failed to load Mic_on.png")
            new_pixmap = pixmap.scaled(40, 40)
            self.icon_label.setPixmap(new_pixmap)
        except Exception as e:
            print(f"Error loading microphone icon: {e}")
            self.icon_label.setText("Mic")
        self.icon_label.setFixedSize(50, 50)
        self.icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border-radius: 25px;
                padding: 5px;
                border: 1px solid #444444;
            }
            QLabel:hover {
                background: rgba(33, 150, 243, 76);
                border: 1px solid #2196f3;
            }
        """)
        self.icon_label.setAttribute(Qt.WA_MouseTracking, True)
        self.icon_label.setMouseTracking(True)
        self.icon_label.mousePressEvent = self.toggle_icon

        # Opacity effect for pulsing
        self.opacity_effect = QGraphicsOpacityEffect()
        self.icon_label.setGraphicsEffect(self.opacity_effect)
        self.pulse_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_animation.setStartValue(0.6)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setKeyValueAt(0.5, 1.0)
        self.pulse_animation.setKeyValueAt(1.0, 0.6)

        self.toggled = True
        self.toggle_icon()
        button_layout.addWidget(self.icon_label)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                background: rgba(0, 0, 0, 128);
                border-radius: 8px;
                padding: 5px 10px;
                border: 1px solid #444444;
            }
        """)
        self.status_label.setFixedSize(150, 25)
        self.status_label.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(self.status_label)

        layout.addLayout(button_layout)

        # GIF setup
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("""
            QLabel {
                border: 2px solid transparent;
                border-radius: 15px;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, 
                                            stop:0 #2196f3, stop:1 transparent);
                padding: 5px;
            }
        """)
        try:
            movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
            if not movie.isValid():
                raise ValueError("Failed to load Jarvis.gif")
            max_gif_size_W = 400
            max_gif_size_H = 225
            movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
            self.gif_label.setAlignment(Qt.AlignCenter)
            self.gif_label.setMovie(movie)
            movie.start()
        except Exception as e:
            print(f"Error loading GIF: {e}")
            self.gif_label.setText("GIF")
        layout.addWidget(self.gif_label)

        self.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1, 
                                            stop:0 #1c2526, stop:1 #121212);
            }
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def toggle_icon(self, event=None):
        if self.toggled:
            try:
                self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 40, 40)
                MicButtonClosed()
                self.pulse_animation.stop()
                self.opacity_effect.setOpacity(1.0)
            except Exception as e:
                print(f"Error toggling mic off: {e}")
        else:
            try:
                self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 40, 40)
                MicButtonInitialed()
                self.pulse_animation.start()
            except Exception as e:
                print(f"Error toggling mic on: {e}")
        self.toggled = not self.toggled

    def load_icon(self, path, width=40, height=40):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            raise ValueError(f"Failed to load icon: {path}")
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
                self.status_label.setText(messages)
        except Exception as e:
            print(f"Error reading status: {e}")
        self.update_mic_icon()

    def update_mic_icon(self):
        try:
            mic_status = GetMicrophoneStatus()
            if mic_status == "True" and not self.toggled:
                self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 40, 40)
                self.toggled = True
                self.pulse_animation.start()
            elif mic_status == "False" and self.toggled:
                self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 40, 40)
                self.toggled = False
                self.pulse_animation.stop()
                self.opacity_effect.setOpacity(1.0)
        except Exception as e:
            print(f"Error updating mic icon: {e}")

    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                text = file.read()
            if text is None or len(text.strip()) <= 1 or str(old_chat_message) == str(text):
                return
            senders = [Username, Assistantname]
            pattern = re.compile(
                r'^\s*({0})\s*:'.format("|".join([re.escape(sender) for sender in senders])),
                re.MULTILINE
            )
            matches = list(pattern.finditer(text))
            messages = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(text)
                msg = text[start:end].strip()
                messages.append(msg)
            for msg in messages:
                self.addMessage(message=msg)
            old_chat_message = text
        except Exception as e:
            print(f"Error loading messages: {e}")

    def addMessage(self, message):
        message = message.strip()
        if message.startswith(f"{Username}:"):
            color = "blue"
            alignment = Qt.AlignmentFlag.AlignLeft
        elif message.startswith(f"{Assistantname}:"):
            color = "green"
            alignment = Qt.AlignmentFlag.AlignRight
        else:
            color = "white"
            alignment = Qt.AlignmentFlag.AlignLeft
        cursor = self.chat_text_edit.textCursor()
        charFormat = QTextCharFormat()
        blockFormat = QTextBlockFormat()
        charFormat.setFontPointSize(14)
        blockFormat.setTopMargin(10)
        blockFormat.setLeftMargin(10)
        blockFormat.setAlignment(alignment)
        charFormat.setForeground(QColor(color))
        cursor.setBlockFormat(blockFormat)
        cursor.setCharFormat(charFormat)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

    def clear_chat(self):
        try:
            self.chat_text_edit.clear()
            global old_chat_message
            old_chat_message = ""
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Database.data'), "w", encoding='utf-8') as file:
                file.write("")
            with open(r'Data\ChatLog.json', "w", encoding='utf-8') as file:
                json.dump([], file)
        except Exception as e:
            print(f"Error clearing chat: {e}")

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        gif_label.setMovie(movie)
        max_gif_size_H = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
# Microphone icon setup
        self.icon_label = QLabel()
        pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
        new_pixmap = pixmap.scaled(60, 60)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Enable mouse events for the label
        self.icon_label.setAttribute(Qt.WA_MouseTracking, True)
        self.icon_label.setMouseTracking(True)
        self.icon_label.mousePressEvent = self.toggle_icon  # Assign the handler
        
        self.toggled = True
        self.toggle_icon()  # Initial call to set the state
        
        self.icon_label.mousePressEvent = self.toggle_icon
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-bottom:0;")
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)
        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: #121212;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            MicButtonClosed()  # Updates Mic.data and Status.data
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            MicButtonInitialed()  # Updates Mic.data and Status.data
        self.toggled = not self.toggled

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def SpeechRecogText(self):
        with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)
        self.update_mic_icon()

    def update_mic_icon(self):
        mic_status = GetMicrophoneStatus()
        if mic_status == "True" and not self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            self.toggled = True
        elif mic_status == "False" and self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            self.toggled = False



class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat section
        chat_section = ChatSection()
        layout.addWidget(chat_section, stretch=1)

        # Microphone icon setup (floating)
        self.icon_label = QLabel(self)
        pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
        new_pixmap = pixmap.scaled(40, 40)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(50, 50)
        self.icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border-radius: 25px;
                padding: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            QLabel:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        self.icon_label.setAttribute(Qt.WA_MouseTracking, True)
        self.icon_label.setMouseTracking(True)
        self.icon_label.mousePressEvent = self.toggle_icon
        self.icon_label.move(screen_width - 70, screen_height - 70)

        self.toggled = True
        self.toggle_icon()

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size:14px; background: transparent;")
        self.status_label.setFixedSize(150, 20)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.move(screen_width - 120, screen_height - 100)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #121212;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 40, 40)
            MicButtonClosed()
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 40, 40)
            MicButtonInitialed()
        self.toggled = not self.toggled

    def load_icon(self, path, width=40, height=40):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def SpeechRecogText(self):
        with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
            messages = file.read()
            self.status_label.setText(messages)
        self.update_mic_icon()

    def update_mic_icon(self):
        mic_status = GetMicrophoneStatus()
        if mic_status == "True" and not self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 40, 40)
            self.toggled = True
        elif mic_status == "False" and self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 40, 40)
            self.toggled = False
# ```
# class MessageScreen(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         desktop = QApplication.desktop()
#         screen_width = desktop.screenGeometry().width()
#         screen_height = desktop.screenGeometry().height()
#         layout = QVBoxLayout()
#         label = QLabel("")
#         layout.addWidget(label)
#         chat_section = ChatSection()
#         layout.addWidget(chat_section)
#         self.setLayout(layout)
#         self.setStyleSheet("background-color: #121212;")
#         self.setFixedHeight(screen_height)
#         self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("height:40px; line-height:40px ; background-color:white; color:black")
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText("  Chat")
        message_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color: black")
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath('Minimize2.png'))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicsDirectoryPath("Minimize.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath('Close.png'))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.closeWindow)
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        title_label = QLabel(f" {str(Assistantname).capitalize()} AI  ")
        title_label.setStyleSheet("color: black; font-size: 18px;; background-color:white")
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
        self.draggable = True  # Fix: Set draggable as a flag, not a method
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
        self.current_screen = initial_screen

class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent, flags)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: #121212;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

# def GraphicalUserInterface():
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     GraphicalUserInterface()


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    
    # Show the login screen first
    login_screen = LoginScreen()
    if login_screen.exec_() == QDialog.Accepted:
        # If login is successful, proceed to main GUI
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()