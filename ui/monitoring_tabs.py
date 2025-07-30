from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QAbstractItemView, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

class MonitoringTabs(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_group_id = None
        
        self.setup_ui()
        
        # Timer for refreshing data
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Group Accounts tab
        self.accounts_tab = self.create_accounts_tab()
        self.tab_widget.addTab(self.accounts_tab, "Group Accounts")
        
        # Pending tab
        self.pending_tab = self.create_pending_tab()
        self.tab_widget.addTab(self.pending_tab, "Pending")
        
        # In-Progress tab
        self.progress_tab = self.create_progress_tab()
        self.tab_widget.addTab(self.progress_tab, "In-Progress")
        
        # Done Posting tab
        self.done_tab = self.create_done_tab()
        self.tab_widget.addTab(self.done_tab, "Done Posting")
        
        # Ban/Locked/Failed tab
        self.failed_tab = self.create_failed_tab()
        self.tab_widget.addTab(self.failed_tab, "Ban/Locked/Failed")
        
        layout.addWidget(self.tab_widget)
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels([
            "Email", "Status", "Last Used", "Country", "Phone"
        ])
        
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.accounts_table)
        
        return widget
    
    def create_pending_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(3)
        self.pending_table.setHorizontalHeaderLabels([
            "Email", "Products to Post", "Queue Position"
        ])
        
        header = self.pending_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.pending_table)
        
        return widget
    
    def create_progress_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels([
            "Email", "Current Action", "Progress", "Time Started"
        ])
        
        header = self.progress_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.progress_table)
        
        return widget
    
    def create_done_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.done_table = QTableWidget()
        self.done_table.setColumnCount(4)
        self.done_table.setHorizontalHeaderLabels([
            "Email", "Products Posted", "Success Rate", "Completed At"
        ])
        
        header = self.done_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.done_table)
        
        return widget
    
    def create_failed_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(4)
        self.failed_table.setHorizontalHeaderLabels([
            "Email", "Failure Type", "Reason", "Failed At"
        ])
        
        header = self.failed_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.failed_table)
        
        return widget
    
    def load_group_accounts(self, group_id):
        """Load accounts for the selected group"""
        self.current_group_id = group_id
        self.refresh_accounts_data()
    
    def refresh_accounts_data(self):
        """Refresh the accounts table"""
        if not self.current_group_id:
            self.accounts_table.setRowCount(0)
            return
        
        accounts = self.db_manager.get_accounts_by_group(self.current_group_id)
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account['email']))
            
            # Status with color coding
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'active':
                status_item.setBackground(QColor(144, 238, 144))  # Light green
            elif account['status'] == 'banned':
                status_item.setBackground(QColor(255, 182, 193))  # Light red
            elif account['status'] == 'locked':
                status_item.setBackground(QColor(255, 255, 0))    # Yellow
            
            self.accounts_table.setItem(row, 1, status_item)
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account['last_used'] or "Never"))
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account['country'] or ""))
            self.accounts_table.setItem(row, 4, QTableWidgetItem(account['phone'] or ""))
    
    def update_account_status(self, account_id, status, current_action=""):
        """Update account status in real-time"""
        # This would be called by the posting manager
        # Implementation depends on how you want to track real-time status
        pass
    
    def refresh_data(self):
        """Refresh all tab data"""
        if self.current_group_id:
            self.refresh_accounts_data()
            # Add other refresh methods for pending, progress, done, failed tabs
