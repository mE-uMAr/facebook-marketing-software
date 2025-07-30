import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from ui.main_window import MainWindow
from database.db_manager import DatabaseManager
from auth.auth_manager import AuthManager

class FacebookMarketplaceApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Facebook Marketing Bot")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Dev")
        
        self.db_manager = DatabaseManager()
        self.db_manager.init_database()
        
        self.auth_manager = AuthManager()
        
        self.main_window = MainWindow(self.db_manager, self.auth_manager)
        
        self.setStyleSheet(self.load_stylesheet())
        
    def load_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #0078d4;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
        
        QTableWidget {
            gridline-color: #e0e0e0;
            background-color: white;
            alternate-background-color: #f8f8f8;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QTextEdit {
            border: 1px solid #ccc;
            background-color: white;
            font-family: 'Consolas', monospace;
        }
        """

def main():
    # Add the project root to the Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    app = FacebookMarketplaceApp(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Create and show main window
    window = MainWindow(db_manager, auth_manager)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
