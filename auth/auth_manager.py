import requests
import json
import os
from datetime import datetime, timedelta

class AuthManager:
    def __init__(self):
        self.token = None
        self.token_file = "auth_token.json"
        self.api_url = "https://validator.meharumar.codes/api/login"
        self.load_token()
    
    def load_token(self):
        """Load token from file if exists and valid"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get('token')
                    expires = data.get('expires')
                    
                    if token and expires:
                        expire_date = datetime.fromisoformat(expires)
                        if expire_date > datetime.now():
                            self.token = token
                            return True
        except Exception as e:
            print(f"Error loading token: {e}")
        return False
    
    def save_token(self, token):
        """Save token to file"""
        try:
            expire_date = datetime.now() + timedelta(days=2)
            data = {
                'token': token,
                'expires': expire_date.isoformat()
            }
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
            self.token = token
        except Exception as e:
            print(f"Error saving token: {e}")
    
    def login(self, email, password):
        """Login via API"""
        try:
            response = requests.post(self.api_url, json={
                'email': email,
                'password': password
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    self.save_token(token)
                    return True, "Login successful"
                else:
                    return False, "No token received"
            else:
                return False, f"Login failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.token is not None
    
    def logout(self):
        """Logout and clear token"""
        self.token = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
