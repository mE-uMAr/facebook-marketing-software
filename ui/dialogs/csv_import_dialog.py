from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt
import csv
import os

class CSVImportDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.imported_product_ids = []
        
        self.setWindowTitle("Import Products from CSV")
        self.setFixedSize(700, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("CSV should contain columns: Product Name, Price, Tags, Category, Description, Images Folder, Location")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)
        
        browse_btn = QPushButton("Browse CSV File")
        browse_btn.clicked.connect(self.browse_csv_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Preview table
        layout.addWidget(QLabel("Preview:"))
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_products)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
    
    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.file_label.setText(os.path.basename(file_path))
            self.csv_file_path = file_path
            self.preview_csv()
    
    def preview_csv(self):
        """Preview CSV content"""
        try:
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
            
            if not rows:
                QMessageBox.warning(self, "Error", "CSV file is empty.")
                return
            
            # Check for required columns (flexible naming)
            headers = list(rows[0].keys())
            required_found = False
            
            for header in headers:
                if any(req in header.lower() for req in ['name', 'product']):
                    required_found = True
                    break
            
            if not required_found:
                QMessageBox.warning(self, "Warning", "CSV should contain a product name column (e.g., 'Product Name', 'Name', etc.)")
            
            # Set up table
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            self.preview_table.setRowCount(min(len(rows), 10))  # Show first 10 rows
            
            # Fill table
            for row_idx, row_data in enumerate(rows[:10]):
                for col_idx, header in enumerate(headers):
                    item = QTableWidgetItem(str(row_data.get(header, "")))
                    self.preview_table.setItem(row_idx, col_idx, item)
            
            # Resize columns
            header = self.preview_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            
            self.import_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read CSV file: {str(e)}")
    
    def import_products(self):
        """Import products from CSV"""
        try:
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
        
            if not rows:
                QMessageBox.warning(self, "Error", "CSV file is empty.")
                return
        
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(rows))
        
            imported_count = 0
            errors = []
        
            for i, row in enumerate(rows):
                try:
                    # Handle different possible column names
                    name = (row.get('Product Name') or row.get('Name') or row.get('product_name') or '').strip()
                    price_str = (row.get('Price') or row.get('price') or '0').strip()
                
                    # Clean price string
                    price_str = price_str.replace('$', '').replace(',', '').replace('£', '').replace('€', '')
                
                    if not name:
                        errors.append(f"Row {i+1}: Missing product name")
                        continue
                
                    try:
                        price = float(price_str) if price_str else 0.0
                    except ValueError:
                        price = 0.0
                        errors.append(f"Row {i+1}: Invalid price '{price_str}', set to 0.0")
                
                    description = (row.get('Description') or row.get('description') or '').strip()
                    category = (row.get('Category') or row.get('category') or '').strip()
                    tags = (row.get('Tags') or row.get('tags') or '').strip()
                    location = (row.get('Location') or row.get('location') or '').strip()
                    images_folder = (row.get('Images Folder') or row.get('images_folder') or row.get('Images') or '').strip()
                
                    # Validate images folder if provided
                    if images_folder and not os.path.exists(images_folder):
                        errors.append(f"Row {i+1}: Images folder '{images_folder}' does not exist")
                        images_folder = ""  # Reset to empty if invalid
                
                    product_id = self.db_manager.add_product(
                        name, price, description, category, tags, location, images_folder
                    )
                
                    self.imported_product_ids.append(product_id)
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
                self.progress_bar.setValue(i + 1)
        
            self.progress_bar.setVisible(False)
        
            # Show results
            message = f"Successfully imported {imported_count} products."
            if errors:
                message += f"\n\nErrors encountered:\n" + "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    message += f"\n... and {len(errors) - 10} more errors."
        
            if imported_count > 0:
                QMessageBox.information(self, "Import Complete", message)
                self.accept()
            else:
                QMessageBox.warning(self, "Import Failed", "No products were imported.\n\n" + message)
        
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to import products: {str(e)}")
    
    def get_imported_product_ids(self):
        """Get list of imported product IDs"""
        return self.imported_product_ids
