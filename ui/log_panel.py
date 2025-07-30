from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont, QTextCursor

class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Logs")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)
        
        # Show All button
        show_all_btn = QPushButton("Show All")
        show_all_btn.clicked.connect(self.show_all_logs)
        header_layout.addWidget(show_all_btn)
        
        layout.addLayout(header_layout)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
    
    def add_log(self, message, level="INFO"):
        """Add a log message"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        
        # Limit log size (keep last 1000 lines)
        if self.log_text.document().blockCount() > 1000:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.removeSelectedText()
    
    def clear_logs(self):
        """Clear all logs"""
        self.log_text.clear()
    
    def show_all_logs(self):
        """Show all logs in a separate window"""
        from .dialogs.log_viewer_dialog import LogViewerDialog
        dialog = LogViewerDialog(self.log_text.toPlainText(), self)
        dialog.exec_()
