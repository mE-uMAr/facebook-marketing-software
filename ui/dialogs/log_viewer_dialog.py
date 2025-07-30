from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class LogViewerDialog(QDialog):
    def __init__(self, log_content, parent=None):
        super().__init__(parent)
        self.log_content = log_content
        
        self.setWindowTitle("All Logs")
        self.setGeometry(200, 200, 800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setPlainText(self.log_content)
        layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_logs)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def save_logs(self):
        """Save logs to file"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Logs", "logs.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.log_content)
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Logs saved successfully.")
                
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", f"Failed to save logs: {str(e)}")
