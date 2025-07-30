from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QHeaderView, QAbstractItemView, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .dialogs.group_dialog import GroupDialog
from .dialogs.product_dialog import ProductDialog
from .dialogs.csv_import_dialog import CSVImportDialog

class GroupPanel(QWidget):
    group_selected = pyqtSignal(int)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_group_id = None
        
        self.setup_ui()
        self.load_groups()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title and Group Selection
        header_layout = QHBoxLayout()
        
        title = QLabel("Group Management")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Group selector
        header_layout.addWidget(QLabel("Group:"))
        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.on_group_changed)
        self.group_combo.setMinimumWidth(150)
        header_layout.addWidget(self.group_combo)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Products tab
        self.products_tab = self.create_products_tab()
        self.tab_widget.addTab(self.products_tab, "Products")
        
        # Groups tab
        self.groups_tab = self.create_groups_tab()
        self.tab_widget.addTab(self.groups_tab, "Groups")
        
        layout.addWidget(self.tab_widget)
    
    def create_products_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_product_btn = QPushButton("Add Product")
        self.add_product_btn.clicked.connect(self.add_product)
        button_layout.addWidget(self.add_product_btn)
        
        self.import_products_btn = QPushButton("Import CSV")
        self.import_products_btn.clicked.connect(self.import_products)
        button_layout.addWidget(self.import_products_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "Product Name", "Price", "Location", "Tags", "Category", "Images", "Actions"
        ])
        
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.products_table)
        
        return widget
    
    def create_groups_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add Group button
        self.add_group_btn = QPushButton("Add Group")
        self.add_group_btn.clicked.connect(self.add_group)
        layout.addWidget(self.add_group_btn)
        
        # Groups table
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(4)
        self.groups_table.setHorizontalHeaderLabels([
            "Name", "Account Count", "Product Count", "Actions"
        ])
        
        header = self.groups_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.groups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.groups_table)
        
        return widget
    
    def load_groups(self):
        """Load groups into combo box and table"""
        # Load combo box
        self.group_combo.clear()
        groups = self.db_manager.get_all_groups()
        for group in groups:
            self.group_combo.addItem(group['name'], group['id'])
        
        # Load groups table
        self.groups_table.setRowCount(len(groups))
        for row, group in enumerate(groups):
            # Get counts
            accounts = self.db_manager.get_accounts_by_group(group['id'])
            products = self.db_manager.get_products_by_group(group['id'])
            
            self.groups_table.setItem(row, 0, QTableWidgetItem(group['name']))
            self.groups_table.setItem(row, 1, QTableWidgetItem(str(len(accounts))))
            self.groups_table.setItem(row, 2, QTableWidgetItem(str(len(products))))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, g_id=group['id']: self.edit_group(g_id))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, g_id=group['id']: self.delete_group(g_id))
            actions_layout.addWidget(delete_btn)
            
            self.groups_table.setCellWidget(row, 3, actions_widget)
    
    def load_products(self):
        """Load products for current group"""
        if not self.current_group_id:
            self.products_table.setRowCount(0)
            return
        
        products = self.db_manager.get_products_by_group(self.current_group_id)
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product['name']))
            self.products_table.setItem(row, 1, QTableWidgetItem(f"${product['price']:.2f}"))
            self.products_table.setItem(row, 2, QTableWidgetItem(product['location'] or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(product['tags'] or ""))
            self.products_table.setItem(row, 4, QTableWidgetItem(product['category'] or ""))
            
            # Count images
            images_count = 0
            if product['images_folder']:
                import os
                if os.path.exists(product['images_folder']):
                    images_count = len([f for f in os.listdir(product['images_folder']) 
                                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
            
            self.products_table.setItem(row, 5, QTableWidgetItem(str(images_count)))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p_id=product['id']: self.edit_product(p_id))
            actions_layout.addWidget(edit_btn)
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, p_id=product['id']: self.remove_product(p_id))
            actions_layout.addWidget(remove_btn)
            
            self.products_table.setCellWidget(row, 6, actions_widget)
    
    def on_group_changed(self):
        """Handle group selection change"""
        if self.group_combo.currentData():
            self.current_group_id = self.group_combo.currentData()
            self.group_selected.emit(self.current_group_id)
            self.load_products()
    
    def add_group(self):
        """Add new group"""
        dialog = GroupDialog(self.db_manager, self)
        if dialog.exec_() == dialog.Accepted:
            self.load_groups()
    
    def edit_group(self, group_id):
        """Edit existing group"""
        group = self.db_manager.get_group_by_id(group_id)
        if group:
            dialog = GroupDialog(self.db_manager, self, group)
            if dialog.exec_() == dialog.Accepted:
                self.load_groups()
    
    def delete_group(self, group_id):
        """Delete group"""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Delete Group', 
                                   'Are you sure you want to delete this group?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.delete_group(group_id)
            self.load_groups()
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self.db_manager, self)
        if dialog.exec_() == dialog.Accepted:
            product_id = dialog.get_product_id()
            if self.current_group_id and product_id:
                self.db_manager.assign_product_to_group(self.current_group_id, product_id)
            self.load_products()
    
    def edit_product(self, product_id):
        """Edit existing product"""
        products = self.db_manager.execute_query("SELECT * FROM products WHERE id = ?", (product_id,))
        if products:
            dialog = ProductDialog(self.db_manager, self, products[0])
            if dialog.exec_() == dialog.Accepted:
                self.load_products()
    
    def remove_product(self, product_id):
        """Remove product from group"""
        if self.current_group_id:
            self.db_manager.remove_product_from_group(self.current_group_id, product_id)
            self.load_products()
    
    def import_products(self):
        """Import products from CSV"""
        dialog = CSVImportDialog(self.db_manager, self)
        if dialog.exec_() == dialog.Accepted:
            # Assign imported products to current group
            if self.current_group_id:
                for product_id in dialog.get_imported_product_ids():
                    self.db_manager.assign_product_to_group(self.current_group_id, product_id)
            self.load_products()
