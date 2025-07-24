import configparser
import os
import base64
from cryptography.fernet import Fernet

class ConfigManager:
    def __init__(self):
        self.config_file = 'config.ini'
        self.key_file = '.app_key'
        self.ensure_key_exists()
    
    def ensure_key_exists(self):
        """Şifreleme anahtarının var olduğundan emin ol"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
    
    def get_key(self):
        """Şifreleme anahtarını al"""
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def encrypt_data(self, data):
        """Veriyi şifrele"""
        key = self.get_key()
        fernet = Fernet(key)
        return fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Veriyi çöz"""
        try:
            key = self.get_key()
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data  # Şifrelenmemiş veri
    
    def save_config(self, config_data):
        """Ayarları kaydet"""
        config = configparser.ConfigParser()
        
        config['Azure'] = {
            'organization_url': config_data['organization_url'],
            'pat_token': self.encrypt_data(config_data['pat_token']),
            'project_name': config_data['project_name']
        }
        
        with open(self.config_file, 'w') as f:
            config.write(f)
    
    def get_config(self):
        """Ayarları al"""
        if not os.path.exists(self.config_file):
            return {}
        
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        if 'Azure' not in config:
            return {}
        
        azure_config = config['Azure']
        
        return {
            'organization_url': azure_config.get('organization_url', ''),
            'pat_token': self.decrypt_data(azure_config.get('pat_token', '')),
            'project_name': azure_config.get('project_name', '')
        }