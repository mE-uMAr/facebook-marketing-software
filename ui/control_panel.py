from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
                            QSpinBox, QDoubleSpinBox, QComboBox, QDateTimeEdit, QFrame)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont

class ControlPanel(QWidget):
    start_posting = pyqtSignal(int, int, float, float) 
    pause_posting = pyqtSignal()
    continue_posting = pyqtSignal()
    schedule_job = pyqtSignal(int, str, int, float, float)  
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.selected_group_id = None
        self.is_posting_active = False
        self.is_posting_paused = False
        
        self.setup_ui()
        self.load_groups()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Control Panel")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Row 1: Batch Size and Price Range
        row1 = QHBoxLayout()
        
        # Batch Size
        row1.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 50)
        self.batch_size_spin.setValue(3)
        row1.addWidget(self.batch_size_spin)
        
        row1.addStretch()
        
        # Price Range
        row1.addWidget(QLabel("Min Price:"))
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0, 999999)
        self.min_price_spin.setPrefix("$")
        row1.addWidget(self.min_price_spin)
        
        row1.addWidget(QLabel("Max Price:"))
        self.max_price_spin = QDoubleSpinBox()
        self.max_price_spin.setRange(0, 999999)
        self.max_price_spin.setValue(999999)
        self.max_price_spin.setPrefix("$")
        row1.addWidget(self.max_price_spin)
        
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        
        # Start Button
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.on_start_clicked)
        row2.addWidget(self.start_btn)
        
        # Control Buttons
        self.pause_btn = QPushButton("Pause All")
        self.pause_btn.clicked.connect(self.pause_posting.emit)
        self.pause_btn.setEnabled(False)
        row2.addWidget(self.pause_btn)
        
        self.continue_btn = QPushButton("Continue All")
        self.continue_btn.clicked.connect(self.continue_posting.emit)
        self.continue_btn.setEnabled(False)
        row2.addWidget(self.continue_btn)
        
        row2.addStretch()
        
        # Group Selection
        row2.addWidget(QLabel("Select Group:"))
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(500)
        row2.addWidget(self.group_combo)
        
        layout.addLayout(row2)
        
        # Row 3: Scheduler
        row3 = QHBoxLayout()
        
        row3.addWidget(QLabel("Schedule At:"))
        self.schedule_datetime = QDateTimeEdit()
        self.schedule_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.schedule_datetime.setCalendarPopup(True)
        row3.addWidget(self.schedule_datetime)
        
        self.schedule_btn = QPushButton("Schedule Job")
        self.schedule_btn.clicked.connect(self.on_schedule_clicked)
        row3.addWidget(self.schedule_btn)
        
        row3.addStretch()
        
        layout.addLayout(row3)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
    
    def load_groups(self):
        """Load groups into combo box"""
        self.group_combo.clear()
        groups = self.db_manager.get_all_groups()
        for group in groups:
            self.group_combo.addItem(group['name'], group['id'])
    
    def on_start_clicked(self):
        """Handle start button click"""
        if self.group_combo.currentData() is None:
            return
        
        group_id = self.group_combo.currentData()
        batch_size = self.batch_size_spin.value()
        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        
        self.start_posting.emit(group_id, batch_size, min_price, max_price)
    
    def on_schedule_clicked(self):
        """Handle schedule button click"""
        if self.group_combo.currentData() is None:
            return
        
        group_id = self.group_combo.currentData()
        scheduled_time = self.schedule_datetime.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        batch_size = self.batch_size_spin.value()
        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        
        self.schedule_job.emit(group_id, scheduled_time, batch_size, min_price, max_price)
    
    def set_selected_group(self, group_id):
        """Set the selected group"""
        self.selected_group_id = group_id
        for i in range(self.group_combo.count()):
            if self.group_combo.itemData(i) == group_id:
                self.group_combo.setCurrentIndex(i)
                break
    
    def set_posting_active(self, active):
        """Set posting active state"""
        self.is_posting_active = active
        self.start_btn.setEnabled(not active)
        self.pause_btn.setEnabled(active and not self.is_posting_paused)
        self.continue_btn.setEnabled(active and self.is_posting_paused)
        self.schedule_btn.setEnabled(not active)
    
    def set_posting_paused(self, paused):
        """Set posting paused state"""
        self.is_posting_paused = paused
        self.pause_btn.setEnabled(self.is_posting_active and not paused)
        self.continue_btn.setEnabled(self.is_posting_active and paused)
