from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QSplitter, QFrame, QPushButton, QLabel,
                            QSpinBox, QDoubleSpinBox, QComboBox, QDateTimeEdit,
                            QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                            QTextEdit, QMessageBox, QDialog, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QColor

from .login_dialog import LoginDialog
from .dialogs.group_dialog import GroupDialog
from .dialogs.product_dialog import ProductDialog
from automation.posting_manager import PostingManager
import threading

class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.posting_manager = PostingManager(db_manager)
        self.current_group_id = None
        self.is_posting_active = False
        self.is_posting_paused = False
        
        # Real-time data storage
        self.pending_accounts = []
        self.progress_accounts = []
        self.done_accounts = []
        self.failed_accounts = []
        
        self.setWindowTitle("Facebook Marketplace Bot - Your Marketplace Friend")
        self.setGeometry(100, 100, 1200, 800)
        
        # Check authentication on startup
        if not self.auth_manager.is_authenticated():
            self.show_login_dialog()
        
        self.setup_ui()
        self.setup_connections()
        self.load_groups()
        
        # Timer for updating UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_realtime_panels)
        self.update_timer.start(1000)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Control Panel (Top Section)
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_layout = QVBoxLayout(control_frame)
        
        # Row 1: Batch Size and Price Range
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 50)
        self.batch_size_spin.setValue(3)
        row1.addWidget(self.batch_size_spin)
        
        row1.addWidget(QLabel("Min Price:"))
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0, 999999)
        self.min_price_spin.setValue(0)
        row1.addWidget(self.min_price_spin)
        
        row1.addWidget(QLabel("Max Price:"))
        self.max_price_spin = QDoubleSpinBox()
        self.max_price_spin.setRange(0, 999999)
        self.max_price_spin.setValue(999999)
        row1.addWidget(self.max_price_spin)
        
        row1.addWidget(QLabel("Select Groups:"))
        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.on_group_changed)
        row1.addWidget(self.group_combo)
        
        # Manage buttons
        self.manage_groups_btn = QPushButton("Groups")
        self.manage_groups_btn.clicked.connect(self.show_manage_groups)
        row1.addWidget(self.manage_groups_btn)
        
        self.manage_products_btn = QPushButton("Products")
        self.manage_products_btn.clicked.connect(self.show_manage_products)
        row1.addWidget(self.manage_products_btn)
        
        control_layout.addLayout(row1)
        
        # Row 2: Control Buttons
        row2 = QHBoxLayout()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_posting)
        row2.addWidget(self.start_btn)
        
        self.pause_continue_btn = QPushButton("Pause All")
        self.pause_continue_btn.clicked.connect(self.toggle_pause_continue)
        self.pause_continue_btn.setEnabled(False)
        row2.addWidget(self.pause_continue_btn)
        
        row2.addWidget(QLabel("Schedule At:"))
        self.schedule_datetime = QDateTimeEdit()
        self.schedule_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.schedule_datetime.setCalendarPopup(True)
        self.schedule_datetime.setDisplayFormat("dd/MM/yyyy hh:mm AP")
        row2.addWidget(self.schedule_datetime)
        
        schedule_btn = QPushButton("Schedule")
        schedule_btn.clicked.connect(self.schedule_job)
        row2.addWidget(schedule_btn)
        
        # Active Accounts checkbox
        self.active_accounts_check = QCheckBox("Active Accounts")
        self.active_accounts_check.setChecked(True)
        row2.addWidget(self.active_accounts_check)
        
        row2.addStretch()
        
        control_layout.addLayout(row2)
        main_layout.addWidget(control_frame)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Monitoring tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Accounts section
        self.accounts_label = QLabel("Accounts: (0)")
        self.accounts_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(self.accounts_label)
        
        self.accounts_list = QTextEdit()
        self.accounts_list.setMaximumHeight(100)
        self.accounts_list.setReadOnly(True)
        left_layout.addWidget(self.accounts_list)
        
        # Status tabs
        status_splitter = QSplitter(Qt.Horizontal)
        
        # Pending
        pending_widget = QWidget()
        pending_layout = QVBoxLayout(pending_widget)
        pending_layout.addWidget(QLabel("Pending:"))
        self.pending_list = QTextEdit()
        self.pending_list.setReadOnly(True)
        pending_layout.addWidget(self.pending_list)
        status_splitter.addWidget(pending_widget)
        
        # In Progress
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.addWidget(QLabel("Inprogress Accounts:"))
        self.progress_list = QTextEdit()
        self.progress_list.setReadOnly(True)
        progress_layout.addWidget(self.progress_list)
        status_splitter.addWidget(progress_widget)
        
        # Done Posting
        done_widget = QWidget()
        done_layout = QVBoxLayout(done_widget)
        done_layout.addWidget(QLabel("Done Posting:"))
        self.done_list = QTextEdit()
        self.done_list.setReadOnly(True)
        done_layout.addWidget(self.done_list)
        status_splitter.addWidget(done_widget)
        
        # Ban/Locked/Failed
        failed_widget = QWidget()
        failed_layout = QVBoxLayout(failed_widget)
        failed_layout.addWidget(QLabel("Ban / Locked / Failed:"))
        self.failed_list = QTextEdit()
        self.failed_list.setReadOnly(True)
        failed_layout.addWidget(self.failed_list)
        status_splitter.addWidget(failed_widget)
        
        left_layout.addWidget(status_splitter)
        
        # Logs section
        logs_label = QLabel("Logs:")
        logs_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(logs_label)
        
        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(150)
        self.logs_text.setReadOnly(True)
        left_layout.addWidget(self.logs_text)
        
        content_splitter.addWidget(left_widget)
        content_splitter.setSizes([1000])
        
        main_layout.addWidget(content_splitter)
    
    def setup_connections(self):
        # Connect posting manager signals
        self.posting_manager.log_message.connect(self.add_log)
        self.posting_manager.account_status_changed.connect(self.update_account_status)
        self.posting_manager.posting_completed.connect(self.on_posting_completed)
        self.posting_manager.batch_started.connect(self.on_batch_started)
    
    def show_login_dialog(self):
        dialog = LoginDialog(self.auth_manager, self)
        if dialog.exec_() != dialog.Accepted:
            self.close()
    
    def load_groups(self):
        """Load groups into combo box"""
        self.group_combo.clear()
        groups = self.db_manager.get_all_groups()
        for group in groups:
            self.group_combo.addItem(group['name'], group['id'])
        
        if groups:
            self.current_group_id = groups[0]['id']
            self.load_group_accounts()
    
    def on_group_changed(self):
        """Handle group selection change"""
        if self.group_combo.currentData():
            self.current_group_id = self.group_combo.currentData()
            self.load_group_accounts()
            self.clear_status_panels()
    
    def load_group_accounts(self):
        """Load accounts for selected group"""
        if not self.current_group_id:
            return
        
        accounts = self.db_manager.get_accounts_by_group(self.current_group_id)
        account_text = ""
        for account in accounts:
            account_text += f"{account['email']}\n"
        
        self.accounts_list.setPlainText(account_text)
        self.accounts_label.setText(f"Accounts: ({len(accounts)})")
        
        # Initialize pending accounts
        self.pending_accounts = [acc['email'] for acc in accounts]
        self.progress_accounts = []
        self.done_accounts = []
        self.failed_accounts = []
    
    def clear_status_panels(self):
        """Clear all status panels"""
        self.pending_list.clear()
        self.progress_list.clear()
        self.done_list.clear()
        self.failed_list.clear()
        
        self.pending_accounts = []
        self.progress_accounts = []
        self.done_accounts = []
        self.failed_accounts = []
    
    def show_manage_groups(self):
        """Show manage groups dialog"""
        dialog = ManageGroupsDialog(self.db_manager, self)
        if dialog.exec_() == dialog.Accepted:
            self.load_groups()
    
    def show_manage_products(self):
        """Show manage products dialog"""
        
        dialog = ManageProductsDialog(self.db_manager, self.current_group_id, self)
        dialog.exec_()
    
    def start_posting(self):
        """Start posting process"""
        if not self.current_group_id:
            QMessageBox.warning(self, "Warning", "Please select a group first.")
            return
        
        # Check if group has products
        products = self.db_manager.get_products_by_group(self.current_group_id)
        if not products:
            QMessageBox.warning(self, "Warning", "Selected group has no products assigned.")
            return
        
        batch_size = self.batch_size_spin.value()
        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        
        self.posting_manager.start_posting(self.current_group_id, batch_size, min_price, max_price)
        self.is_posting_active = True
        self.is_posting_paused = False
        self.update_button_states()
        self.add_log("Started posting process", "INFO")
        
        # Initialize status tracking
        accounts = self.db_manager.get_accounts_by_group(self.current_group_id)
        self.pending_accounts = [acc['email'] for acc in accounts]
        self.progress_accounts = []
        self.done_accounts = []
        self.failed_accounts = []
    
    def toggle_pause_continue(self):
        """Toggle between pause and continue"""
        if self.is_posting_paused:
            self.posting_manager.continue_posting()
            self.is_posting_paused = False
            self.add_log("Posting process resumed", "INFO")
        else:
            self.posting_manager.pause_posting()
            self.is_posting_paused = True
            self.add_log("Posting process paused", "INFO")
        
        self.update_button_states()
    
    def schedule_job(self):
        """Schedule posting job"""
        if not self.current_group_id:
            QMessageBox.warning(self, "Warning", "Please select a group first.")
            return
        
        scheduled_time = self.schedule_datetime.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        batch_size = self.batch_size_spin.value()
        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        
        try:
            job_id = self.db_manager.create_scheduled_job(
                self.current_group_id, scheduled_time, batch_size, min_price, max_price
            )
            self.add_log(f"Scheduled job {job_id} for {scheduled_time}", "INFO")
            QMessageBox.information(self, "Success", f"Job scheduled successfully for {scheduled_time}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to schedule job: {str(e)}")
    
    def update_button_states(self):
        """Update button states based on posting status"""
        self.start_btn.setEnabled(not self.is_posting_active)
        self.pause_continue_btn.setEnabled(self.is_posting_active)
        
        if self.is_posting_active:
            if self.is_posting_paused:
                self.pause_continue_btn.setText("Continue All")
            else:
                self.pause_continue_btn.setText("Pause All")
        else:
            self.pause_continue_btn.setText("Pause All")
    
    def add_log(self, message, level="INFO"):
        """Add log message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_account_status(self, account_id, status, current_action=""):
        """Update account status in real-time"""
        # Get account email
        accounts = self.db_manager.get_accounts_by_group(self.current_group_id)
        account_email = None
        for acc in accounts:
            if acc['id'] == account_id:
                account_email = acc['email']
                break
        
        if not account_email:
            return
        
        # Update status lists
        if status == "processing":
            if account_email in self.pending_accounts:
                self.pending_accounts.remove(account_email)
            if account_email not in self.progress_accounts:
                self.progress_accounts.append(f"{account_email} - {current_action}")
        elif status == "completed":
            if account_email in self.progress_accounts:
                # Remove from progress (with any action text)
                self.progress_accounts = [acc for acc in self.progress_accounts if not acc.startswith(account_email)]
            if account_email not in self.done_accounts:
                self.done_accounts.append(f"{account_email} - {current_action}")
        elif status == "failed":
            if account_email in self.progress_accounts:
                self.progress_accounts = [acc for acc in self.progress_accounts if not acc.startswith(account_email)]
            if account_email not in self.failed_accounts:
                self.failed_accounts.append(f"{account_email} - {current_action}")
    
    def on_batch_started(self, batch_accounts):
        """Handle batch start"""
        for account_email in batch_accounts:
            if account_email in self.pending_accounts:
                self.pending_accounts.remove(account_email)
    
    def on_posting_completed(self, group_id):
        """Handle posting completion"""
        self.is_posting_active = False
        self.is_posting_paused = False
        self.update_button_states()
        self.add_log(f"Posting completed for group {group_id}", "INFO")
    
    def update_realtime_panels(self):
        """Update real-time status panels"""
        # Update pending
        self.pending_list.setPlainText('\n'.join(self.pending_accounts))
        
        # Update progress
        self.progress_list.setPlainText('\n'.join(self.progress_accounts))
        
        # Update done
        self.done_list.setPlainText('\n'.join(self.done_accounts))
        
        # Update failed
        self.failed_list.setPlainText('\n'.join(self.failed_accounts))

# Separate dialog classes
class ManageGroupsDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.setWindowTitle("Manage Groups")
        self.setGeometry(200, 200, 800, 600)
        
        self.setup_ui()
        self.load_groups()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        title = QLabel("Manage Groups")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Add button
        add_btn = QPushButton("+ Add Group")
        add_btn.clicked.connect(self.add_group)
        layout.addWidget(add_btn)
        
        # Groups table
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(6)
        self.groups_table.setHorizontalHeaderLabels([
            "Id", "Group Name", "Accounts", "Product Count", "Edit", "Remove"
        ])
        
        header = self.groups_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.groups_table)
    
    def load_groups(self):
        """Load groups into table"""
        groups = self.db_manager.get_all_groups()
        self.groups_table.setRowCount(len(groups))
        
        for row, group in enumerate(groups):
            accounts = self.db_manager.get_accounts_by_group(group['id'])
            products = self.db_manager.get_products_by_group(group['id'])
            
            self.groups_table.setItem(row, 0, QTableWidgetItem(str(group['id'])))
            self.groups_table.setItem(row, 1, QTableWidgetItem(group['name']))
            self.groups_table.setItem(row, 2, QTableWidgetItem(str(len(accounts))))
            self.groups_table.setItem(row, 3, QTableWidgetItem(str(len(products))))
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, g_id=group['id']: self.edit_group(g_id))
            self.groups_table.setCellWidget(row, 4, edit_btn)
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, g_id=group['id']: self.remove_group(g_id))
            self.groups_table.setCellWidget(row, 5, remove_btn)
    
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
    
    def remove_group(self, group_id):
        """Remove group"""
        reply = QMessageBox.question(self, 'Remove Group', 
                                   'Are you sure you want to remove this group?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.delete_group(group_id)
            self.load_groups()

class ManageProductsDialog(QDialog):
    def __init__(self, db_manager, group_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.group_id = group_id
        
        self.setWindowTitle("Manage Products")
        self.setGeometry(200, 200, 1000, 600)
        
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        title = QLabel("Manage Products")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Add button
        add_btn = QPushButton("+ Add Product")
        add_btn.clicked.connect(self.add_product)
        layout.addWidget(add_btn)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(9)
        self.products_table.setHorizontalHeaderLabels([
            "Id", "Product Name", "Price", "Locations", "Titles", "Images", "Category", "Edit", "Remove"
        ])
        
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.products_table)
    
    def load_products(self):
        """Load products into table"""
        products = self.db_manager.get_products_by_group(self.group_id)
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Count images
            images_count = 0
            if product['images_folder']:
                import os
                if os.path.exists(product['images_folder']):
                    images_count = len([f for f in os.listdir(product['images_folder']) 
                                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
            
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.products_table.setItem(row, 2, QTableWidgetItem(str(product['price'])))
            self.products_table.setItem(row, 3, QTableWidgetItem("3"))  # Default locations
            self.products_table.setItem(row, 4, QTableWidgetItem(product['tags'] or ""))
            self.products_table.setItem(row, 5, QTableWidgetItem(str(images_count)))
            self.products_table.setItem(row, 6, QTableWidgetItem(product['category'] or ""))
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p_id=product['id']: self.edit_product(p_id))
            self.products_table.setCellWidget(row, 7, edit_btn)
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, p_id=product['id']: self.remove_product(p_id))
            self.products_table.setCellWidget(row, 8, remove_btn)
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self.db_manager, self)
        if dialog.exec_() == dialog.Accepted:
            product_id = dialog.get_product_id()
            if product_id:
                self.db_manager.assign_product_to_group(self.group_id, product_id)
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
        reply = QMessageBox.question(self, 'Remove Product', 
                                   'Are you sure you want to remove this product from the group?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.remove_product_from_group(self.group_id, product_id)
            self.load_products()
