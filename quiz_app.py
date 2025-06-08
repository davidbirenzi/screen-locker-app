import sys
import random
import time
import ctypes
from ctypes import wintypes, c_int, c_void_p, POINTER, WINFUNCTYPE, windll
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QRadioButton, QButtonGroup, 
                           QMessageBox, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent, QFont, QPalette, QColor

# Windows API constants and types
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_D = 0x44

# Define callback function type
HOOKPROC = WINFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))

# Course-specific questions
COURSE_QUESTIONS = {
    "python": [
        {
            "question": "What is the output of print(type(1/2)) in Python?",
            "options": ["<class 'int'>", "<class 'float'>", "<class 'number'>", "<class 'decimal'>"],
            "correct": 1
        },
        {
            "question": "Which of the following is NOT a Python data type?",
            "options": ["List", "Dictionary", "Array", "Tuple"],
            "correct": 2
        },
        {
            "question": "What does the 'self' keyword represent in a Python class?",
            "options": ["The class itself", "The instance of the class", "A static method", "A class method"],
            "correct": 1
        },
        {
            "question": "Which method is used to add an element to a list in Python?",
            "options": ["add()", "insert()", "append()", "push()"],
            "correct": 2
        },
        {
            "question": "What is the correct way to create a virtual environment in Python?",
            "options": ["python -m venv env", "python create venv", "python -v environment", "python setup venv"],
            "correct": 0
        }
    ],
    "database": [
        {
            "question": "What does SQL stand for?",
            "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"],
            "correct": 0
        },
        {
            "question": "Which SQL command is used to insert new data into a database?",
            "options": ["ADD", "INSERT", "CREATE", "UPDATE"],
            "correct": 1
        },
        {
            "question": "What is a primary key in a database?",
            "options": ["A key that opens the database", "A unique identifier for each record", "The first column in a table", "A backup key"],
            "correct": 1
        },
        {
            "question": "Which of the following is NOT a type of database relationship?",
            "options": ["One-to-One", "One-to-Many", "Many-to-Many", "One-to-All"],
            "correct": 3
        },
        {
            "question": "What is normalization in database design?",
            "options": ["Making the database faster", "Organizing data to reduce redundancy", "Backing up the database", "Creating indexes"],
            "correct": 1
        }
    ],
    "web": [
        {
            "question": "What does HTML stand for?",
            "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Hyper Transfer Markup Language", "Hyper Text Modern Language"],
            "correct": 0
        },
        {
            "question": "Which CSS property is used to change the text color?",
            "options": ["text-color", "font-color", "color", "text-style"],
            "correct": 2
        },
        {
            "question": "What is the correct way to write a JavaScript array?",
            "options": ["var colors = (1:'red', 2:'green', 3:'blue')", "var colors = ['red', 'green', 'blue']", "var colors = 'red', 'green', 'blue'", "var colors = {1:'red', 2:'green', 3:'blue'}"],
            "correct": 1
        },
        {
            "question": "Which HTML tag is used to create a hyperlink?",
            "options": ["<link>", "<a>", "<href>", "<url>"],
            "correct": 1
        },
        {
            "question": "What is the purpose of the <meta> tag in HTML?",
            "options": ["To create a new page", "To add metadata about the document", "To create a table", "To add a style"],
            "correct": 1
        }
    ]
}

class QuizApp(QMainWindow):
    def __init__(self, course="python"):
        super().__init__()
        self.setWindowTitle(f"{course.title()} Programming Quiz")
        self.setFixedSize(900, 700)
        
        # Initialize Windows API
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        
        # Set up keyboard hook
        self.keyboard_hook = None
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #1a1a1a;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QRadioButton {
                spacing: 8px;
                font-size: 14px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #4a90e2;
                border-radius: 9px;
            }
            QRadioButton::indicator:checked {
                background-color: #4a90e2;
                border: 2px solid #4a90e2;
                border-radius: 9px;
            }
        """)
        
        # Load course-specific questions
        self.questions = COURSE_QUESTIONS.get(course.lower(), COURSE_QUESTIONS["python"])
        
        self.current_question = 0
        self.score = 0
        self.start_time = None
        self.quiz_started = False
        self.answers = [None] * len(self.questions)
        
        # Randomize questions
        random.shuffle(self.questions)
        
        self.init_ui()
        
    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel("General Knowledge Quiz")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 20px;
        """)
        self.layout.addWidget(title_label)
        
        # Instructions screen
        self.instructions_label = QLabel(
            "Welcome to the General Knowledge Quiz!\n\n"
            "Rules:\n"
            "- You have 10 minutes to complete the quiz\n"
            "- There are 10 multiple-choice questions\n"
            "- Once started, you cannot switch windows or minimize\n"
            "- You can submit early if all questions are answered\n"
            "- No changes are allowed after submission\n\n"
            "Click 'Start Quiz' when you're ready!"
        )
        self.instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("""
            font-size: 16px;
            line-height: 1.5;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        """)
        self.layout.addWidget(self.instructions_label)
        
        # Start button
        self.start_button = QPushButton("Start Quiz")
        self.start_button.setStyleSheet("""
            font-size: 18px;
            padding: 12px 24px;
            min-width: 200px;
        """)
        self.start_button.clicked.connect(self.start_quiz)
        self.layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Quiz elements (initially hidden)
        self.question_frame = QFrame()
        self.question_frame.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 20px;
        """)
        question_layout = QVBoxLayout(self.question_frame)
        question_layout.setSpacing(15)
        
        self.question_label = QLabel()
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1a1a1a;
        """)
        question_layout.addWidget(self.question_label)
        
        self.option_group = QButtonGroup()
        self.option_buttons = []
        for i in range(4):
            option = QRadioButton()
            self.option_buttons.append(option)
            self.option_group.addButton(option, i)
            option.setStyleSheet("""
                font-size: 16px;
                padding: 8px;
            """)
            question_layout.addWidget(option)
        
        self.layout.addWidget(self.question_frame)
        
        # Navigation buttons
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(10)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.setStyleSheet("""
            min-width: 120px;
        """)
        self.prev_button.clicked.connect(self.prev_question)
        
        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet("""
            min-width: 120px;
        """)
        self.next_button.clicked.connect(self.next_question)
        
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)
        
        # Timer and submit section
        bottom_layout = QHBoxLayout()
        
        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4a90e2;
        """)
        bottom_layout.addWidget(self.timer_label)
        
        self.submit_button = QPushButton("Submit Quiz")
        self.submit_button.setStyleSheet("""
            min-width: 150px;
            background-color: #2ecc71;
        """)
        self.submit_button.clicked.connect(self.submit_quiz)
        bottom_layout.addWidget(self.submit_button)
        
        self.layout.addLayout(bottom_layout)
        
        # Hide quiz elements initially
        self.hide_quiz_elements()
        
    def hide_quiz_elements(self):
        self.question_frame.hide()
        self.timer_label.hide()
        self.submit_button.hide()
        self.prev_button.hide()
        self.next_button.hide()
        
    def show_quiz_elements(self):
        self.question_frame.show()
        self.timer_label.show()
        self.submit_button.show()
        self.prev_button.show()
        self.next_button.show()
        
    def start_quiz(self):
        self.quiz_started = True
        self.start_time = time.time()
        self.instructions_label.hide()
        self.start_button.hide()
        self.show_quiz_elements()
        
        # Set up keyboard hook when quiz starts
        self.setup_keyboard_hook()
        
        # Enter fullscreen mode and set window flags
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.showFullScreen()
        
        # Force window to stay on top
        self.user32.SetWindowPos(
            self.winId(),
            -1,  # HWND_TOPMOST
            0, 0, 0, 0,
            0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
        )
        
        # Disable task switching
        self.user32.SystemParametersInfoW(0x101F, 0, None, 0)  # SPI_SETSCREENSAVERRUNNING
        
        # Start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every second
        
        self.display_question()
        
    def update_timer(self):
        if not self.quiz_started:
            return
            
        elapsed = time.time() - self.start_time
        remaining = max(600 - int(elapsed), 0)  # 10 minutes = 600 seconds
        
        if remaining == 0:
            self.submit_quiz()
            return
            
        minutes = remaining // 60
        seconds = remaining % 60
        self.timer_label.setText(f"Time remaining: {minutes:02d}:{seconds:02d}")
        
    def display_question(self):
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            self.question_label.setText(f"Question {self.current_question + 1}: {question['question']}")
            
            for i, option in enumerate(question['options']):
                self.option_buttons[i].setText(option)
                self.option_buttons[i].setChecked(False)
                
            # Restore previous answer if exists
            if self.answers[self.current_question] is not None:
                self.option_buttons[self.answers[self.current_question]].setChecked(True)
                
            # Update navigation buttons state
            self.prev_button.setEnabled(self.current_question > 0)
            self.next_button.setEnabled(self.current_question < len(self.questions) - 1)
            
    def next_question(self):
        # Save current answer
        checked_button = self.option_group.checkedButton()
        if checked_button:
            self.answers[self.current_question] = self.option_group.id(checked_button)
        
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            self.display_question()
            
    def prev_question(self):
        # Save current answer
        checked_button = self.option_group.checkedButton()
        if checked_button:
            self.answers[self.current_question] = self.option_group.id(checked_button)
            
        if self.current_question > 0:
            self.current_question -= 1
            self.display_question()
            
    def setup_keyboard_hook(self):
        """Set up low-level keyboard hook to block Windows key and Windows+D"""
        def keyboard_callback(nCode, wParam, lParam):
            if nCode >= 0:
                # Get the key code
                key_code = ctypes.cast(lParam, POINTER(c_int))[0]
                
                # Block all system keys
                if (wParam == WM_KEYDOWN or wParam == WM_SYSKEYDOWN):
                    # Block Windows key
                    if key_code == VK_LWIN or key_code == VK_RWIN:
                        return 1
                    # Block Windows+D
                    if key_code == VK_D:
                        if (self.user32.GetAsyncKeyState(VK_LWIN) & 0x8000 or 
                            self.user32.GetAsyncKeyState(VK_RWIN) & 0x8000):
                            return 1
                    # Block Alt+Tab
                    if key_code == 0x09:  # VK_TAB
                        if self.user32.GetAsyncKeyState(0x12) & 0x8000:  # VK_ALT
                            return 1
                    # Block Alt+Esc
                    if key_code == 0x1B:  # VK_ESCAPE
                        if self.user32.GetAsyncKeyState(0x12) & 0x8000:  # VK_ALT
                            return 1
                    # Block Ctrl+Esc
                    if key_code == 0x1B:  # VK_ESCAPE
                        if self.user32.GetAsyncKeyState(0x11) & 0x8000:  # VK_CONTROL
                            return 1
            return self.user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)
        
        # Create the hook
        self.keyboard_hook = self.user32.SetWindowsHookExA(
            WH_KEYBOARD_LL,
            HOOKPROC(keyboard_callback),
            self.kernel32.GetModuleHandleW(None),
            0
        )
        
        # Additional system-level blocking
        self.user32.BlockInput(True)
        
    def remove_keyboard_hook(self):
        """Remove the keyboard hook"""
        if self.keyboard_hook:
            self.user32.UnhookWindowsHookEx(self.keyboard_hook)
            self.keyboard_hook = None
            # Re-enable input
            self.user32.BlockInput(False)
            # Re-enable task switching
            self.user32.SystemParametersInfoW(0x101F, 1, None, 0)  # SPI_SETSCREENSAVERRUNNING
            
    def closeEvent(self, event):
        """Clean up when the application is closed"""
        self.remove_keyboard_hook()
        event.accept()
        
    def keyPressEvent(self, event: QKeyEvent):
        if self.quiz_started:
            # Block Alt+Tab, Windows key, Windows+D, and other window switching shortcuts
            if (event.key() in [Qt.Key.Key_Alt, Qt.Key.Key_Tab, Qt.Key.Key_Escape, 
                              Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R] or
                (event.key() == Qt.Key.Key_D and 
                 (event.modifiers() & Qt.KeyboardModifier.MetaModifier or 
                  event.modifiers() & Qt.KeyboardModifier.ControlModifier))):
                event.ignore()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def submit_quiz(self):
        if not self.quiz_started:
            return
            
        self.quiz_started = False
        self.timer.stop()
        
        # Save current answer
        checked_button = self.option_group.checkedButton()
        if checked_button:
            self.answers[self.current_question] = self.option_group.id(checked_button)
        
        # Calculate score
        self.score = 0
        for i, question in enumerate(self.questions):
            if self.answers[i] is not None and self.answers[i] == question['correct']:
                self.score += 1
                
        # Calculate time taken
        time_taken = time.time() - self.start_time
        minutes = int(time_taken) // 60
        seconds = int(time_taken) % 60
        
        # Send grade to web application
        try:
            import requests
            grade_data = {
                'course': self.course,
                'score': self.score,
                'total_questions': len(self.questions)
            }
            requests.post('http://127.0.0.1:5000/submit_grade', json=grade_data)
        except Exception as e:
            print(f"Error submitting grade: {e}")
        
        # Show results
        QMessageBox.information(
            self,
            "Quiz Results",
            f"Quiz completed!\n\n"
            f"Score: {self.score}/{len(self.questions)}\n"
            f"Time taken: {minutes:02d}:{seconds:02d}"
        )
        
        # Exit fullscreen
        self.showNormal()
        
        # Remove keyboard hook before closing
        self.remove_keyboard_hook()
        
        # Close the application
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Get course from command line argument if provided
    course = sys.argv[1] if len(sys.argv) > 1 else "python"
    window = QuizApp(course)
    window.show()
    sys.exit(app.exec()) 