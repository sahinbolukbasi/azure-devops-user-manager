import os
import json

class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config = self.load_config()
    
    def load_config(self):
        """Konfigürasyon dosyasını yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Konfigürasyon yükleme hatası: {e}")
            return {}
    
    def save_config(self, config):
        """Konfigürasyon dosyasını kaydet"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            print(f"Konfigürasyon kaydetme hatası: {e}")
            return False
    
    def get_config(self):
        """Konfigürasyon bilgisini döndür"""
        return self.config