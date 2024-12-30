import sys
import subprocess
import json
import os
import psutil
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QFrame, QMainWindow, QStatusBar, QTextEdit, QFileDialog, QInputDialog,
    QFileSystemModel, QTreeView, QScrollArea, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap
from PyQt5.QtCore import Qt, QTimer, QModelIndex, QDir, QByteArray

class SILAApp(QMainWindow):
    WINDOW_TITLE = 'Studio Instrument Launch Assistant - SILA v4.0'
    JSON_FILE_NAME = 'instruments.json'
    STATUS_BAR_COLOR = "#FFDD44"
    BUTTON_STYLE = """
        QPushButton { background-color: #444444; color: white; padding: 10px; border-radius: 5px; }
        QPushButton:hover { background-color: #666666; }
    """
    ICON_BASE64 = ""

    def __init__(self):
        super().__init__()
        self.instruments = {}
        self.json_file_path = os.path.join(os.path.expanduser('~'), self.JSON_FILE_NAME)
        self.selected_exe_path = None
        self.process_states = {}
        self.initUI()
        self.load_instruments()
        self.find_vst_plugins()

        # Timer to check running processes
        self.check_processes_timer = QTimer(self)
        self.check_processes_timer.timeout.connect(self.check_running_processes)
        self.check_processes_timer.start(1000)

    def find_vst_plugins(self):
        """Looks for VST2 and VST3 plugins in common paths and adds them to the instrument list."""
        vst_paths = [
            os.path.join(os.getenv("ProgramFiles"), "VSTPlugins"),
            os.path.join(os.getenv("ProgramFiles(x86)"), "VSTPlugins"),
            os.path.join(os.getenv("ProgramFiles"), "Common Files", "VST3"),
            os.path.join(os.getenv("ProgramFiles(x86)"), "Common Files", "VST3"),
        ]

        for path in vst_paths:
            if os.path.exists(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith(".dll"):
                            instrument_name = file.replace(".dll", "")
                            file_path = os.path.join(root, file)
                            if instrument_name not in self.instruments:
                                self.instruments[instrument_name] = file_path
                                self.create_instrument_button(instrument_name, file_path)
                                self.log_info(f"Found VST: {instrument_name} at {file_path}")

        self.save_instruments()

    def initUI(self):
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setFixedSize(950, 600)
        self.setWindowIcon(self.load_icon_from_base64(self.ICON_BASE64))
        self.setPalette(self.create_palette())

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(self.create_file_explorer_layout())
        main_layout.addLayout(self.create_main_content_layout())

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_icon_from_base64(self, base64_data):
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(base64_data.encode()))
        return QIcon(pixmap)

    def create_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.Text, QColor(255, 255, 0))
        return palette

    def create_file_explorer_layout(self):
        file_explorer_layout = QVBoxLayout()
        file_explorer_layout.addWidget(self.create_label("File Explorer"))

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(QDir.rootPath()))
        self.file_tree.setColumnWidth(0, 200)
        self.file_tree.setSelectionMode(QTreeView.SingleSelection)
        self.file_tree.clicked.connect(self.on_file_selected)

        button_layout = QHBoxLayout()
        back_button = QPushButton("Back", self)
        back_button.setStyleSheet(self.BUTTON_STYLE)
        back_button.clicked.connect(self.go_back)
        button_layout.addWidget(back_button)

        home_button = QPushButton("Go to Root", self)
        home_button.setStyleSheet(self.BUTTON_STYLE)
        home_button.clicked.connect(self.go_to_root)
        button_layout.addWidget(home_button)

        file_explorer_layout.addWidget(self.file_tree)
        file_explorer_layout.addLayout(button_layout)
        file_explorer_layout.addWidget(self.create_button("Add from Explorer", self.add_instrument_from_explorer))

        return file_explorer_layout

    def create_main_content_layout(self):
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.create_welcome_label())
        right_layout.addWidget(self.create_separator_line())

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.instrument_widget = QWidget()
        self.instrument_layout = QVBoxLayout(self.instrument_widget)
        self.scroll_area.setWidget(self.instrument_widget)
        right_layout.addWidget(self.scroll_area)

        self.log_area = self.create_log_area()
        right_layout.addWidget(self.create_scroll_area(self.log_area))
        right_layout.addLayout(self.create_button_layout())

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        return right_layout

    def create_welcome_label(self):
        welcome_label = QLabel("SILA", self)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #FFDD44; font-size: 18px; font-weight: bold;")
        return welcome_label

    def create_label(self, text, font_size=14, bold=True):
        label = QLabel(text, self)
        font = QFont('Arial', font_size, QFont.Bold if bold else QFont.Normal)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {self.STATUS_BAR_COLOR};")
        return label

    def create_separator_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: gray;")
        return line

    def create_log_area(self):
        log_area = QTextEdit(self)
        log_area.setReadOnly(True)
        log_area.setFont(QFont('Consolas', 10))
        log_area.setStyleSheet("background-color: #1C1C1C; color: yellow;")
        return log_area

    def create_scroll_area(self, widget):
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        return scroll_area

    def create_button_layout(self):
        button_layout = QHBoxLayout()

        buttons = [
            ("Add Instrument", self.add_instrument),
            ("Export to CSV", self.export_to_csv),
            ("Settings", self.open_settings)
        ]

        for text, callback in buttons:
            button = self.create_button(text, callback)
            button_layout.addWidget(button)

        return button_layout

    def create_button(self, text, callback):
        button = QPushButton(text, self)
        button.setStyleSheet(self.BUTTON_STYLE)
        button.clicked.connect(callback)
        return button

    def load_instruments(self):
        if not os.path.exists(self.json_file_path):
            self.instruments = {}
            self.save_instruments()
            return

        try:
            with open(self.json_file_path, 'r') as f:
                self.instruments = json.load(f)
            self.update_instrument_buttons()
        except json.JSONDecodeError:
            self.log_error("Error decoding JSON. Creating a new instruments file.")
            self.instruments = {}
            self.save_instruments()
        except Exception as e:
            self.log_error(f"Error loading instruments: {e}. Creating a new one.")
            self.instruments = {}
            self.save_instruments()

    def update_instrument_buttons(self):
        self.clear_instrument_buttons()
        for instrument_name, exe_path in self.instruments.items():
            self.create_instrument_button(instrument_name, exe_path)

    def clear_instrument_buttons(self):
        while self.instrument_layout.count():
            widget = self.instrument_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def create_instrument_button(self, instrument_name, exe_path):
        button_layout = QHBoxLayout()
        
        status_indicator = QLabel()
        status_indicator.setFixedSize(10, 10)
        status_indicator.setStyleSheet("background-color: red; border-radius: 5px;")
        
        display_name = instrument_name.replace('.exe', '')
        button = self.create_button(display_name, lambda: self.launch_instrument(exe_path, display_name, status_indicator))
        button_layout.addWidget(button)
        button_layout.addWidget(status_indicator)

        remove_button = self.create_button("Delete", lambda: self.remove_instrument(instrument_name, button_layout))
        button_layout.addWidget(remove_button)

        self.instrument_layout.addLayout(button_layout)
        self.process_states[instrument_name] = False

    def check_running_processes(self):
        for instrument_name, exe_path in self.instruments.items():
            is_running = self.is_process_running(exe_path)
            self.process_states[instrument_name] = is_running
            self.update_instrument_status_indicator(instrument_name, is_running)

    def update_instrument_status_indicator(self, instrument_name, is_running):
        for i in range(self.instrument_layout.count()):
            layout = self.instrument_layout.itemAt(i).layout()
            if layout:
                button = layout.itemAt(0).widget()
                if button and button.text() == instrument_name:
                    indicator = layout.itemAt(1).widget()
                    if indicator:
                        indicator.setStyleSheet("background-color: green; border-radius: 5px;" if is_running else "background-color: red; border-radius: 5px;")

    def is_process_running(self, exe_path):
        """Checks if a process with the specified path is running."""
        for process in psutil.process_iter(attrs=["exe"]):
            if process.info.get("exe") == exe_path:
                return True
        return False

    def log_info(self, message):
        self.log_area.append(f"[INFO] {message}")

    def log_error(self, message):
        self.log_area.append(f"[ERROR] {message}")

    def add_instrument_from_explorer(self):
        if self.selected_exe_path:
            text, ok = QInputDialog.getText(self, 'Add Instrument', 'Name of the instrument:')
            if ok and text:
                if text not in self.instruments:
                    self.instruments[text] = self.selected_exe_path
                    self.save_instruments()
                    self.create_instrument_button(text, self.selected_exe_path)
                    self.log_info(f"Added instrument: {text}")
                else:
                    self.log_error("Instrument already exists.")
        else:
            self.log_error("No executable selected.")

    def add_instrument(self):
        text, ok = QInputDialog.getText(self, 'Add Instrument', 'Name of the instrument:')
        if ok and text:
            if text not in self.instruments:
                if self.selected_exe_path:
                    self.instruments[text] = self.selected_exe_path
                    self.save_instruments()
                    self.create_instrument_button(text, self.selected_exe_path)
                    self.log_info(f"Added instrument: {text}")
                else:
                    self.log_error("No executable selected.")
            else:
                self.log_error("Instrument already exists.")

    def export_to_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Instrument Name", "Executable Path"])
                    for name, path in self.instruments.items():
                        writer.writerow([name, path])
                self.log_info("Instruments exported successfully.")
            except Exception as e:
                self.log_error(f"Error exporting to CSV: {e}")

    def open_settings(self):
        self.log_info("Settings window opened.")  # Placeholder for settings functionality


    def on_file_selected(self, index: QModelIndex):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path) and file_path.endswith('.exe'):
            self.selected_exe_path = file_path
            self.log_info(f"Select: {file_path}")

    def go_back(self):
        current_index = self.file_tree.currentIndex()
        if current_index.isValid():
            parent_index = current_index.parent()
            if parent_index.isValid():
                self.file_tree.setRootIndex(parent_index)
            else:
                self.log_info("No back to skip.")

    def go_to_root(self):
        self.file_tree.setRootIndex(self.file_model.index(QDir.rootPath()))

    def launch_instrument(self, exe_path, name, status_indicator):
        if not os.path.exists(exe_path):
            self.log_error(f"Executable not found: {exe_path}")
            return

        try:
            # Ejecutar el proceso de manera segura
            process = subprocess.Popen([exe_path])
            self.process_states[name] = True
            self.update_status_indicator(status_indicator, True)
            self.log_info(f"{name} launched successfully.")
        except Exception as e:
            # Capturar cualquier error y loguearlo
            self.log_error(f"Failed to launch {name}: {e}")

    def remove_instrument(self, name, button_layout):
        reply = QMessageBox.question(self, 'Remove Instrument',
                                     f"Are you sure to remove {name}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.instruments[name]
            self.save_instruments()
            for i in reversed(range(button_layout.count())):
                widget = button_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            self.log_info(f"Removed instrument: {name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SILAApp()
    window.show()
    sys.exit(app.exec_())
