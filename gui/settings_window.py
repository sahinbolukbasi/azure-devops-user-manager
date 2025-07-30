from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import threading

class SettingsWindow(QDialog):
    def __init__(self, parent, config_manager, callback=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.callback = callback
        
        # Pencere ayarları
        self.setWindowTitle("⚙️ Azure DevOps Ayarları")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        # Mevcut ayarları yükle
        self.config = self.config_manager.get_config()
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Ayarlar arayüzünü oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("🔧 Azure DevOps Ayarları")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #0078d4; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # Ana ayarlar grubu
        settings_group = QGroupBox("Bağlantı Ayarları")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(15)
        
        # Organization URL
        self.org_url_edit = QLineEdit()
        self.org_url_edit.setPlaceholderText("https://dev.azure.com/yourorganization")
        self.org_url_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        settings_layout.addRow("🏢 Organization URL:", self.org_url_edit)
        
        # Personal Access Token
        self.pat_edit = QLineEdit()
        self.pat_edit.setEchoMode(QLineEdit.Password)
        self.pat_edit.setPlaceholderText("Azure DevOps PAT token'ınızı girin")
        self.pat_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        settings_layout.addRow("🔑 Personal Access Token (PAT):", self.pat_edit)
        
        # Project Name
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("Proje adını girin")
        self.project_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        settings_layout.addRow("📁 Proje Adı:", self.project_edit)
        
        layout.addWidget(settings_group)
        
        # Yardım metni
        help_label = QLabel("""
        💡 Yardım:
        • Organization URL: Azure DevOps organizasyonunuzun URL'i
        • PAT Token: Azure DevOps → User Settings → Personal Access Tokens
        • Proje Adı: Kullanıcıları eklemek istediğiniz projenin adı
        """)
        help_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                color: #6c757d;
                font-size: 11px;
            }
        """)
        layout.addWidget(help_label)
        
        # Test bağlantısı butonu
        self.test_btn = QPushButton("🔗 Bağlantıyı Test Et")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        layout.addWidget(self.test_btn)
        
        # Buton grubu
        button_layout = QHBoxLayout()
        
        # İptal butonu
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Kaydet butonu
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """Mevcut ayarları form alanlarına yükle"""
        self.org_url_edit.setText(self.config.get('organization_url', ''))
        self.pat_edit.setText(self.config.get('pat_token', ''))
        self.project_edit.setText(self.config.get('project_name', ''))
    
    def test_connection(self):
        """Bağlantıyı test et"""
        org_url = self.org_url_edit.text().strip()
        pat_token = self.pat_edit.text().strip()
        project_name = self.project_edit.text().strip()
        
        if not all([org_url, pat_token, project_name]):
            QMessageBox.critical(self, "Hata", "Lütfen tüm alanları doldurun")
            return
        
        # Test butonunu devre dışı bırak
        self.test_btn.setEnabled(False)
        self.test_btn.setText("🔄 Test ediliyor...")
        
        # Direkt test et (thread kullanmadan)
        try:
            from core.azure_rest_client import AzureDevOpsRESTClient
            
            # URL formatını düzelt
            if not org_url.startswith('https://'):
                org_url = f"https://dev.azure.com/{org_url}"
            
            print(f"🔄 Bağlantı test ediliyor...")
            print(f"📍 Organization: {org_url}")
            print(f"📂 Project: {project_name}")
            
            client = AzureDevOpsRESTClient(org_url, project_name, pat_token)
            result = client.test_connection()
            
            if result:
                print("✅ Bağlantı testi başarılı!")
                QMessageBox.information(self, "Başarılı", "✅ Bağlantı başarıyla test edildi!\n\n" +
                                      f"Organization: {org_url}\n" +
                                      f"Project: {project_name}")
            else:
                print("❌ Bağlantı testi başarısız!")
                QMessageBox.critical(self, "Hata", "❌ Bağlantı test edilemedi.\n\n" +
                                    "Lütfen şunları kontrol edin:\n" +
                                    "• PAT token geçerli mi?\n" +
                                    "• Organization URL doğru mu?\n" +
                                    "• Project adı doğru mu?\n" +
                                    "• İnternet bağlantınız var mı?")
        except Exception as e:
            print(f"❌ Bağlantı test hatası: {e}")
            QMessageBox.critical(self, "Hata", f"❌ Bağlantı hatası:\n\n{str(e)}\n\n" +
                               "Lütfen şunları kontrol edin:\n" +
                               "• PAT token doğru girildi mi?\n" +
                               "• Organization URL formatı: https://dev.azure.com/organizasyon\n" +
                               "• Project adı doğru yazıldı mı?")
        finally:
            # Test butonunu her durumda yeniden etkinleştir
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🔗 Bağlantıyı Test Et")
            print("🔄 Test butonu yeniden etkinleştirildi")
    

    
    def save_settings(self):
        """Ayarları kaydet"""
        org_url = self.org_url_edit.text().strip()
        pat_token = self.pat_edit.text().strip()
        project_name = self.project_edit.text().strip()
        
        if not all([org_url, pat_token, project_name]):
            QMessageBox.critical(self, "Hata", "Lütfen tüm alanları doldurun")
            return
        
        # URL formatını kontrol et
        if not org_url.startswith('https://'):
            QMessageBox.critical(self, "Hata", "Organization URL 'https://' ile başlamalıdır")
            return
        
        try:
            # Ayarları kaydet
            self.config_manager.save_config({
                'organization_url': org_url,
                'pat_token': pat_token,
                'project_name': project_name
            })
            
            QMessageBox.information(self, "Başarılı", "Ayarlar başarıyla kaydedildi!")
            
            # Callback'i çağır
            if self.callback:
                self.callback()
            
            # Pencereyi kapat
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilemedi:\n{str(e)}")