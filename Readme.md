# Azure DevOps Kullanıcı Atama Aracı

Excel şablonu kullanarak Azure DevOps projelerinde takımlara kullanıcı ataması yapabilen cross-platform Python uygulaması.

## Özellikler

- 🖥️ **Cross-Platform**: Mac ve Windows'ta çalışır
- 📊 **Excel Entegrasyonu**: Basit şablon formatı
- ⚙️ **Azure DevOps API**: RESTful API entegrasyonu
- 🔒 **Güvenli**: Token şifreleme
- 🎨 **Modern GUI**: Kullanıcı dostu arayüz

## Kurulum

1. **Repository'yi klonlayın:**
```bash
git clone https://github.com/sahinbolukbasi/azure-devops-user-manager.git
cd azure-devops-user-manager
```

2. **Gereksinimları yükleyin:**
```bash
pip install -r requirements.txt
```

3. **Uygulamayı başlatın:**
```bash
python main.py
```

## Kullanım

### 1. Ayarları Yapın
- Sol üst köşedeki "⚙️ Ayarlar" butonuna tıklayın
- Azure DevOps organization URL'nizi girin
- Personal Access Token (PAT) oluşturun ve girin
- Proje adını girin
- "Bağlantıyı Test Et" ile kontrol edin
- Ayarları kaydedin

### 2. Excel Şablonu Hazırlayın
Excel dosyanız şu sütunları içermelidir:

| Team Name | User Email | Role | Action |
|-----------|------------|------|--------|
| Development Team | user@example.com | Member | Add |
| QA Team | user2@example.com | Admin | Remove |

**Sütun Açıklamaları:**
- **Team Name**: Azure DevOps'taki takım adı
- **User Email**: Kullanıcının email adresi
- **Role**: Member, Admin, Contributor, Reader
- **Action**: Add (ekle) veya Remove (çıkar)

### 3. İşlemi Başlatın
- "📁 Dosya Seç" ile Excel dosyanızı seçin
- "🚀 İşlemi Başlat" butonuna tıklayın
- İşlem durumunu loglardan takip edin

## Personal Access Token (PAT) Oluşturma

1. Azure DevOps'a gidin
2. Sağ üst köşede profil resminize tıklayın
3. "Personal access tokens" seçin
4. "New Token" butonuna tıklayın
5. Gerekli izinleri verin:
   - **Project and Team**: Read & Write
   - **Identity**: Read
   - **Graph**: Read
6. Token'ı kopyalayın ve uygulamaya girin

## Desteklenen Roller

- **Member**: Standart takım üyesi
- **Admin**: Takım yöneticisi
- **Contributor**: Katkıda bulunan
- **Reader**: Sadece okuma yetkisi

## Güvenlik

- PAT token'lar şifrelenmiş olarak saklanır
- Bağlantı bilgileri güvenli şekilde tutulur
- API çağrılarında SSL/TLS kullanılır

## Hata Durumları

Yaygın hatalar ve çözümleri:

- **"Takım bulunamadı"**: Takım adını doğru yazdığınızdan emin olun
- **"Kullanıcı bulunamadı"**: Email adresinin doğru olduğunu kontrol edin
- **"Yetki hatası"**: PAT token'ın gerekli izinlere sahip olduğunu kontrol edin

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

## Lisans

MIT License# azure-devops-user-manager
# azure-devops-user-manager
