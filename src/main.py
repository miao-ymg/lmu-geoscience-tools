import sys
import os
import re
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

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
            
            # Find all definitions like `@var-name: #hexcode;`
            variables = re.findall(r'(@[\w-]+):\s*([^;]+);', content)
            
            # Replace all occurrences of the variables in the rest of the file
            for var_name, var_value in variables:
                content = content.replace(var_name, var_value.strip())
                
            return content
    except Exception as e:
        print(f"Could not load stylesheet: {e}")
        return ""

def main():
    app = QApplication(sys.argv)
    
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
