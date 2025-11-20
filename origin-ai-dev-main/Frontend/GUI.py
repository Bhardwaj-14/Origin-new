from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QTimer, QSize
from dotenv import dotenv_values
import sys
import os

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}/Frontend/Files"
GraphicsDirPath = rf"{current_dir}/Frontend/Graphics"

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
    os.makedirs(TempDirPath, exist_ok=True)
    with open(rf'{TempDirPath}/Mic.data', "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf"{TempDirPath}/Mic.data", "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    os.makedirs(TempDirPath, exist_ok=True)
    with open(rf"{TempDirPath}/Status.data", "w", encoding='utf-8') as file:
        file.write(Status)

def SetMicPendingState(state):
    os.makedirs(TempDirPath, exist_ok=True)
    with open(rf"{TempDirPath}/MicPending.data", "w", encoding='utf-8') as file:
        file.write(state)

def GetMicPendingState():
    try:
        with open(rf"{TempDirPath}/MicPending.data", "r", encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

def GetAssistantStatus():
    with open(rf"{TempDirPath}/Status.data", "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def MicButtonInitialised():
    current_status = GetAssistantStatus()
    busy_states = ["Thinking", "Answering", "Searching"]
    if any(state in current_status for state in busy_states):
        SetMicPendingState("True")
        SetAssistantStatus("Will resume listening after this response...")
    else:
        SetMicPendingState("")
        SetMicrophoneStatus("True")
        SetAssistantStatus("Listening... ")

def MicButtonClosed():
    current_status = GetAssistantStatus()
    busy_states = ["Thinking", "Answering", "Searching"]
    if any(state in current_status for state in busy_states):
        SetMicPendingState("False")
        SetAssistantStatus("Will stop listening after this response...")
    else:
        SetMicPendingState("")
        SetMicrophoneStatus("False")
        SetAssistantStatus("Available ... ")

def GraphicDirectoryPath(Filename):
    Path = rf'{GraphicsDirPath}/{Filename}'
    return Path

def TempDirectoryPath(Filename):
    Path = rf"{TempDirPath}/{Filename}"
    return Path

def ShowTextToScreen(Text):
    os.makedirs(TempDirPath, exist_ok=True)
    with open(rf"{TempDirPath}/Responses.data", "w", encoding='utf-8') as file:
        file.write(Text)

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()

        # Main layout for the chat section
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Chat text area
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet("background-color: black; color: white; border: none;")
        layout.addWidget(self.chat_text_edit)

        # Setting default font and text color
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        text_color_format = QTextCharFormat()
        text_color_format.setForeground(QColor(Qt.blue))
        self.chat_text_edit.setCurrentCharFormat(text_color_format)

        # GIF Label
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicDirectoryPath("Jarvis.gif"))
        movie.setScaledSize(QSize(480, 270))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)

        # Placeholder Label
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px; border: none; margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        # Timer to handle dynamic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.speechRecognitionText)
        self.timer.start(100)
        self.chat_text_edit.viewport().installEventFilter(self)

        # Scrollbar styling
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                height: 10px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def loadMessages(self):
        global old_chat_message

        with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
            messages = file.read()

            if messages and str(old_chat_message) != str(messages):
                self.addMessage(message=messages, color='White')
                old_chat_message = messages

    def speechRecognitionText(self):
        with open(TempDirectoryPath("Status.data"), "r", encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        text_format = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)
        text_format.setForeground(QColor(color))
        cursor.setCharFormat(text_format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Add GIF
        gif_label = QLabel()
        movie = QMovie(GraphicDirectoryPath('Jarvis.gif'))
        gif_label.setMovie(movie)
        max_gif_size_H = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add icon
        self.icon_label = QLabel()
        pixmap = QPixmap(GraphicDirectoryPath('Mic_on.png'))
        new_pixmap = pixmap.scaled(60, 60)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # Toggle state
        self.toggle = False
        self.toggle_icon()  # Initialize with microphone ON
        self.icon_label.mousePressEvent = self.toggle_icon

        # Add text label
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-bottom: 0;")

        # Add widgets to layout
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)

        # Set up layout and window properties
        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")

        # Timer for updating speech recognition text
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)

    def SpeechRecogText(self):
        with open(TempDirectoryPath('Status.data'), 'r', encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        self.toggle = not self.toggle  # Toggle the state
        if self.toggle:
            self.load_icon(GraphicDirectoryPath('Mic_on.png'), 60, 60)
            MicButtonInitialised()
        else:
            self.load_icon(GraphicDirectoryPath('Mic_off.png'), 60, 60)
            MicButtonClosed()


class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Get screen dimensions
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        # Set up layout
        layout = QVBoxLayout()

        # Add a label
        label = QLabel("")
        layout.addWidget(label)

        # Add chat section
        chat_section = ChatSection()
        layout.addWidget(chat_section)  # Fixed method name: addWidget (not addWidgets)

        # Set layout and styling
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBarWidget(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)

        # Home Button
        home_button = QPushButton()
        home_icon = QIcon(GraphicDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText("  Home")
        home_button.setStyleSheet("height: 40px; line-height: 40px; background-color: white; color: black")
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))  # Fixed connection method

        # Message Button
        message_button = QPushButton()
        message_icon = QIcon(GraphicDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText("  Chat")  # Fixed method name
        message_button.setStyleSheet("height: 40px; line-height: 40px; background-color: white; color: black")
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        # Minimize Button
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicDirectoryPath("Minimize2.png"))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color: white")
        minimize_button.clicked.connect(self.minimizeWindow)

        # Maximize/Restore Button
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicDirectoryPath("Minimize.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color: white")
        self.maximize_button.clicked.connect(self.maximizeWindow)

        # Close Button
        close_button = QPushButton()
        close_icon = QIcon(GraphicDirectoryPath("Close.png"))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color: white")
        close_button.clicked.connect(self.closeWindow)

        # Line Frame
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")

        # Title Label
        title_label = QLabel(f"{str(Assistantname).capitalize()} AI   ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color: white")

        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)

        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()  # Fixed typo: `parnet` to `parent`
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
            layout.addWidget(initial_screen)  # Fixed method name: `addwidget` to `addWidget`
        self.current_screen = initial_screen  # Fixed typo: `curent_screen` to `current_screen`

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        # Create a stacked widget for managing screens
        stacked_widget = QStackedWidget(self)

        # Add screens to the stacked widget
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)

        # Set main window properties
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

        # Add custom top bar
        top_bar = CustomTopBarWidget(self, stacked_widget)
        self.setMenuWidget(top_bar)

        # Set stacked widget as the central widget
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface(on_ready=None):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if on_ready is not None:
        QTimer.singleShot(1000, on_ready)
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()