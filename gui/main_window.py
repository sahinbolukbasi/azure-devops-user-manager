import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from .settings_window import SettingsWindow
from core.excel_processor import ExcelProcessor
from core.azure_client import AzureDevOpsClient
from core.config_manager import ConfigManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Azure DevOps Kullanıcı Atama Aracı")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.config_manager = ConfigManager()
        self.excel_processor = ExcelProcessor()
        self.azure_client = None
        self.selected_file = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Ana arayüzü oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Settings butonu (sol üst)
        settings_btn = ttk.Button(main_frame, text="⚙️ Ayarlar", 
                                 command=self.open_settings)
        settings_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 20))
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Azure DevOps Kullanıcı Atama Aracı", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=(0, 30))
        
        # Dosya seçimi bölümü
        file_frame = ttk.LabelFrame(main_frame, text="Excel Dosyası Seç", padding="15")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Dosya yolu gösterici
        self.file_var = tk.StringVar(value="Henüz dosya seçilmedi...")
        file_label = ttk.Label(file_frame, textvariable=self.file_var, 
                              foreground="gray", wraplength=400)
        file_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Dosya seç butonu
        browse_btn = ttk.Button(file_frame, text="📁 Dosya Seç", 
                               command=self.browse_file)
        browse_btn.grid(row=1, column=0, padx=(0, 10))
        
        # Örnek şablon indir butonu
        template_btn = ttk.Button(file_frame, text="📄 Örnek Şablon İndir", 
                                 command=self.download_template)
        template_btn.grid(row=1, column=1)
        
        # İşlem butonu
        self.process_btn = ttk.Button(main_frame, text="🚀 İşlemi Başlat", 
                                     command=self.start_processing, 
                                     state="disabled")
        self.process_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Durum mesajı
        self.status_var = tk.StringVar(value="Hazır")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=2)
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="İşlem Logları", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def open_settings(self):
        """Ayarlar penceresini aç"""
        SettingsWindow(self.root, self.config_manager, self.on_settings_saved)
    
    def on_settings_saved(self):
        """Ayarlar kaydedildiğinde çağrılır"""
        self.log_message("Ayarlar kaydedildi")
        self.check_ready_state()
    
    def browse_file(self):
        """Excel dosyası seç"""
        file_path = filedialog.askopenfilename(
            title="Excel Dosyası Seç",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_var.set(f"Seçili: {file_path.split('/')[-1]}")
            self.check_ready_state()
            self.log_message(f"Dosya seçildi: {file_path}")
    
    def download_template(self):
        """Örnek şablon dosyası oluştur"""
        try:
            self.excel_processor.create_sample_template()
            messagebox.showinfo("Başarılı", "Örnek şablon 'sample_template.xlsx' olarak kaydedildi")
            self.log_message("Örnek şablon oluşturuldu")
        except Exception as e:
            messagebox.showerror("Hata", f"Şablon oluşturulamadı: {str(e)}")
            self.log_message(f"Şablon oluşturma hatası: {str(e)}")
    
    def check_ready_state(self):
        """İşlem başlatma butonunun durumunu kontrol et"""
        config = self.config_manager.get_config()
        has_config = all([config.get('organization_url'), 
                         config.get('pat_token'), 
                         config.get('project_name')])
        has_file = self.selected_file is not None
        
        if has_config and has_file:
            self.process_btn.config(state="normal")
        else:
            self.process_btn.config(state="disabled")
    
    def start_processing(self):
        """İşlemi başlat (thread'de)"""
        if not self.selected_file:
            messagebox.showerror("Hata", "Lütfen önce bir Excel dosyası seçin")
            return
        
        # UI'yi devre dışı bırak
        self.process_btn.config(state="disabled")
        self.progress.start()
        self.status_var.set("İşlem başlatılıyor...")
        
        # Thread'de işlemi başlat
        thread = threading.Thread(target=self.process_file)
        thread.daemon = True
        thread.start()
    
    def process_file(self):
        """Excel dosyasını işle"""
        try:
            # Azure client oluştur
            config = self.config_manager.get_config()
            self.azure_client = AzureDevOpsClient(
                config['organization_url'],
                config['pat_token'],
                config['project_name']
            )
            
            self.log_message("Azure DevOps bağlantısı kuruluyor...")
            
            # Excel dosyasını oku
            self.log_message("Excel dosyası okunuyor...")
            data = self.excel_processor.read_excel(self.selected_file)
            
            if data.empty:
                raise Exception("Excel dosyası boş veya geçersiz format")
            
            # Her satırı işle
            total_rows = len(data)
            success_count = 0
            error_count = 0
            
            for index, row in data.iterrows():
                try:
                    team_name = row['Team Name']
                    user_email = row['User Email']
                    role = row['Role']
                    action = row['Action']
                    
                    self.status_var.set(f"İşleniyor: {index + 1}/{total_rows}")
                    self.log_message(f"İşlem: {action} - {user_email} -> {team_name}")
                    
                    if action.lower() == 'add':
                        result = self.azure_client.add_user_to_team(team_name, user_email, role)
                    elif action.lower() == 'remove':
                        result = self.azure_client.remove_user_from_team(team_name, user_email)
                    else:
                        raise Exception(f"Geçersiz işlem: {action}")
                    
                    if result:
                        success_count += 1
                        self.log_message(f"✅ Başarılı: {user_email}")
                    else:
                        error_count += 1
                        self.log_message(f"❌ Başarısız: {user_email}")
                        
                except Exception as e:
                    error_count += 1
                    self.log_message(f"❌ Hata ({index + 1}): {str(e)}")
            
            # İşlem tamamlandı
            self.status_var.set(f"Tamamlandı: {success_count} başarılı, {error_count} hata")
            self.log_message(f"\n🎉 İşlem tamamlandı! Başarılı: {success_count}, Hata: {error_count}")
            
            messagebox.showinfo("Tamamlandı", 
                              f"İşlem tamamlandı!\nBaşarılı: {success_count}\nHata: {error_count}")
            
        except Exception as e:
            self.status_var.set("Hata oluştu")
            self.log_message(f"❌ Kritik hata: {str(e)}")
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu:\n{str(e)}")
        
        finally:
            # UI'yi yeniden etkinleştir
            self.progress.stop()
            self.process_btn.config(state="normal")
    
    def log_message(self, message):
        """Log mesajı ekle"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()