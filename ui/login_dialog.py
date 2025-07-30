from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class LoginDialog(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("Login - Facebook Marketplace Bot")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Facebook Marketplace Bot Login")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email")
        layout.addWidget(self.email_edit)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        layout.addWidget(self.password_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        button_layout.addWidget(self.login_btn)
        
        layout.addLayout(button_layout)
        
        # Connect enter key
        self.password_edit.returnPressed.connect(self.login)
    
    def login(self):
        """Handle login"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return
        
        self.login_btn.setText("Logging in...")
        self.login_btn.setEnabled(False)
        
        success, message = self.auth_manager.login(email, password)
        
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", message)
            self.login_btn.setText("Login")
            self.login_btn.setEnabled(True)
