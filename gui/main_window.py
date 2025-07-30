import os
import sys
import datetime
import threading

# PyQt5 kütüphaneleri
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QTextEdit, QFrame, QSplitter,
                             QApplication, QGroupBox, QScrollArea, QLineEdit,
                             QDialog, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

# Uyarıları bastır
import warnings
warnings.filterwarnings("ignore")

# Core modüllerini import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.config_manager import ConfigManager
    from core.excel_processor import ExcelProcessor
    from core.azure_rest_client import AzureDevOpsRESTClient
    from gui.settings_window import SettingsWindow
    print("✅ Tüm core modüller başarıyla yüklendi")
except ImportError as e:
    print(f"❌ Core modül import hatası: {e}")
    QMessageBox.critical(None, "Import Hatası", f"Core modüller yüklenemedi: {e}")
    sys.exit(1)

# İşlem thread'i
class ProcessThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)  # current, total
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, file_path, azure_rest_client, excel_processor):
        super().__init__()
        self.file_path = file_path
        self.azure_rest_client = azure_rest_client
        self.excel_processor = excel_processor
        self.is_running = False
        
        # Rapor verilerini toplama sistemi
        self.report_data = []
        
    def run(self):
        try:
            self.is_running = True
            self.log_signal.emit("🚀 Azure DevOps işlemi başlatılıyor...")
            
            # Bağlantıyı test et
            self.log_signal.emit("🔍 Azure DevOps bağlantısı test ediliyor...")
            try:
                success = self.azure_rest_client.test_connection()
                if not success:
                    self.log_signal.emit("❌ Azure CLI bağlantı hatası")
                    self.status_signal.emit("❌ Bağlantı hatası")
                    self.finished_signal.emit(False, "Azure CLI bağlantı hatası")
                    return
            except Exception as e:
                self.log_signal.emit(f"❌ Bağlantı test hatası: {str(e)}")
                self.finished_signal.emit(False, f"Bağlantı test hatası: {str(e)}")
                return
            
            self.log_signal.emit("✅ Azure DevOps bağlantısı başarılı")
            self.status_signal.emit("📂 Excel dosyası okunuyor...")
            
            # Excel dosyasını oku
            try:
                excel_data = self.excel_processor.read_excel(self.file_path)
                if not excel_data or 'users' not in excel_data:
                    self.log_signal.emit("❌ Excel dosyası okunamadı veya boş")
                    self.finished_signal.emit(False, "Excel dosyası okunamadı")
                    return
                    
                users = excel_data['users']
                if not users:
                    self.log_signal.emit("❌ Excel dosyasında kullanıcı bulunamadı")
                    self.finished_signal.emit(False, "Excel dosyasında kullanıcı bulunamadı")
                    return
                    
            except Exception as e:
                self.log_signal.emit(f"❌ Excel okuma hatası: {str(e)}")
                self.finished_signal.emit(False, f"Excel okuma hatası: {str(e)}")
                return
            
            self.log_signal.emit(f"📊 {len(users)} kullanıcı bulundu, işlem başlatılıyor...")
            
            # 🚀 PERFORMANS OPTİMİZASYONU: Toplu işlem stratejisi
            self.log_signal.emit("⚡ Performans optimizasyonu aktif: Cache ve batch işlem kullanılıyor")
            
            # Kullanıcıları işlem türüne göre grupla
            add_users = []
            remove_users = []
            
            for user in users:
                user_email = user.get('User Email', '').strip()
                team_name = user.get('Team Name', '').strip()
                action = user.get('Action', 'add').strip().lower()
                
                if not user_email or not team_name:
                    continue
                    
                if action == 'add':
                    add_users.append(user)
                elif action == 'remove':
                    remove_users.append(user)
            
            self.log_signal.emit(f"📊 İşlem planı: {len(add_users)} ekleme, {len(remove_users)} çıkarma")
            
            # Önce tüm takımları ve organizasyon üyelerini cache'le (tek seferde)
            self.status_signal.emit("🔄 Takımlar ve organizasyon üyeleri yükleniyor...")
            teams = self.azure_rest_client.get_teams()  # Cache'lenir
            org_users = self.azure_rest_client._load_all_org_users()  # Cache'lenir
            self.log_signal.emit(f"💾 {len(teams)} takım ve {len(org_users)} organizasyon üyesi cache'lendi")
            
            # Toplu davet işlemi (sadece ekleme için)
            if add_users:
                self.status_signal.emit("📧 Toplu davet işlemi başlatılıyor...")
                add_emails = [user.get('User Email', '').strip() for user in add_users]
                batch_invite_results = self.azure_rest_client.invite_multiple_users_batch(add_emails)
                self.log_signal.emit(f"📧 Toplu davet tamamlandı: {sum(batch_invite_results.values())}/{len(add_emails)} başarılı")
            
            # Kullanıcıları işle (optimize edilmiş)
            success_count = 0
            error_count = 0
            errors = []
            total_users = len(users)
            
            for i, user in enumerate(users):
                if not self.is_running:
                    self.log_signal.emit("⏹️ İşlem kullanıcı tarafından durduruldu")
                    break
                    
                try:
                    user_email = user.get('User Email', '').strip()
                    team_name = user.get('Team Name', '').strip()
                    role = user.get('Role', 'Member').strip()
                    action = user.get('Action', 'add').strip().lower()
                    
                    self.progress_signal.emit(i + 1, total_users)
                    self.status_signal.emit(f"⚡ İşleniyor: {user_email} ({i+1}/{total_users})")
                    
                    if not user_email or not team_name:
                        self.log_signal.emit(f"❌ Eksik bilgi: {user}")
                        error_count += 1
                        errors.append(f"Eksik bilgi: {user_email or 'Email yok'} - {team_name or 'Takım yok'}")
                        continue
                        
                    try:
                        # İşlem türüne göre kullanıcı ekle/çıkar (cache'den hızlı)
                        if action == 'add':
                            result = self.azure_rest_client.add_user_to_team(user_email, team_name, role)
                        elif action == 'remove':
                            result = self.azure_rest_client.remove_user_from_team(user_email, team_name)
                        else:
                            self.log_signal.emit(f"❌ Geçersiz işlem: {action} - {user_email}")
                            error_count += 1
                            errors.append(f"Geçersiz işlem: {action} - {user_email}")
                            continue
                        
                        # Rapor verilerini topla
                        import datetime
                        report_entry = {
                            'Kullanıcı Email': user_email,
                            'Takım Adı': team_name,
                            'Rol': role,
                            'İşlem': action.upper(),
                            'Durum': 'BAŞARILI' if result else 'BAŞARISIZ',
                            'Hata Mesajı': '' if result else 'API işlemi başarısız',
                            'Zaman': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.report_data.append(report_entry)
                        
                        if result:
                            self.log_signal.emit(f"✅ Başarılı: {user_email} -> {team_name} ({action})")
                            success_count += 1
                        else:
                            self.log_signal.emit(f"❌ Başarısız: {user_email} -> {team_name} ({action})")
                            error_count += 1
                            errors.append(f"İşlem başarısız: {user_email} -> {team_name}")
                            
                    except Exception as e:
                        # Hata durumu için rapor verisi
                        import datetime
                        report_entry = {
                            'Kullanıcı Email': user_email,
                            'Takım Adı': team_name,
                            'Rol': role,
                            'İşlem': action.upper(),
                            'Durum': 'HATA',
                            'Hata Mesajı': str(e),
                            'Zaman': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.report_data.append(report_entry)
                        
                        self.log_signal.emit(f"❌ Hata: {user_email} -> {str(e)}")
                        error_count += 1
                        errors.append(f"Hata: {user_email} -> {str(e)}")
                        
                except Exception as e:
                    error_msg = f"Satır {i+2} işlem hatası: {str(e)}"
                    self.log_signal.emit(f"❌ {error_msg}")
                    errors.append(error_msg)
                    error_count += 1
            
            # Bekleyen davetleri işle (non-blocking)
            if hasattr(self.azure_rest_client, '_pending_invitations') and self.azure_rest_client._pending_invitations:
                self.status_signal.emit("⏳ Bekleyen davetler işleniyor...")
                processed = self.azure_rest_client.wait_for_pending_invitations(max_wait_time=30)
                if processed > 0:
                    self.log_signal.emit(f"✅ {processed} bekleyen davet başarıyla işlendi")
                    
            # Sonuçları raporla
            self.progress_signal.emit(len(users), len(users))
            
            if success_count > 0:
                self.log_signal.emit(f"\n🎉 İşlem tamamlandı!")
                self.log_signal.emit(f"✅ Başarılı işlem sayısı: {success_count}")
                if error_count > 0:
                    self.log_signal.emit(f"❌ Hatalı işlem sayısı: {error_count}")
                    
            if error_count == 0:
                self.status_signal.emit("🎉 Tüm işlemler başarılı!")
                self.finished_signal.emit(True, None)
            else:
                error_summary = f"{error_count} hata oluştu"
                if errors:
                    error_summary += f": {'; '.join(errors[:3])}"
                    if len(errors) > 3:
                        error_summary += f" ve {len(errors)-3} hata daha..."
                        
                self.status_signal.emit(f"⚠️ {success_count} başarılı, {error_count} hatalı")
                self.finished_signal.emit(success_count > 0, error_summary)
                
        except Exception as e:
            self.log_signal.emit(f"❌ Genel işlem hatası: {str(e)}")
            self.status_signal.emit("❌ İşlem hatası")
            self.finished_signal.emit(False, str(e))
        finally:
            self.is_running = False
            
    def stop(self):
        """Thread'i durdur"""
        self.is_running = False
    
    def generate_excel_report(self):
        """İşlem sonuçlarının Excel raporunu oluşturur"""
        try:
            import pandas as pd
            import os
            import datetime
            
            if not self.report_data:
                return None
            
            # Masaüstü yolunu al
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"azure_devops_islem_raporu_{timestamp}.xlsx"
            report_path = os.path.join(desktop_path, report_filename)
            
            # DataFrame oluştur
            df = pd.DataFrame(self.report_data)
            
            # Excel dosyasını oluştur
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                # Ana rapor sayfası
                df.to_excel(writer, sheet_name='İşlem Detayları', index=False)
                
                # Özet istatistikler sayfası
                summary_data = {
                    'Metrik': [
                        'Toplam İşlem Sayısı',
                        'Başarılı İşlemler',
                        'Başarısız İşlemler', 
                        'Hatalı İşlemler',
                        'Başarı Oranı (%)'
                    ],
                    'Değer': [
                        len(self.report_data),
                        len([r for r in self.report_data if r['Durum'] == 'BAŞARILI']),
                        len([r for r in self.report_data if r['Durum'] == 'BAŞARISIZ']),
                        len([r for r in self.report_data if r['Durum'] == 'HATA']),
                        round((len([r for r in self.report_data if r['Durum'] == 'BAŞARILI']) / len(self.report_data)) * 100, 2) if self.report_data else 0
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Özet İstatistikler', index=False)
                
                # Takım bazında özet
                team_summary = df.groupby(['Takım Adı', 'Durum']).size().unstack(fill_value=0)
                if not team_summary.empty:
                    team_summary.to_excel(writer, sheet_name='Takım Bazında Özet')
            
            return report_path
            
        except Exception as e:
            print(f"Excel raporu oluşturma hatası: {str(e)}")
            return None



# Ana pencere sınıfı
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Temel değişkenler
        self.config_manager = ConfigManager()
        self.excel_processor = ExcelProcessor()
        self.azure_client = None
        self.selected_file = None
        self.processing = False
        self.process_thread = None
        
        # UI kurulumu
        self.setup_ui()
        self.log_message("Uygulama başlatıldı")
        
        # Hazır durumu kontrol et
        self.check_ready_state()
        
    def setup_ui(self):
        """Ana kullanıcı arayüzünü kur"""
        self.setWindowTitle("🚀 Azure DevOps Kullanıcı Ekleme Aracı")
        self.setMinimumSize(900, 700)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title_label = QLabel("🚀 Azure DevOps Kullanıcı Ekleme Aracı")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)
        

        
        # Ayarlar bölümü
        settings_group = QGroupBox("Azure DevOps Ayarları")
        settings_layout = QHBoxLayout(settings_group)
        
        # Ayarlar butonu
        settings_btn = QPushButton("⚙️ Ayarları Düzenle")
        settings_btn.clicked.connect(self.open_settings)
        
        # Test bağlantısı butonu
        test_btn = QPushButton("🔍 Bağlantı Test Et")
        test_btn.clicked.connect(self.test_connection)
        
        settings_layout.addWidget(settings_btn)
        settings_layout.addWidget(test_btn)
        settings_layout.addStretch()
        
        main_layout.addWidget(settings_group)
        
        # Dosya seçim bölümü
        file_group = QGroupBox("Excel Dosyası")
        file_layout = QVBoxLayout(file_group)
        
        self.file_label = QLabel("Henüz dosya seçilmedi")
        file_layout.addWidget(self.file_label)
        
        file_buttons = QHBoxLayout()
        self.browse_btn = QPushButton("📁 Dosya Seç")
        self.browse_btn.clicked.connect(self.browse_file)
        
        self.template_btn = QPushButton("📋 Şablon Oluştur")
        self.template_btn.clicked.connect(self.create_template)
        
        file_buttons.addWidget(self.browse_btn)
        file_buttons.addWidget(self.template_btn)
        file_buttons.addStretch()
        
        file_layout.addLayout(file_buttons)
        main_layout.addWidget(file_group)
        
        # İşlem butonu
        self.process_btn = QPushButton("🚀 Kullanıcıları Ekle")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        main_layout.addWidget(self.process_btn)
        
        # Durum bilgisi
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Durum:"))
        
        self.status_label = QLabel("Hazır")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Log alanı
        log_group = QGroupBox("İşlem Logları")
        log_layout = QVBoxLayout(log_group)
        
        # Log text widget
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Log temizleme butonu
        clear_btn = QPushButton("🗑️ Logları Temizle")
        clear_btn.clicked.connect(self.clear_logs)
        
        log_buttons = QHBoxLayout()
        log_buttons.addStretch()
        log_buttons.addWidget(clear_btn)
        
        log_layout.addLayout(log_buttons)
        main_layout.addWidget(log_group)
        
    def open_settings(self):
        """Ayarlar penceresini aç"""
        settings_dialog = SettingsWindow(self, self.config_manager, self.on_settings_saved)
        settings_dialog.exec_()
        
    def on_settings_saved(self):
        """Ayarlar kaydedildiğinde çağrılır"""
        self.log_message("Ayarlar güncellendi")
        self.check_ready_state()
        
    def browse_file(self):
        """Excel dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel Dosyaları (*.xlsx *.xls);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.log_message(f"Dosya seçildi: {os.path.basename(file_path)}")
            self.check_ready_state()
    
    def create_template(self):
        """Excel şablonu oluştur"""
        try:
            self.log_message("📋 Excel şablonu oluşturuluyor...")
            
            # Masaüstü yolunu al
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            template_path = os.path.join(desktop_path, "azure_devops_template.xlsx")
            
            # Şablonu oluştur
            result_path = self.excel_processor.create_sample_template(template_path)
            
            if result_path and os.path.exists(result_path):
                self.log_message(f"✅ Şablon başarıyla oluşturuldu: {result_path}")
                QMessageBox.information(
                    self, 
                    "Şablon Oluşturuldu", 
                    f"Excel şablonu masaüstüne kaydedildi:\n{os.path.basename(result_path)}"
                )
            else:
                self.log_message("❌ Şablon oluşturulamadı")
                QMessageBox.critical(self, "Hata", "Şablon oluşturulamadı")
                
        except Exception as e:
            error_msg = f"Şablon oluşturma hatası: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "Hata", error_msg)
    
    def test_connection(self):
        """Azure DevOps bağlantısını test et"""
        try:
            self.log_message("🔍 Bağlantı testi başlatılıyor...")
            
            # Ayarları kontrol
            config = self.config_manager.get_config()
            
            # Gerekli ayarları kontrol et
            if not config.get('organization_url'):
                error_msg = "Organization URL ayarlanmamış. Lütfen ayarları kontrol edin."
                self.log_message(f"❌ {error_msg}")
                QMessageBox.critical(self, "Ayar Hatası", error_msg)
                self.open_settings()
                return
                
            if not config.get('project_name'):
                error_msg = "Project Name ayarlanmamış. Lütfen ayarları kontrol edin."
                self.log_message(f"❌ {error_msg}")
                QMessageBox.critical(self, "Ayar Hatası", error_msg)
                self.open_settings()
                return
                
            if not config.get('pat_token'):
                error_msg = "PAT Token ayarlanmamış. Lütfen ayarları kontrol edin."
                self.log_message(f"❌ {error_msg}")
                QMessageBox.critical(self, "Ayar Hatası", error_msg)
                self.open_settings()
                return
            
            self.log_message(f"📍 Organization: {config['organization_url']}")
            self.log_message(f"📂 Project: {config['project_name']}")
            self.log_message("🔑 PAT Token: [GIZLI]")
            
            # Azure DevOps REST API Client oluştur
            from core.azure_rest_client import AzureDevOpsRESTClient
            
            azure_rest_client = AzureDevOpsRESTClient(
                config['organization_url'],
                config['project_name'],
                config['pat_token']
            )
            
            self.log_message("🔄 Azure DevOps REST API bağlantısı test ediliyor...")
            
            # Bağlantıyı test et
            success = azure_rest_client.test_connection()
            
            if success:
                self.log_message("✅ Azure DevOps REST API bağlantısı BAŞARILI!")
                
                # Takım listesini al
                try:
                    self.log_message("📋 Takımlar listeleniyor...")
                    teams = azure_rest_client.get_teams()
                    
                    if teams and len(teams) > 0:
                        self.log_message(f"✅ {len(teams)} takım bulundu:")
                        for i, team in enumerate(teams[:5], 1):
                            self.log_message(f"  {i}. {team['name']}")
                        if len(teams) > 5:
                            self.log_message(f"  ... ve {len(teams)-5} takım daha")
                        
                        # Başarı mesajı
                        QMessageBox.information(
                            self, 
                            "✅ Bağlantı Başarılı", 
                            f"✅ Azure DevOps bağlantısı başarılı!\n\n"
                            f"📍 Organization: {config['organization_url']}\n"
                            f"📂 Project: {config['project_name']}\n"
                            f"👥 Takım Sayısı: {len(teams)}\n\n"
                            f"Sistem hazır! Excel dosyasını seçip kullanıcı ekleme işlemini başlatabilirsiniz."
                        )
                    else:
                        self.log_message("⚠️ Projede takım bulunamadı")
                        QMessageBox.warning(
                            self, 
                            "⚠️ Uyarı", 
                            f"Bağlantı başarılı ancak '{config['project_name']}' projesinde takım bulunamadı.\n\n"
                            f"Lütfen proje adını kontrol edin veya projede takım oluşturun."
                        )
                        
                except Exception as team_error:
                    self.log_message(f"⚠️ Takım listesi alınamadı: {str(team_error)}")
                    QMessageBox.information(
                        self, 
                        "✅ Bağlantı Başarılı", 
                        f"✅ Azure DevOps bağlantısı başarılı!\n\n"
                        f"Ancak takım listesi alınamadı:\n{str(team_error)}"
                    )
            else:
                error_msg = "Azure DevOps bağlantısı başarısız!"
                self.log_message(f"❌ {error_msg}")
                QMessageBox.critical(
                    self, 
                    "❌ Bağlantı Hatası", 
                    f"{error_msg}\n\n"
                    f"Lütfen şunları kontrol edin:\n"
                    f"• PAT Token geçerli mi?\n"
                    f"• Organization URL doğru mu?\n"
                    f"• Project adı doğru mu?\n"
                    f"• İnternet bağlantınız var mı?"
                )
                
        except Exception as e:
            error_msg = f"Bağlantı test hatası: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(
                self, 
                "❌ Hata", 
                f"{error_msg}\n\n"
                f"Lütfen ayarlarınızı kontrol edin ve tekrar deneyin."
            )
        
    def download_template(self):
        """Örnek şablon indir"""
        try:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Şablonu Kaydet",
                "sample_template.xlsx",
                "Excel Dosyaları (*.xlsx)"
            )
            
            if save_path:
                template_path = self.excel_processor.create_sample_template(save_path)
                if template_path:
                    self.log_message(f"Şablon oluşturuldu: {os.path.basename(template_path)}")
                    QMessageBox.information(
                        self,
                        "Başarılı",
                        f"Örnek şablon oluşturuldu: {os.path.basename(template_path)}"
                    )
        except Exception as e:
            self.log_message(f"Şablon oluşturma hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Şablon oluşturulamadı: {str(e)}")
    
    def check_ready_state(self):
        """Hazır olma durumunu kontrol et"""
        try:
            config = self.config_manager.get_config()
            has_config = (
                config.get('organization_url') and
                config.get('project_name')
            )
            
            has_file = self.selected_file is not None and os.path.exists(self.selected_file)
            
            if has_config and has_file:
                self.process_btn.setEnabled(True)
                self.status_label.setText("✅ Hazır - İşlemi başlatabilirsiniz")
            else:
                self.process_btn.setEnabled(False)
                
                missing = []
                if not has_config:
                    missing.append("Azure DevOps ayarları")
                if not has_file:
                    missing.append("Excel dosyası")
                
                self.status_label.setText(f"⚠️ Eksik: {', '.join(missing)}")
        except Exception as e:
            self.log_message(f"Durum kontrolü hatası: {str(e)}")
    
    def start_processing(self):
        """İşlemi başlat"""
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.critical(self, "Hata", "Lütfen geçerli bir Excel dosyası seçin")
            return
        
        # Ayarları kontrol et
        config = self.config_manager.get_config()
        if not config.get('organization_url') or not config.get('project_name'):
            QMessageBox.critical(self, "Hata", "Azure DevOps ayarlarını tamamlayın (Organization URL ve Project Name gerekli)")
            self.open_settings()
            return
        
        # İşlem zaten çalışıyorsa durdur
        if self.processing and self.process_thread and self.process_thread.isRunning():
            reply = QMessageBox.question(
                self, 
                "Devam Eden İşlem", 
                "Devam eden bir işlem var. İptal edip yeni işlem başlatmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.process_thread.stop()
                self.process_thread.wait()
            else:
                return
        
        # UI'yi işlem moduna al
        self.processing = True
        self.process_btn.setText("🛑 İşlemi Durdur")
        self.browse_btn.setEnabled(False)
        self.template_btn.setEnabled(False)
        
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("🔄 İşlem başlatılıyor...")
        
        # Thread'de işlemi başlat
        config = self.config_manager.get_config()
        pat_token = config.get('pat_token', '')
        if not pat_token:
            QMessageBox.critical(self, "Hata", "PAT token bulunamadı! Lütfen ayarlardan PAT token'ınızı girin.")
            self.open_settings()
            return
        
        self.azure_rest_client = AzureDevOpsRESTClient(
            config['organization_url'],
            config['project_name'],
            pat_token
        )
        
        self.process_thread = ProcessThread(self.selected_file, self.azure_rest_client, self.excel_processor)
        self.process_thread.log_signal.connect(self.log_message)
        self.process_thread.status_signal.connect(self.update_status)
        self.process_thread.progress_signal.connect(self.update_progress)
        self.process_thread.finished_signal.connect(self.on_process_finished)
        self.process_thread.start()
    
    def on_process_finished(self, success, error_message):
        """İşlem tamamlandığında çağrılır"""
        # UI'yi normal duruma getir
        self.processing = False
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.process_btn.setText("🚀 İşlemi Başlat")
        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.template_btn.setEnabled(True)
        
        # Excel raporu indirme seçeneği ile gelişmiş popup
        self.show_completion_popup_with_report(success, error_message)
    
    def show_completion_popup_with_report(self, success, error_message):
        """İşlem tamamlandığında Excel raporu indirme seçeneği ile popup gösterir"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        import os
        
        # Popup dialog oluştur
        dialog = QDialog(self)
        dialog.setWindowTitle("İşlem Tamamlandı")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Başlık
        if success:
            if error_message:
                title = "⚠️ Kısmi Başarı"
                title_style = "color: #FF9800; font-weight: bold; font-size: 16px;"
            else:
                title = "✅ İşlem Başarılı"
                title_style = "color: #4CAF50; font-weight: bold; font-size: 16px;"
        else:
            title = "❌ İşlem Başarısız"
            title_style = "color: #F44336; font-weight: bold; font-size: 16px;"
        
        title_label = QLabel(title)
        title_label.setStyleSheet(title_style)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Mesaj içeriği
        if success:
            if error_message:
                message = f"İşlem tamamlandı ancak bazı sorunlar yaşandı:\n\n{error_message}"
            else:
                message = "Tüm işlemler başarıyla tamamlandı!"
        else:
            message = f"İşlem sırasında hata oluştu:\n\n{error_message}"
        
        message_text = QTextEdit()
        message_text.setPlainText(message)
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(150)
        layout.addWidget(message_text)
        
        # Excel raporu indirme bölümü
        report_layout = QVBoxLayout()
        
        report_info = QLabel("📊 İşlem detaylarını Excel raporu olarak indirebilirsiniz:")
        report_info.setStyleSheet("color: #2196F3; font-weight: bold; margin: 10px 0;")
        report_layout.addWidget(report_info)
        
        # Rapor indirme butonu
        download_btn = QPushButton("📥 Excel Raporu İndir")
        download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2196F3, stop: 1 #1976D2);
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                border: 2px solid #2196F3;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #42A5F5, stop: 1 #1565C0);
                border: 2px solid #42A5F5;
            }
        """)
        
        def download_report():
            try:
                # ProcessThread'den Excel raporu oluştur
                if hasattr(self, 'process_thread') and self.process_thread:
                    report_path = self.process_thread.generate_excel_report()
                    if report_path and os.path.exists(report_path):
                        self.log_message(f"✅ Excel raporu oluşturuldu: {os.path.basename(report_path)}")
                        QMessageBox.information(
                            dialog,
                            "Rapor İndirildi",
                            f"Excel raporu masaüstüne kaydedildi:\n\n{os.path.basename(report_path)}"
                        )
                    else:
                        QMessageBox.warning(
                            dialog,
                            "Rapor Hatası",
                            "Excel raporu oluşturulamadı. Lütfen işlem loglarını kontrol edin."
                        )
                else:
                    QMessageBox.warning(
                        dialog,
                        "Rapor Hatası",
                        "Rapor verileri bulunamadı."
                    )
            except Exception as e:
                QMessageBox.critical(
                    dialog,
                    "Rapor Hatası",
                    f"Excel raporu oluşturulurken hata oluştu:\n\n{str(e)}"
                )
        
        download_btn.clicked.connect(download_report)
        report_layout.addWidget(download_btn)
        
        layout.addLayout(report_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # Dialog'u göster
        dialog.exec_()
            
    def update_progress(self, current, total):
        """İlerleme çubuğunu güncelle"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
    
    def update_status(self, message):
        """Durum mesajını güncelle"""
        self.status_label.setText(message)
    
    def log_message(self, message):
        """Log mesajı ekle"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            
            self.log_text.append(formatted_message)
            # Otomatik kaydırma
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            print(f"Log mesajı eklenirken hata: {e}")
    
    def clear_logs(self):
        """Log alanını temizle"""
        self.log_text.clear()
        self.log_message("Loglar temizlendi")
    

    

