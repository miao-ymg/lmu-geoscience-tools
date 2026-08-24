import sys
import os
import re
import subprocess
import matplotlib
matplotlib.use('Agg')
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

from theme import COLORS

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_stylesheet(style_path):
    """Loads a QSS file and parses custom @variables."""
    try:
        with open(style_path, "r") as f:
            content = f.read()
            
            # Sort variables by length descending to prevent partial replacement
            # (e.g. replacing @toggle-bg inside @toggle-bg-hover)
            variables = sorted(COLORS.items(), key=lambda x: len(x[0]), reverse=True)
            
            # Replace all occurrences of the variables in the rest of the file
            for var_name, var_value in variables:
                content = content.replace(var_name, var_value.strip())
                
            return content
    except Exception as e:
        print(f"Could not load stylesheet: {e}")
        return ""

def main():
    # Remove macOS quarantine flags from bundled dynamic libraries to prevent 30s Gatekeeper freezes
    if sys.platform == 'darwin' and getattr(sys, 'frozen', False):
        try:
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            if app_path.endswith('.app'):
                subprocess.run(['xattr', '-rc', app_path], capture_output=True)
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    # Load custom IBM Plex fonts
    from PyQt6.QtGui import QFontDatabase, QFont
    fonts_dir = resource_path(os.path.join("resources", "fonts"))
    if os.path.exists(fonts_dir):
        for font_file in os.listdir(fonts_dir):
            if font_file.endswith(".ttf") or font_file.endswith(".otf"):
                QFontDatabase.addApplicationFont(os.path.join(fonts_dir, font_file))
                
    # Set global default application font to IBM Plex Sans
    default_font = QFont("IBM Plex Sans", 14)
    app.setFont(default_font)
    
    # Load and apply QSS stylesheet
    style_path = resource_path(os.path.join("resources", "style.qss"))
    stylesheet = load_stylesheet(style_path)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
