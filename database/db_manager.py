import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path="fb_marketplace.db"):
        self.db_path = db_path
        
    def init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                jwt_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                location TEXT,
                use_fingerprint BOOLEAN DEFAULT 0,
                proxy_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                country TEXT,
                cookies TEXT,
                status TEXT DEFAULT 'active',
                last_used TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                category TEXT,
                tags TEXT,
                location TEXT,
                images_folder TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Group-Product associations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_products (
                group_id INTEGER,
                product_id INTEGER,
                PRIMARY KEY (group_id, product_id),
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Posting logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posting_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                product_id INTEGER,
                status TEXT,
                reason TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Scheduled jobs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                scheduled_time TIMESTAMP,
                batch_size INTEGER,
                min_price REAL,
                max_price REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dictionaries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update/insert query and return affected rows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows
    
    # User management
    def create_user(self, email: str, password_hash: str) -> bool:
        try:
            self.execute_update(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        results = self.execute_query("SELECT * FROM users WHERE email = ?", (email,))
        return results[0] if results else None
    
    def update_user_token(self, email: str, token: str):
        self.execute_update(
            "UPDATE users SET jwt_token = ?, last_login = CURRENT_TIMESTAMP WHERE email = ?",
            (token, email)
        )
    
    # Group management
    def create_group(self, name: str, location: str = "", use_fingerprint: bool = False, proxy_config: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO groups (name, location, use_fingerprint, proxy_config) VALUES (?, ?, ?, ?)",
            (name, location, use_fingerprint, proxy_config)
        )
        group_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return group_id
    
    def get_all_groups(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM groups ORDER BY name")
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict]:
        results = self.execute_query("SELECT * FROM groups WHERE id = ?", (group_id,))
        return results[0] if results else None
    
    def delete_group(self, group_id: int):
        self.execute_update("DELETE FROM groups WHERE id = ?", (group_id,))
    
    # Account management
    def add_account_to_group(self, group_id: int, email: str, password: str, phone: str = "", country: str = ""):
        self.execute_update(
            "INSERT INTO accounts (group_id, email, password, phone, country) VALUES (?, ?, ?, ?, ?)",
            (group_id, email, password, phone, country)
        )
    
    def get_accounts_by_group(self, group_id: int) -> List[Dict]:
        return self.execute_query("SELECT * FROM accounts WHERE group_id = ?", (group_id,))
    
    def update_account_cookies(self, account_id: int, cookies: str):
        self.execute_update(
            "UPDATE accounts SET cookies = ?, last_used = CURRENT_TIMESTAMP WHERE id = ?",
            (cookies, account_id)
        )
    
    def update_account_status(self, account_id: int, status: str):
        self.execute_update("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
    
    # Product management
    def add_product(self, name: str, price: float, description: str = "", category: str = "", 
                   tags: str = "", location: str = "", images_folder: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price, description, category, tags, location, images_folder) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, price, description, category, tags, location, images_folder)
        )
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id
    
    def get_all_products(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM products ORDER BY name")
    
    def get_products_by_group(self, group_id: int) -> List[Dict]:
        query = """
            SELECT p.* FROM products p
            JOIN group_products gp ON p.id = gp.product_id
            WHERE gp.group_id = ?
            ORDER BY p.name
        """
        return self.execute_query(query, (group_id,))
    
    def assign_product_to_group(self, group_id: int, product_id: int):
        self.execute_update(
            "INSERT OR IGNORE INTO group_products (group_id, product_id) VALUES (?, ?)",
            (group_id, product_id)
        )
    
    def remove_product_from_group(self, group_id: int, product_id: int):
        self.execute_update(
            "DELETE FROM group_products WHERE group_id = ? AND product_id = ?",
            (group_id, product_id)
        )
    
    def delete_product(self, product_id: int):
        self.execute_update("DELETE FROM products WHERE id = ?", (product_id,))
    
    # Logging
    def log_posting_attempt(self, account_id: int, product_id: int, status: str, reason: str = ""):
        self.execute_update(
            "INSERT INTO posting_logs (account_id, product_id, status, reason) VALUES (?, ?, ?, ?)",
            (account_id, product_id, status, reason)
        )
    
    def get_posting_logs(self, limit: int = 100) -> List[Dict]:
        query = """
            SELECT pl.*, a.email as account_email, p.name as product_name
            FROM posting_logs pl
            JOIN accounts a ON pl.account_id = a.id
            JOIN products p ON pl.product_id = p.id
            ORDER BY pl.posted_at DESC
            LIMIT ?
        """
        return self.execute_query(query, (limit,))
    
    # Scheduling
    def create_scheduled_job(self, group_id: int, scheduled_time: str, batch_size: int, 
                           min_price: float = 0, max_price: float = 999999) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scheduled_jobs (group_id, scheduled_time, batch_size, min_price, max_price) VALUES (?, ?, ?, ?, ?)",
            (group_id, scheduled_time, batch_size, min_price, max_price)
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def get_pending_jobs(self) -> List[Dict]:
        return self.execute_query(
            "SELECT * FROM scheduled_jobs WHERE status = 'pending' AND scheduled_time <= CURRENT_TIMESTAMP"
        )
    
    def update_job_status(self, job_id: int, status: str):
        self.execute_update("UPDATE scheduled_jobs SET status = ? WHERE id = ?", (status, job_id))
