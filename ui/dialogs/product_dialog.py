from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QTextEdit, QFileDialog, QMessageBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os

class ProductDialog(QDialog):
    def __init__(self, db_manager, parent=None, product_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product_data = product_data
        self.is_edit_mode = product_data is not None
        self.product_id = None
        
        self.setWindowTitle("Edit Product" if self.is_edit_mode else "Add Product")
        self.setFixedSize(500, 600)
        
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_product_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with close button
        header_layout = QHBoxLayout()
        title = QLabel("Edit Product" if self.is_edit_mode else "Add Product")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Product Name
        layout.addWidget(QLabel("Product Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Price
        layout.addWidget(QLabel("Price:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$")
        layout.addWidget(self.price_spin)
        
        # Category
        layout.addWidget(QLabel("Category:"))
        self.category_edit = QLineEdit()
        layout.addWidget(self.category_edit)
        
        # Tags
        layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma separated tags")
        layout.addWidget(self.tags_edit)
        
        # Location
        layout.addWidget(QLabel("Location:"))
        self.location_edit = QLineEdit()
        layout.addWidget(self.location_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(self.description_edit)
        
        # Images Folder
        layout.addWidget(QLabel("Images Folder:"))
        images_layout = QHBoxLayout()
        self.images_edit = QLineEdit()
        self.images_edit.setReadOnly(True)
        images_layout.addWidget(self.images_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_images_folder)
        images_layout.addWidget(browse_btn)
        
        layout.addLayout(images_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_product)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_product_data(self):
        """Load existing product data"""
        self.name_edit.setText(self.product_data['name'])
        self.price_spin.setValue(self.product_data['price'])
        self.category_edit.setText(self.product_data['category'] or "")
        self.tags_edit.setText(self.product_data['tags'] or "")
        self.location_edit.setText(self.product_data['location'] or "")
        self.description_edit.setPlainText(self.product_data['description'] or "")
        self.images_edit.setText(self.product_data['images_folder'] or "")
        self.product_id = self.product_data['id']
    
    def browse_images_folder(self):
        """Browse for images folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if folder:
            self.images_edit.setText(folder)
    
    def save_product(self):
        """Save product data"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required.")
            return
        
        price = self.price_spin.value()
        if price <= 0:
            QMessageBox.warning(self, "Error", "Price must be greater than 0.")
            return
        
        category = self.category_edit.text().strip()
        tags = self.tags_edit.text().strip()
        location = self.location_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        images_folder = self.images_edit.text().strip()
        
        # Validate images folder if provided
        if images_folder and not os.path.exists(images_folder):
            QMessageBox.warning(self, "Error", "Images folder does not exist.")
            return
        
        try:
            if self.is_edit_mode:
                # Update existing product
                self.db_manager.execute_update(
                    "UPDATE products SET name = ?, price = ?, category = ?, tags = ?, location = ?, description = ?, images_folder = ? WHERE id = ?",
                    (name, price, category, tags, location, description, images_folder, self.product_data['id'])
                )
                self.product_id = self.product_data['id']
            else:
                # Create new product
                self.product_id = self.db_manager.add_product(
                    name, price, description, category, tags, location, images_folder
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save product: {str(e)}")
    
    def get_product_id(self):
        """Get the product ID after saving"""
        return self.product_id
