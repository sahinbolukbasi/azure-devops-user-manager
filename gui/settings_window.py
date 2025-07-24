import tkinter as tk
from tkinter import ttk, messagebox
import threading

class SettingsWindow:
    def __init__(self, parent, config_manager, callback=None):
        self.config_manager = config_manager
        self.callback = callback
        
        # Pencere oluştur
        self.window = tk.Toplevel(parent)
        self.window.title("Ayarlar")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Mevcut ayarları yükle
        self.config = self.config_manager.get_config()
        
        self.setup_ui()
        self.load_current_settings()
        
        # Pencereyi ortala
        self.center_window()
    
    def setup_ui(self):
        """Ayarlar arayüzünü oluştur"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Azure DevOps Ayarları", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Organization URL
        ttk.Label(main_frame, text="Organization URL:").pack(anchor=tk.W)
        self.org_url_var = tk.StringVar()
        org_entry = ttk.Entry(main_frame, textvariable=self.org_url_var, width=60)
        org_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Yardım metni
        help_label = ttk.Label(main_frame, 
                              text="Örnek: https://dev.azure.com/yourorganization", 
                              foreground="gray", font=("Arial", 8))
        help_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Personal Access Token
        ttk.Label(main_frame, text="Personal Access Token (PAT):").pack(anchor=tk.W)
        self.pat_var = tk.StringVar()
        pat_entry = ttk.Entry(main_frame, textvariable=self.pat_var, 
                             width=60, show="*")
        pat_entry.pack(fill=tk.X, pady=(5, 15))
        
        # PAT yardım metni
        pat_help = ttk.Label(main_frame, 
                            text="Azure DevOps'tan Personal Access Token oluşturun", 
                            foreground="gray", font=("Arial", 8))
        pat_help.pack(anchor=tk.W, pady=(0, 10))
        
        # Project Name
        ttk.Label(main_frame, text="Proje Adı:").pack(anchor=tk.W)
        self.project_var = tk.StringVar()
        project_entry = ttk.Entry(main_frame, textvariable=self.project_var, width=60)
        project_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Test bağlantısı butonu
        self.test_btn = ttk.Button(main_frame, text="🔗 Bağlantıyı Test Et", 
                                  command=self.test_connection)
        self.test_btn.pack(pady=10)
        
        # Buton çerçevesi
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Kaydet butonu
        save_btn = ttk.Button(button_frame, text="💾 Kaydet", 
                             command=self.save_settings)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # İptal butonu
        cancel_btn = ttk.Button(button_frame, text="❌ İptal", 
                               command=self.window.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def center_window(self):
        """Pencereyi ekranın ortasına yerleştir"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"500x400+{x}+{y}")
    
    def load_current_settings(self):
        """Mevcut ayarları form alanlarına yükle"""
        self.org_url_var.set(self.config.get('organization_url', ''))
        self.pat_var.set(self.config.get('pat_token', ''))
        self.project_var.set(self.config.get('project_name', ''))
    
    def test_connection(self):
        """Bağlantıyı test et"""
        org_url = self.org_url_var.get().strip()
        pat_token = self.pat_var.get().strip()
        project_name = self.project_var.get().strip()
        
        if not all([org_url, pat_token, project_name]):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun")
            return
        
        # Test butonunu devre dışı bırak
        self.test_btn.config(state="disabled", text="Test ediliyor...")
        
        # Thread'de test et
        thread = threading.Thread(target=self._test_connection_thread, 
                                args=(org_url, pat_token, project_name))
        thread.daemon = True
        thread.start()
    
    def _test_connection_thread(self, org_url, pat_token, project_name):
        """Bağlantı testini thread'de çalıştır"""
        try:
            from core.azure_client import AzureDevOpsClient
            
            client = AzureDevOpsClient(org_url, pat_token, project_name)
            result = client.test_connection()
            
            if result:
                messagebox.showinfo("Başarılı", "✅ Bağlantı başarıyla test edildi!")
            else:
                messagebox.showerror("Hata", "❌ Bağlantı test edilemedi. Lütfen ayarları kontrol edin.")
                
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Bağlantı hatası:\n{str(e)}")
        
        finally:
            # Test butonunu yeniden etkinleştir
            self.test_btn.config(state="normal", text="🔗 Bağlantıyı Test Et")
    
    def save_settings(self):
        """Ayarları kaydet"""
        org_url = self.org_url_var.get().strip()
        pat_token = self.pat_var.get().strip()
        project_name = self.project_var.get().strip()
        
        if not all([org_url, pat_token, project_name]):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun")
            return
        
        # URL formatını kontrol et
        if not org_url.startswith('https://'):
            messagebox.showerror("Hata", "Organization URL 'https://' ile başlamalıdır")
            return
        
        try:
            # Ayarları kaydet
            self.config_manager.save_config({
                'organization_url': org_url,
                'pat_token': pat_token,
                'project_name': project_name
            })
            
            messagebox.showinfo("Başarılı", "Ayarlar başarıyla kaydedildi!")
            
            # Callback'i çağır
            if self.callback:
                self.callback()
            
            # Pencereyi kapat
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi:\n{str(e)}")