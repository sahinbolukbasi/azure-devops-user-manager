# Azure DevOps REST Client - Fonksiyon Dokümantasyonu

## 📋 İçindekiler
- [Genel Bakış](#genel-bakış)
- [Sınıf Yapısı](#sınıf-yapısı)
- [Temel Fonksiyonlar](#temel-fonksiyonlar)
- [Kullanıcı Yönetimi](#kullanıcı-yönetimi)
- [Takım Yönetimi](#takım-yönetimi)
- [Cache Sistemi](#cache-sistemi)
- [Güvenlik ve Kimlik Doğrulama](#güvenlik-ve-kimlik-doğrulama)
- [Hata Yönetimi](#hata-yönetimi)
- [Kullanım Örnekleri](#kullanım-örnekleri)

---

## 🎯 Genel Bakış

`AzureDevOpsRESTClient` sınıfı, Azure DevOps REST API'si kullanarak kullanıcı ve takım yönetimi işlemlerini gerçekleştiren kapsamlı bir Python client'ıdır.

### Temel Özellikler
- ✅ Azure CLI tabanlı kimlik doğrulama
- ✅ PAT token desteği (geriye dönük uyumluluk)
- ✅ Akıllı cache sistemi (5 dakika TTL)
- ✅ Toplu işlem desteği
- ✅ Gelişmiş hata yönetimi
- ✅ Çoklu fallback mekanizması

---

## 🏗️ Sınıf Yapısı

### AzureDevOpsRESTClient

```python
class AzureDevOpsRESTClient:
    """Azure DevOps REST API Client"""
```

#### Cache Sistemi
- `_teams_cache`: Takım bilgileri cache'i
- `_org_users_cache`: Organizasyon kullanıcıları cache'i
- `_project_id_cache`: Proje ID cache'i
- `_cache_ttl`: Cache süresi (300 saniye)

#### Batch İşlem Sistemi
- `_pending_invitations`: Bekleyen davetler listesi
- `_batch_size`: Toplu işlem boyutu (10 kullanıcı)

---

## 🔧 Temel Fonksiyonlar

### `__init__(self, organization_url: str, project_name: str, pat_token: str = None)`

**Amaç:** Azure DevOps REST API Client'ı başlatır

**Parametreler:**
- `organization_url` (str): Azure DevOps organizasyon URL'i
- `project_name` (str): Proje adı
- `pat_token` (str, opsiyonel): Personal Access Token

**Özellikler:**
- Azure CLI tabanlı kimlik doğrulama (önerilen)
- PAT token desteği (geriye dönük uyumluluk)
- Otomatik endpoint yapılandırması
- Cache sistemi başlatma

**Örnek Kullanım:**
```python
# Azure CLI ile (önerilen)
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
)

# PAT token ile
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject",
    pat_token="your-pat-token"
)
```

---

### `test_connection(self) -> bool`

**Amaç:** Azure DevOps bağlantısını test eder

**Döndürür:** 
- `bool`: Bağlantı başarılı ise True, değilse False

**İşlem Adımları:**
1. Projects API endpoint'ini test eder
2. Belirtilen proje adının varlığını kontrol eder
3. Mevcut projeleri listeler (hata durumunda)

**Örnek Kullanım:**
```python
if client.test_connection():
    print("✅ Bağlantı başarılı")
else:
    print("❌ Bağlantı hatası")
```

---

## 👥 Kullanıcı Yönetimi

### `check_user_exists_in_org(self, user_email: str) -> bool`

**Amaç:** Kullanıcının organizasyonda olup olmadığını kontrol eder (cache ile optimize edilmiş)

**Parametreler:**
- `user_email` (str): Kontrol edilecek kullanıcının e-posta adresi

**Döndürür:**
- `bool`: Kullanıcı organizasyonda varsa True, yoksa False

**Özellikler:**
- ⚡ Cache sistemi ile hızlı sorgulama
- 🔄 Otomatik cache yenileme
- 📊 Performans optimizasyonu

**Örnek Kullanım:**
```python
if client.check_user_exists_in_org("user@example.com"):
    print("Kullanıcı organizasyonda mevcut")
else:
    print("Kullanıcı organizasyonda bulunamadı")
```

---

### `check_multiple_users_exist(self, user_emails: List[str]) -> Dict[str, bool]`

**Amaç:** Birden fazla kullanıcının organizasyonda olup olmadığını toplu kontrol eder

**Parametreler:**
- `user_emails` (List[str]): Kontrol edilecek kullanıcıların e-posta listesi

**Döndürür:**
- `Dict[str, bool]`: Her kullanıcı için varlık durumu

**Avantajlar:**
- 🚀 Toplu işlem performansı
- 📊 Tek API çağrısı ile çoklu kontrol
- 💾 Cache optimizasyonu

**Örnek Kullanım:**
```python
users = ["user1@example.com", "user2@example.com", "user3@example.com"]
results = client.check_multiple_users_exist(users)

for email, exists in results.items():
    status = "✅ Mevcut" if exists else "❌ Yok"
    print(f"{email}: {status}")
```

---

### `invite_user_to_organization(self, user_email: str, license_type: str = "stakeholder", team_name: str = None, role: str = "Member") -> bool`

**Amaç:** Kullanıcıyı organizasyona davet eder ve isteğe bağlı olarak doğrudan takıma ekler

**Parametreler:**
- `user_email` (str): Davet edilecek kullanıcının e-posta adresi
- `license_type` (str): Lisans tipi ("stakeholder", "basic", "basic+testplans")
- `team_name` (str, opsiyonel): Doğrudan eklenecek takım adı
- `role` (str): Takımdaki rol ("Member", "Admin")

**Döndürür:**
- `bool`: İşlem başarılı ise True, değilse False

**İşlem Adımları:**
1. Kullanıcının organizasyonda olup olmadığını kontrol eder
2. User Entitlements API ile organizasyona davet eder
3. İsteğe bağlı olarak belirtilen takıma ekler
4. Detaylı hata raporlama

**Örnek Kullanım:**
```python
# Sadece organizasyona davet
success = client.invite_user_to_organization(
    user_email="newuser@example.com",
    license_type="basic"
)

# Organizasyona davet + takıma ekleme
success = client.invite_user_to_organization(
    user_email="newuser@example.com",
    license_type="basic",
    team_name="Development Team",
    role="Member"
)
```

---

### `invite_multiple_users_batch(self, user_emails: List[str], license_type: str = "stakeholder") -> Dict[str, bool]`

**Amaç:** Birden fazla kullanıcıyı toplu olarak organizasyona davet eder

**Parametreler:**
- `user_emails` (List[str]): Davet edilecek kullanıcıların e-posta listesi
- `license_type` (str): Tüm kullanıcılar için lisans tipi

**Döndürür:**
- `Dict[str, bool]`: Her kullanıcı için davet sonucu

**Avantajlar:**
- 🚀 Toplu işlem performansı
- 📊 Batch processing ile API optimizasyonu
- 🔄 Otomatik retry mekanizması

**Örnek Kullanım:**
```python
users = ["user1@example.com", "user2@example.com", "user3@example.com"]
results = client.invite_multiple_users_batch(users, "basic")

for email, success in results.items():
    status = "✅ Başarılı" if success else "❌ Başarısız"
    print(f"{email}: {status}")
```

---

## 🏢 Takım Yönetimi

### `get_teams(self) -> List[Dict]`

**Amaç:** Proje takımlarını listeler (cache ile optimize edilmiş)

**Döndürür:**
- `List[Dict]`: Takım bilgileri listesi

**Takım Bilgileri:**
- `id`: Takım ID'si
- `name`: Takım adı
- `description`: Takım açıklaması
- `url`: Takım URL'i

**Özellikler:**
- ⚡ Cache sistemi (5 dakika TTL)
- 🔄 Otomatik cache yenileme
- 📊 Performans optimizasyonu

**Örnek Kullanım:**
```python
teams = client.get_teams()
for team in teams:
    print(f"Takım: {team['name']} (ID: {team['id']})")
```

---

### `get_team_members(self, team_id: str) -> List[Dict]`

**Amaç:** Belirtilen takımın üyelerini listeler

**Parametreler:**
- `team_id` (str): Takım ID'si

**Döndürür:**
- `List[Dict]`: Takım üyeleri listesi

**Üye Bilgileri:**
- `identity`: Kullanıcı kimlik bilgileri
- `isTeamAdmin`: Admin yetkisi durumu

**Örnek Kullanım:**
```python
team_members = client.get_team_members("team-id-123")
for member in team_members:
    name = member['identity']['displayName']
    email = member['identity']['uniqueName']
    is_admin = member.get('isTeamAdmin', False)
    role = "Admin" if is_admin else "Member"
    print(f"{name} ({email}) - {role}")
```

---

### `add_user_to_any_group(self, user_email: str, group_name: str, role: str = 'Member') -> bool`

**Amaç:** Kullanıcıyı herhangi bir gruba (takım veya güvenlik grubu) ekler

**Parametreler:**
- `user_email` (str): Kullanıcı e-posta adresi
- `group_name` (str): Grup adı (takım veya güvenlik grubu)
- `role` (str): Kullanıcının rolü (sadece takımlar için)

**Döndürür:**
- `bool`: İşlem başarılı ise True, değilse False

**İşlem Adımları:**
1. Grup tipini tespit eder (takım/güvenlik grubu)
2. Uygun API endpoint'ini seçer
3. Kullanıcıyı gruba ekler
4. Fallback mekanizması ile alternatif yöntemleri dener

**Grup Tipleri:**
- `team`: Proje takımları
- `security`: Güvenlik grupları
- `unknown`: Bilinmeyen gruplar (özel gruplar)

**Örnek Kullanım:**
```python
# Takıma ekleme
success = client.add_user_to_any_group(
    user_email="user@example.com",
    group_name="Development Team",
    role="Member"
)

# Güvenlik grubuna ekleme
success = client.add_user_to_any_group(
    user_email="user@example.com",
    group_name="Contributors"
)
```

---

### `add_user_to_team(self, user_email: str, team_name: str, role: str = 'Member') -> bool`

**Amaç:** Kullanıcıyı takıma ekler (geriye uyumluluk için)

**Parametreler:**
- `user_email` (str): Kullanıcı e-posta adresi
- `team_name` (str): Takım adı
- `role` (str): Kullanıcı rolü

**Döndürür:**
- `bool`: İşlem başarılı ise True, değilse False

**Not:** Bu fonksiyon `add_user_to_any_group` fonksiyonuna yönlendirir.

---

## 🔍 Cache Sistemi

### `_is_cache_valid(self, cache_time) -> bool`

**Amaç:** Cache'in hala geçerli olup olmadığını kontrol eder

**Parametreler:**
- `cache_time`: Cache oluşturulma zamanı

**Döndürür:**
- `bool`: Cache geçerli ise True, değilse False

**Cache TTL:** 300 saniye (5 dakika)

---

### `_get_teams_from_cache(self) -> Optional[List[Dict]]`

**Amaç:** Cache'den takımları alır

**Döndürür:**
- `Optional[List[Dict]]`: Cache'deki takımlar veya None

**Avantajlar:**
- ⚡ Hızlı veri erişimi
- 📊 API çağrısı tasarrufu
- 🔄 Otomatik geçerlilik kontrolü

---

### `_cache_teams(self, teams: List[Dict])`

**Amaç:** Takımları cache'ler

**Parametreler:**
- `teams` (List[Dict]): Cache'lenecek takım listesi

---

### `_load_all_org_users(self) -> List[Dict]`

**Amaç:** Tüm organizasyon üyelerini yükler (cache ile optimize edilmiş)

**Döndürür:**
- `List[Dict]`: Organizasyon üyeleri listesi

**Özellikler:**
- ⚡ Cache sistemi
- 🔄 Otomatik sayfalama (pagination)
- 📊 Performans optimizasyonu

---

## 🔐 Güvenlik ve Kimlik Doğrulama

### Kimlik Doğrulama Yöntemleri

#### 1. Azure CLI (Önerilen)
```python
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
    # pat_token belirtilmez
)
```

#### 2. PAT Token (Geriye Dönük Uyumluluk)
```python
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject",
    pat_token="your-pat-token"
)
```

### Güvenlik Özellikleri
- 🔐 Azure CLI tabanlı güvenli kimlik doğrulama
- 🛡️ PAT token şifreleme
- 🔒 HTTPS zorunlu bağlantı
- 📝 Detaylı audit logging

---

## 🚨 Hata Yönetimi

### Hata Tipleri ve Çözümleri

#### 1. API Erişim Hataları
- **404 Not Found**: API endpoint'i bulunamadı
- **401 Unauthorized**: Kimlik doğrulama hatası
- **403 Forbidden**: Yetki yetersizliği

#### 2. Kullanıcı Hataları
- **Kullanıcı organizasyonda yok**: Önce organizasyona davet edilmeli
- **Takım bulunamadı**: Takım adını kontrol edin
- **Yetki yetersizliği**: Admin yetkisi gerekli

#### 3. Fallback Mekanizması

Kullanıcı ekleme işleminde 3 aşamalı fallback sistemi:

1. **Teams API ile e-posta kullanarak ekleme**
2. **Organizasyonda kullanıcı arama ve ID ile ekleme**
3. **Basit davet sistemi (alternatif endpoint'ler)**

### Hata Mesajları

```python
# Detaylı hata raporlama örneği
try:
    success = client.add_user_to_team("user@example.com", "Dev Team")
    if not success:
        print("❌ Kullanıcı ekleme başarısız")
except Exception as e:
    print(f"🚨 Hata: {str(e)}")
```

---

## 🔧 Gelişmiş Özellikler

### `wait_for_pending_invitations(self, max_wait_time: int = 30) -> int`

**Amaç:** Bekleyen davetlerin işlenmesini bekler

**Parametreler:**
- `max_wait_time` (int): Maksimum bekleme süresi (saniye)

**Döndürür:**
- `int`: İşlenen davet sayısı

**Kullanım Senaryosu:**
Toplu kullanıcı ekleme işlemlerinde, Azure DevOps'un davetleri işlemesi için bekleme süresi.

---

### `add_user_to_custom_group(self, user_email: str, group_name: str) -> bool`

**Amaç:** Özel gruplara kullanıcı ekleme - farklı API yaklaşımları

**Parametreler:**
- `user_email` (str): Kullanıcı e-posta adresi
- `group_name` (str): Özel grup adı

**Döndürür:**
- `bool`: İşlem başarılı ise True

**API Yaklaşımları:**
1. **Graph API ile grup üyeliği**
2. **Security Groups API**
3. **Teams API ile özel takım**
4. **Group Memberships API**

---

## 📚 Kullanım Örnekleri

### Temel Kullanım

```python
# Client oluşturma
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
)

# Bağlantı testi
if not client.test_connection():
    print("❌ Bağlantı hatası")
    exit(1)

# Takımları listele
teams = client.get_teams()
print(f"📋 {len(teams)} takım bulundu")

# Kullanıcı kontrolü
user_email = "newuser@example.com"
if client.check_user_exists_in_org(user_email):
    print(f"✅ {user_email} organizasyonda mevcut")
else:
    print(f"❌ {user_email} organizasyonda bulunamadı")
```

### Toplu Kullanıcı İşlemleri

```python
# Toplu kullanıcı kontrolü
users = ["user1@example.com", "user2@example.com", "user3@example.com"]
results = client.check_multiple_users_exist(users)

# Mevcut olmayan kullanıcıları davet et
missing_users = [email for email, exists in results.items() if not exists]
if missing_users:
    invite_results = client.invite_multiple_users_batch(missing_users, "basic")
    
    for email, success in invite_results.items():
        if success:
            print(f"✅ {email} başarıyla davet edildi")
        else:
            print(f"❌ {email} davet edilemedi")

# Tüm kullanıcıları takıma ekle
team_name = "Development Team"
for user_email in users:
    success = client.add_user_to_any_group(user_email, team_name, "Member")
    if success:
        print(f"✅ {user_email} takıma eklendi")
    else:
        print(f"❌ {user_email} takıma eklenemedi")
```

### Hata Yönetimi ile Güvenli Kullanım

```python
def safe_add_user_to_team(client, user_email, team_name, role="Member"):
    """Güvenli kullanıcı ekleme fonksiyonu"""
    try:
        # 1. Kullanıcı kontrolü
        if not client.check_user_exists_in_org(user_email):
            print(f"⚠️ {user_email} organizasyonda yok, davet ediliyor...")
            
            # Organizasyona davet et
            invite_success = client.invite_user_to_organization(
                user_email=user_email,
                license_type="basic"
            )
            
            if not invite_success:
                print(f"❌ {user_email} davet edilemedi")
                return False
            
            # Davet işleminin tamamlanmasını bekle
            print("⏳ Davet işlemi bekleniyor...")
            time.sleep(10)
        
        # 2. Takıma ekle
        success = client.add_user_to_any_group(user_email, team_name, role)
        
        if success:
            print(f"✅ {user_email} başarıyla {team_name} takımına eklendi")
            return True
        else:
            print(f"❌ {user_email} takıma eklenemedi")
            return False
            
    except Exception as e:
        print(f"🚨 Hata: {str(e)}")
        return False

# Kullanım
client = AzureDevOpsRESTClient(
    organization_url="https://dev.azure.com/myorg",
    project_name="MyProject"
)

safe_add_user_to_team(client, "newuser@example.com", "Development Team", "Member")
```

---

## 🎯 En İyi Uygulamalar

### 1. Kimlik Doğrulama
- ✅ Azure CLI kullanın (önerilen)
- ⚠️ PAT token sadece gerekli durumlarda
- 🔐 Token'ları güvenli saklayın

### 2. Performans Optimizasyonu
- ✅ Cache sistemini kullanın
- ✅ Toplu işlemler için batch fonksiyonları
- ⚡ Gereksiz API çağrılarından kaçının

### 3. Hata Yönetimi
- ✅ Her API çağrısını try-catch ile sarın
- ✅ Fallback mekanizmalarını kullanın
- 📝 Detaylı logging yapın

### 4. Güvenlik
- 🔒 HTTPS bağlantı zorunlu
- 🛡️ Minimum yetki prensibi
- 📊 Audit trail tutun

---

## 🔄 Sürüm Geçmişi

### v2.0.0 (Mevcut)
- ✅ Azure CLI tabanlı kimlik doğrulama
- ✅ Gelişmiş cache sistemi
- ✅ Toplu işlem desteği
- ✅ Çoklu fallback mekanizması

### v1.0.0 (Eski)
- PAT token tabanlı sistem
- Temel API işlemleri
- Sınırlı hata yönetimi

---

## 📞 Destek ve Katkı

### Hata Raporlama
Hata bulduğunuzda lütfen şu bilgileri ekleyin:
- Hata mesajı
- Kullanılan parametreler
- Azure DevOps organizasyon yapısı
- İşlem adımları

### Katkı Sağlama
- Fork yapın
- Feature branch oluşturun
- Test yazın
- Pull request gönderin

---

*Bu dokümantasyon Azure DevOps REST Client v2.0.0 için hazırlanmıştır.*
*Son güncelleme: 2025-01-30*
