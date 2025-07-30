from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QCheckBox, QTextEdit, QFileDialog, QMessageBox,
                            QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import csv
import os

class GroupDialog(QDialog):
    def __init__(self, db_manager, parent=None, group_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.group_data = group_data
        self.is_edit_mode = group_data is not None
        
        self.setWindowTitle("Edit Group" if self.is_edit_mode else "Add Group")
        self.setFixedSize(700, 600)
        
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_group_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with close button
        header_layout = QHBoxLayout()
        title = QLabel("Edit Group" if self.is_edit_mode else "Add Group")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Group Name
        layout.addWidget(QLabel("Group Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Location
        layout.addWidget(QLabel("Location:"))
        self.location_edit = QLineEdit()
        layout.addWidget(self.location_edit)
        
        # Fingerprint toggle
        self.fingerprint_check = QCheckBox("Apply Fingerprint")
        layout.addWidget(self.fingerprint_check)
        
        # Proxy configuration
        layout.addWidget(QLabel("Proxy Configuration:"))
        self.proxy_edit = QTextEdit()
        self.proxy_edit.setMaximumHeight(80)
        self.proxy_edit.setPlaceholderText("Enter proxy settings (optional)")
        layout.addWidget(self.proxy_edit)
        
        # Tab widget for accounts and products
        self.tab_widget = QTabWidget()
        
        # Accounts tab
        accounts_tab = self.create_accounts_tab()
        self.tab_widget.addTab(accounts_tab, "Accounts")
        
        # Products tab
        products_tab = self.create_products_tab()
        self.tab_widget.addTab(products_tab, "Products")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_group)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Import CSV button
        import_btn = QPushButton("Import Accounts CSV")
        import_btn.clicked.connect(self.import_accounts_csv)
        layout.addWidget(import_btn)
        
        # Accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(4)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Password", "Phone", "Country"])
        
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.accounts_table)
        
        return widget
    
    def create_products_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Products selection table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["Select", "Product Name", "Price", "Category"])
        
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.products_table)
        
        self.load_products()
        
        return widget
    
    def load_group_data(self):
        """Load existing group data"""
        self.name_edit.setText(self.group_data['name'])
        self.location_edit.setText(self.group_data['location'] or "")
        self.fingerprint_check.setChecked(bool(self.group_data['use_fingerprint']))
        self.proxy_edit.setPlainText(self.group_data['proxy_config'] or "")
        
        # Load accounts
        accounts = self.db_manager.get_accounts_by_group(self.group_data['id'])
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account['email']))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account['password']))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account['phone'] or ""))
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account['country'] or ""))
    
    def load_products(self):
        """Load all products for selection"""
        all_products = self.db_manager.get_all_products()
        selected_products = []
        
        if self.is_edit_mode:
            selected_products = self.db_manager.get_products_by_group(self.group_data['id'])
            selected_ids = [p['id'] for p in selected_products]
        else:
            selected_ids = []
        
        self.products_table.setRowCount(len(all_products))
        
        for row, product in enumerate(all_products):
            # Checkbox
            checkbox = QCheckBox()
            if product['id'] in selected_ids:
                checkbox.setChecked(True)
            self.products_table.setCellWidget(row, 0, checkbox)
            
            # Product details
            self.products_table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"${product['price']:.2f}"))
            self.products_table.setItem(row, 3, QTableWidgetItem(product['category'] or ""))
            
            # Store product ID in the checkbox
            checkbox.product_id = product['id']
    
    def import_accounts_csv(self):
        """Import accounts from CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Accounts CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                accounts = list(reader)
        
            if not accounts:
                QMessageBox.warning(self, "Error", "CSV file is empty.")
                return
        
            # Check for required columns (flexible naming)
            headers = list(accounts[0].keys())
            email_col = None
            password_col = None
        
            for header in headers:
                if 'email' in header.lower():
                    email_col = header
                elif 'password' in header.lower():
                    password_col = header
        
            if not email_col or not password_col:
                QMessageBox.warning(self, "Error", "CSV must contain 'Email' and 'Password' columns (case insensitive).")
                return
        
            # Add accounts to table
            current_row = self.accounts_table.rowCount()
            valid_accounts = 0
        
            for account in accounts:
                email = account.get(email_col, '').strip()
                password = account.get(password_col, '').strip()
            
                if email and password:  # Only add if both email and password exist
                    self.accounts_table.setRowCount(current_row + valid_accounts + 1)
                    row = current_row + valid_accounts
                
                    self.accounts_table.setItem(row, 0, QTableWidgetItem(email))
                    self.accounts_table.setItem(row, 1, QTableWidgetItem(password))
                    self.accounts_table.setItem(row, 2, QTableWidgetItem(account.get('Phone', account.get('phone', ''))))
                    self.accounts_table.setItem(row, 3, QTableWidgetItem(account.get('Country', account.get('country', ''))))
                
                    valid_accounts += 1
        
            if valid_accounts > 0:
                QMessageBox.information(self, "Success", f"Imported {valid_accounts} valid accounts.")
            else:
                QMessageBox.warning(self, "Warning", "No valid accounts found in CSV file.")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import CSV: {str(e)}")
    
    def save_group(self):
        """Save group data"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Group name is required.")
            return
        
        location = self.location_edit.text().strip()
        use_fingerprint = self.fingerprint_check.isChecked()
        proxy_config = self.proxy_edit.toPlainText().strip()
        
        try:
            if self.is_edit_mode:
                # Update existing group
                self.db_manager.execute_update(
                    "UPDATE groups SET name = ?, location = ?, use_fingerprint = ?, proxy_config = ? WHERE id = ?",
                    (name, location, use_fingerprint, proxy_config, self.group_data['id'])
                )
                group_id = self.group_data['id']
                
                # Clear existing accounts and products
                self.db_manager.execute_update("DELETE FROM accounts WHERE group_id = ?", (group_id,))
                self.db_manager.execute_update("DELETE FROM group_products WHERE group_id = ?", (group_id,))
            else:
                # Create new group
                group_id = self.db_manager.create_group(name, location, use_fingerprint, proxy_config)
            
            # Add accounts
            for row in range(self.accounts_table.rowCount()):
                email_item = self.accounts_table.item(row, 0)
                password_item = self.accounts_table.item(row, 1)
                phone_item = self.accounts_table.item(row, 2)
                country_item = self.accounts_table.item(row, 3)
                
                if email_item and password_item and email_item.text().strip() and password_item.text().strip():
                    self.db_manager.add_account_to_group(
                        group_id,
                        email_item.text().strip(),
                        password_item.text().strip(),
                        phone_item.text().strip() if phone_item else "",
                        country_item.text().strip() if country_item else ""
                    )
            
            # Add selected products
            for row in range(self.products_table.rowCount()):
                checkbox = self.products_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    self.db_manager.assign_product_to_group(group_id, checkbox.product_id)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save group: {str(e)}")
