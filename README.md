# Azure DevOps User Manager

🚀 **Azure DevOps kullanıcı ve takım yönetimi için kapsamlı Python uygulaması**

Azure DevOps organizasyonlarında kullanıcı ekleme, takım atama ve toplu işlem yönetimi için geliştirilmiş modern PyQt5 tabanlı masaüstü uygulaması.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![Azure DevOps](https://img.shields.io/badge/Azure%20DevOps-API-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Yapılandırma](#-yapılandırma)
- [Excel Dosya Formatı](#-excel-dosya-formatı)
- [Kimlik Doğrulama](#-kimlik-doğrulama)
- [Proje Yapısı](#-proje-yapısı)
- [API Dokümantasyonu](#-api-dokümantasyonu)
- [Sorun Giderme](#-sorun-giderme)
- [Katkıda Bulunma](#-katkıda-bulunma)

---

## 🎯 Özellikler

### 🔐 Kimlik Doğrulama
- ✅ **Azure CLI tabanlı kimlik doğrulama** (önerilen)
- ✅ **PAT Token desteği** (geriye dönük uyumluluk)
- ✅ **Uygulama içi Azure CLI login**
- ✅ **Otomatik kimlik doğrulama durumu kontrolü**

### 👥 Kullanıcı Yönetimi
- ✅ **Excel'den toplu kullanıcı ekleme**
- ✅ **Organizasyona otomatik davet**
- ✅ **Takımlara otomatik atama**
- ✅ **Rol bazlı yetki yönetimi**
- ✅ **Kullanıcı varlık kontrolü**

### 🏢 Takım Yönetimi
- ✅ **Takım listeleme ve üye yönetimi**
- ✅ **Çoklu takım ataması**
- ✅ **Admin/Member rol ataması**
- ✅ **Özel grup desteği**

### 📊 Gelişmiş Özellikler
- ✅ **Akıllı cache sistemi** (5 dakika TTL)
- ✅ **Toplu işlem optimizasyonu**
- ✅ **Gerçek zamanlı durum güncellemeleri**
- ✅ **Detaylı hata raporlama**
- ✅ **Excel rapor çıktısı**

### 💻 Kullanıcı Arayüzü
- ✅ **Modern PyQt5 GUI**
- ✅ **Kullanıcı dostu tasarım**
- ✅ **İlerleme çubuğu ve durum mesajları**
- ✅ **Çoklu dil desteği** (Türkçe/İngilizce)

---

## 🛠️ Kurulum

### Sistem Gereksinimleri
- **Python 3.9+**
- **Azure CLI** (önerilen kimlik doğrulama için)
- **macOS/Windows/Linux** desteği

### 1. Projeyi İndirin
```bash
git clone https://github.com/sahinbolukbasi/azure-devops-user-manager.git
cd azure-devops-user-manager
```

### 2. Virtual Environment Oluşturun
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Azure CLI Kurulumu (Önerilen)
```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 5. Yapılandırma Dosyası
```bash
cp config.json.template config.json
```

`config.json` dosyasını düzenleyin:
```json
{
  "organization_url": "https://dev.azure.com/your-organization/",
  "pat_token": "",
  "project_name": "Your-Project-Name"
}
```

---

## 🚀 Kullanım

### 1. Azure CLI ile Giriş (Önerilen)
```bash
az login
```

### 2. Uygulamayı Başlatın
```bash
python3 main.py
```

### 3. GUI Üzerinden İşlemler

#### Azure CLI Login
1. **"Azure CLI Girişi Yap"** butonuna tıklayın
2. Tarayıcıda açılan sayfada Azure hesabınızla giriş yapın
3. **"Durumu Yenile"** ile giriş durumunu kontrol edin

#### Ayarlar Yapılandırması
1. **"Ayarlar"** butonuna tıklayın
2. **Organization URL** ve **Project Name** bilgilerini girin
3. **"Kaydet"** butonuna tıklayın

#### Kullanıcı Ekleme İşlemi
1. **"Excel Dosyası Seç"** butonuna tıklayın
2. Kullanıcı bilgilerini içeren Excel dosyasını seçin
3. **"İşlemi Başlat"** butonuna tıklayın
4. İşlem tamamlandığında sonuç raporunu inceleyin

---

## ⚙️ Yapılandırma

### config.json Parametreleri

| Parametre | Açıklama | Örnek |
|-----------|----------|-------|
| `organization_url` | Azure DevOps organizasyon URL'i | `https://dev.azure.com/myorg/` |
| `project_name` | Proje adı | `MyProject` |
| `pat_token` | Personal Access Token (opsiyonel) | `your-pat-token` |

### Kimlik Doğrulama Seçenekleri

#### 1. Azure CLI (Önerilen) ✅
```bash
az login
az devops configure --defaults organization=https://dev.azure.com/myorg/
```

#### 2. PAT Token
1. Azure DevOps → User Settings → Personal Access Tokens
2. **New Token** oluşturun
3. **Work Items (Read & Write)** ve **Project and Team (Read & Write)** izinleri verin
4. Token'ı `config.json` dosyasına ekleyin

---

## 📊 Excel Dosya Formatı

Excel dosyanız aşağıdaki kolonları içermelidir:

| Kolon Adı | Açıklama | Örnek |
|-----------|----------|-------|
| `User Email` | Kullanıcının e-posta adresi | `user@example.com` |
| `Team Name` | Eklenecek takım adı | `Development Team` |
| `Role` | Kullanıcının rolü | `Member` veya `Admin` |
| `Action` | Yapılacak işlem | `add` veya `remove` |

### Örnek Excel İçeriği:
```
User Email              | Team Name         | Role   | Action
user1@example.com      | Development Team  | Member | add
user2@example.com      | QA Team          | Admin  | add
user3@example.com      | Design Team      | Member | add
```

### Desteklenen Roller:
- **Member**: Standart takım üyesi
- **Admin**: Takım yöneticisi

### Desteklenen İşlemler:
- **add**: Kullanıcıyı takıma ekle
- **remove**: Kullanıcıyı takımdan çıkar

---

## 🔐 Kimlik Doğrulama

### Azure CLI Kimlik Doğrulama (Önerilen)

**Avantajları:**
- 🔐 Daha güvenli (token saklamaya gerek yok)
- 🔄 Otomatik token yenileme
- 🏢 Çoklu organizasyon desteği
- ✅ Microsoft tarafından önerilen yöntem

**Kurulum:**
```bash
# Azure CLI kurulumu
az login

# Azure DevOps extension kurulumu (otomatik)
az extension add --name azure-devops

# Varsayılan organizasyon ayarlama
az devops configure --defaults organization=https://dev.azure.com/myorg/
```

### PAT Token Kimlik Doğrulama

**Kullanım Senaryoları:**
- CI/CD pipeline'ları
- Otomatik scriptler
- Azure CLI kullanılamayan ortamlar

**Token Oluşturma:**
1. Azure DevOps → User Settings → Personal Access Tokens
2. **New Token** → **Custom defined**
3. **Gerekli İzinler:**
   - Work Items: Read & Write
   - Project and Team: Read & Write
   - Graph: Read
   - User Profile: Read

---

## 📁 Proje Yapısı

```
azure-devops-user-manager/
├── 📁 core/                          # Ana iş mantığı
│   ├── azure_cli_client.py           # Azure CLI client
│   ├── azure_rest_client.py          # REST API client
│   ├── enhanced_azure_cli_client.py  # Gelişmiş CLI client
│   └── streamlined_processor.py      # Optimize edilmiş işlemci
├── 📁 gui/                           # Kullanıcı arayüzü
│   ├── main_window.py                # Ana pencere
│   ├── settings_window.py            # Ayarlar penceresi
│   └── process_thread.py             # Background işlem thread'i
├── 📁 utils/                         # Yardımcı araçlar
│   └── excel_processor.py            # Excel dosya işleyici
├── 📁 docs/                          # Dokümantasyon
│   └── FUNCTION_DOCUMENTATION.md     # API dokümantasyonu
├── 📁 tests/                         # Test dosyaları
│   └── test_azure_cli.py             # Azure CLI testleri
├── main.py                           # Ana uygulama
├── config.json.template              # Yapılandırma şablonu
├── requirements.txt                  # Python bağımlılıkları
├── azure_devops_manager.spec         # PyInstaller spec
└── README.md                         # Bu dosya
```

### Core Modülleri

#### `azure_rest_client.py`
- Azure DevOps REST API client'ı
- 34 fonksiyon ile kapsamlı API desteği
- Cache sistemi ve performans optimizasyonu
- Çoklu fallback mekanizması

#### `enhanced_azure_cli_client.py`
- Azure CLI tabanlı gelişmiş client
- Toplu işlem desteği
- Otomatik hata yönetimi

#### `streamlined_processor.py`
- Optimize edilmiş kullanıcı ekleme işlemci
- Tek adımda org + takım ekleme
- %70 daha hızlı işlem

### GUI Modülleri

#### `main_window.py`
- Ana uygulama penceresi
- Azure CLI login entegrasyonu
- Real-time status updates

#### `settings_window.py`
- Yapılandırma yönetimi
- Bağlantı test sistemi
- Kullanıcı dostu ayarlar

---

## 📚 API Dokümantasyonu

Detaylı API dokümantasyonu için: [`docs/FUNCTION_DOCUMENTATION.md`](docs/FUNCTION_DOCUMENTATION.md)

### Temel API Kullanımı

```python
from core.azure_rest_client import AzureDevOpsRESTClient

# Client oluşturma
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
)

# Bağlantı testi
if client.test_connection():
    print("✅ Bağlantı başarılı")

# Takımları listele
teams = client.get_teams()
for team in teams:
    print(f"Takım: {team['name']}")

# Kullanıcı ekleme
success = client.add_user_to_any_group(
    user_email="user@example.com",
    group_name="Development Team",
    role="Member"
)
```

### Toplu İşlem Örneği

```python
# Toplu kullanıcı kontrolü
users = ["user1@example.com", "user2@example.com"]
results = client.check_multiple_users_exist(users)

# Mevcut olmayan kullanıcıları davet et
missing_users = [email for email, exists in results.items() if not exists]
if missing_users:
    invite_results = client.invite_multiple_users_batch(missing_users, "basic")
```

---

## 🐛 Sorun Giderme

### Sık Karşılaşılan Sorunlar

#### 1. Azure CLI Login Sorunu
```bash
# Çözüm 1: Yeniden login
az logout
az login

# Çözüm 2: Device code ile login
az login --use-device-code

# Çözüm 3: Subscription olmadan login
az login --allow-no-subscriptions
```

#### 2. API 404 Hatası
- **Sebep**: User Entitlements API organizasyonda kısıtlı
- **Çözüm**: Azure CLI kimlik doğrulama kullanın
- **Alternatif**: Teams API ile doğrudan ekleme

#### 3. Kullanıcı Ekleme Başarısız
- **Kontrol 1**: Kullanıcı organizasyonda var mı?
- **Kontrol 2**: Takım adı doğru mu?
- **Kontrol 3**: Yeterli yetki var mı?

#### 4. Excel Dosya Okuma Hatası
- **Format**: `.xlsx` veya `.xls` formatında olmalı
- **Kolonlar**: Gerekli kolonların varlığını kontrol edin
- **Encoding**: UTF-8 encoding kullanın

### Debug Modu

```bash
# Detaylı log çıktısı için
export AZURE_DEVOPS_DEBUG=1
python3 main.py
```

### Log Dosyaları

```bash
# Log dosyalarını kontrol edin
tail -f logs/azure_devops.log
```

---

## 🧪 Test Etme

### Manuel Test
```bash
python3 tests/test_azure_cli.py
```

### GUI Test
```bash
python3 main.py
# Test senaryolarını GUI üzerinden çalıştırın
```

### API Test
```python
from core.azure_rest_client import AzureDevOpsRESTClient

client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
)

# Bağlantı testi
assert client.test_connection() == True

# Takım listesi testi
teams = client.get_teams()
assert len(teams) > 0
```

---

## 📦 Executable Oluşturma

### PyInstaller ile Build

```bash
# Tek dosya executable
pyinstaller --onefile --windowed main.py

# Spec dosyası ile build
pyinstaller azure_devops_manager.spec
```

### Build Çıktıları
- **macOS**: `dist/azure_devops_manager.app`
- **Windows**: `dist/azure_devops_manager.exe`
- **Linux**: `dist/azure_devops_manager`

---

## 🔄 Güncelleme

### Uygulama Güncellemesi
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Bağımlılık Güncellemesi
```bash
pip install --upgrade PyQt5 requests pandas openpyxl
```

---

## 🤝 Katkıda Bulunma

### Geliştirme Süreci
1. **Fork** yapın
2. **Feature branch** oluşturun (`git checkout -b feature/new-feature`)
3. **Commit** yapın (`git commit -am 'Add new feature'`)
4. **Push** edin (`git push origin feature/new-feature`)
5. **Pull Request** oluşturun

### Kod Standartları
- **PEP 8** Python kod standardı
- **Type hints** kullanın
- **Docstring** yazın
- **Unit test** ekleyin

### Test Gereksinimleri
```bash
# Test çalıştırma
python -m pytest tests/

# Coverage raporu
coverage run -m pytest
coverage report
```

---

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👨‍💻 Geliştirici

**Şahin Bölükbaşı**
- GitHub: [@sahinbolukbasi](https://github.com/sahinbolukbasi)
- Email: [contact@example.com](mailto:contact@example.com)

---

## 🙏 Teşekkürler

- **Microsoft Azure DevOps Team** - API dokümantasyonu için
- **PyQt5 Community** - GUI framework için
- **Python Community** - Açık kaynak kütüphaneler için

---

## 📈 Sürüm Geçmişi

### v2.0.0 (Mevcut)
- ✅ Azure CLI tabanlı kimlik doğrulama
- ✅ Gelişmiş cache sistemi
- ✅ Toplu işlem desteği
- ✅ Modern PyQt5 GUI
- ✅ Kapsamlı hata yönetimi

### v1.0.0
- PAT token tabanlı sistem
- Temel GUI
- Excel dosya desteği
- Basit kullanıcı ekleme

---

## 🔗 Faydalı Bağlantılar

- [Azure DevOps REST API Dokümantasyonu](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
- [Azure CLI Dokümantasyonu](https://docs.microsoft.com/en-us/cli/azure/)
- [PyQt5 Dokümantasyonu](https://doc.qt.io/qtforpython/)
- [Python Packaging Guide](https://packaging.python.org/)

---

**⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!**
