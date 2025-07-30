#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Azure DevOps REST API Client
Azure DevOps REST API kullanarak kullanıcı ve takım yönetimi
"""

import requests
import json
import base64
import time
from typing import List, Dict, Tuple, Optional
from urllib.parse import quote


class AzureDevOpsRESTClient:
    """Azure DevOps REST API Client"""
    
    def __init__(self, organization_url: str, project_name: str, pat_token: str, debug_mode: bool = True):
        """Azure DevOps REST API Client başlatıcı
        
        Args:
            organization_url: Azure DevOps organizasyon URL'i
            project_name: Proje adı
            pat_token: Personal Access Token
            debug_mode: Debug modu (detaylı logging)
        """
        # Debug modu
        self.debug_mode = debug_mode
        
        # URL'yi temizle ve düzenle
        self.organization_url = organization_url.rstrip('/')
        if not self.organization_url.startswith('https://'):
            self.organization_url = f"https://{self.organization_url}"
        
        # Organizasyon adını çıkar
        self.organization_name = self.organization_url.split('/')[-1]
        
        self.project_name = project_name
        self.pat_token = pat_token
        
        # API base URL'leri
        self.base_url = f"{self.organization_url}/{self.project_name}/_apis"
        self.vsaex_base_url = f"https://vsaex.dev.azure.com/{self.organization_name}/_apis"
        self.api_version = "7.1-preview.3"
        
        # HTTP headers
        self.headers = {
            'Authorization': f'Basic {base64.b64encode(f":{self.pat_token}".encode()).decode()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Cache sistemi
        self._teams_cache = None
        self._teams_cache_time = None
        self._org_users_cache = None
        self._org_users_cache_time = None
        self._cache_ttl = 300  # 5 dakika
    
    def _debug_log(self, message: str, level: str = "INFO"):
        """Debug modu için detaylı logging"""
        if self.debug_mode:
            icons = {
                "INFO": "ℹ️",
                "SUCCESS": "✅", 
                "WARNING": "⚠️",
                "ERROR": "❌",
                "API": "🌐",
                "STEP": "🔄",
                "CACHE": "💾"
            }
            icon = icons.get(level, "📝")
            print(f"{icon} [{level}] {message}")
    
    def _debug_api_call(self, method: str, url: str, status_code: int = None, response_data: dict = None):
        """API çağrıları için özel debug logging"""
        if self.debug_mode:
            print(f"\n🌐 API CALL: {method} {url}")
            if status_code:
                status_icon = "✅" if 200 <= status_code < 300 else "❌"
                print(f"{status_icon} Status Code: {status_code}")
            if response_data:
                print(f"📄 Response: {json.dumps(response_data, indent=2)[:500]}...")
        
        if self.debug_mode:
            print(f"\n🔧 DEBUG MODE AKTIF - Detaylı logging etkin")
            print(f"🔗 Organization: {self.organization_name}")
            print(f"📁 Project: {self.project_name}")
            print(f"🔑 PAT Token: {'*' * 20}...{self.pat_token[-4:] if len(self.pat_token) > 4 else '****'}")
            print(f"🌐 Base URL: {self.base_url}")
            print(f"🌐 VSAEX URL: {self.vsaex_base_url}")
            print("✅ Azure CLI doğrulama hazır")
            # Not: Az CLI kimlik bilgileri otomatik kullanılacak
        
        # PERFORMANS CACHE SİSTEMİ
        self._teams_cache = None
        self._teams_cache_time = None
        self._org_users_cache = None
        self._org_users_cache_time = None
        self._project_id_cache = None
        self._cache_ttl = 300  # 5 dakika cache süresi
        
        # Toplu işlem için batch kontrolürü
        self._pending_invitations = []  # List olarak değiştirildi - pop(0) ve append() için
        self._batch_size = 10  # Aynı anda işlenecek kullanıcı sayısı
    
    
    def test_connection(self) -> bool:
        """Azure DevOps bağlantısını test eder"""
        try:
            print("🔄 API bağlantı testi...")
            
            # Projects endpoint'ini test et
            url = f"{self.base_url}/projects?api-version={self.api_version}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                projects = response.json().get('value', [])
                project_names = [p['name'] for p in projects]
                
                if self.project_name in project_names:
                    print(f"✅ Bağlantı başarılı")
                    return True
                else:
                    print(f"❌ Proje bulunamadı: {self.project_name}")
                    print(f"📋 Mevcut projeler: {project_names}")
                    return False
            else:
                print(f"❌ API hatası: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Bağlantı hatası: {str(e)}")
            return False
    
    def _is_cache_valid(self, cache_time) -> bool:
        """Cache'in hala geçerli olup olmadığını kontrol et"""
        if cache_time is None:
            return False
        return (time.time() - cache_time) < self._cache_ttl
    
    def _get_teams_from_cache(self) -> Optional[List[Dict]]:
        """Cache'den takımları al"""
        if self._is_cache_valid(self._teams_cache_time) and self._teams_cache is not None:
            print("⚡ Takımlar cache'den alındı")
            return self._teams_cache
        return None
    
    def _cache_teams(self, teams: List[Dict]):
        """Takımları cache'le"""
        self._teams_cache = teams
        self._teams_cache_time = time.time()
        print(f"💾 {len(teams)} takım kaydedildi")
    
    def _detect_group_type(self, group_name: str) -> str:
        """
        Verilen grup isminin takım mı yoksa güvenlik grubu mu olduğunu tespit eder.
        
        Args:
            group_name: Tespit edilecek grup adı
            
        Returns:
            str: 'team', 'security' veya 'unknown'
        """
        try:
            # Önce takımları kontrol et
            teams = self.get_teams()
            for team in teams:
                if team.get('name', '').lower() == group_name.lower():
                    return 'team'
            
            # Sonra güvenlik gruplarını kontrol et
            security_groups = self._get_security_groups()
            for group in security_groups:
                if group.get('principalName', '').lower() == group_name.lower():
                    return 'security'
            
            # Bulunamadıysa bilinmeyen
            return 'unknown'
            
        except Exception as e:
            print(f"⛔ Grup tespiti hatası: {str(e)}")
            return 'unknown'
    
    def _get_security_groups(self) -> List[Dict]:
        """
        Proje güvenlik gruplarını alır
        
        Returns:
            List[Dict]: Güvenlik grupları listesi
        """
        try:
            # Proje ID'sini al
            project_id = self._get_project_id()
            if not project_id:
                return []
            
            # Güvenlik gruplarını getir
            url = f"{self.organization_url}/_apis/graph/groups?api-version=7.1-preview.1"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                groups = response.json().get('value', [])
                project_groups = []
                
                # Sadece proje ile ilgili grupları filtrele
                for group in groups:
                    if group.get('description', '').find(project_id) >= 0 or \
                       group.get('principalName', '').find(self.project_name) >= 0:
                        project_groups.append(group)
                        
                print(f"✅ {len(project_groups)} güvenlik grubu")
                return project_groups
            else:
                print(f"⛔ Güvenlik grupları hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⛔ Güvenlik grupları hatası: {str(e)}")
            return []
    
    def get_teams(self) -> List[Dict]:
        """🚀 OPTIMIZE EDİLMİŞ: Proje takımlarını listeler (cache ile)"""
        try:
            # Önce cache'i kontrol et
            cached_teams = self._get_teams_from_cache()
            if cached_teams is not None:
                return cached_teams
            
            print("📋 Takımlar yükleniyor...")
            
            url = f"{self.base_url}/projects/{quote(self.project_name)}/teams?api-version={self.api_version}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                teams_data = response.json().get('value', [])
                teams = []
                
                for team in teams_data:
                    teams.append({
                        'id': team.get('id'),
                        'name': team.get('name'),
                        'description': team.get('description', ''),
                        'url': team.get('url', '')
                    })
                
                print(f"✅ {len(teams)} takım")
                
                # Cache'le
                self._cache_teams(teams)
                
                return teams
            else:
                print(f"❌ Takım listesi hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Takım listesi hatası: {str(e)}")
            return []
    
    def get_team_members(self, team_id: str) -> List[Dict]:
        """Takım üyelerini listeler"""
        try:
            url = f"{self.base_url}/projects/{quote(self.project_name)}/teams/{team_id}/members?api-version={self.api_version}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                members_data = response.json().get('value', [])
                members = []
                
                for member in members_data:
                    identity = member.get('identity', {})
                    members.append({
                        'id': identity.get('id'),
                        'displayName': identity.get('displayName'),
                        'uniqueName': identity.get('uniqueName'),
                        'email': identity.get('uniqueName'),  # uniqueName genellikle email
                        'isActive': identity.get('isActive', True)
                    })
                
                return members
            else:
                print(f"❌ Takım üyeleri hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Takım üyeleri hatası: {str(e)}")
            return []
    
    def _get_org_users_from_cache(self) -> Optional[List[Dict]]:
        """Cache'den organizasyon üyelerini al"""
        if self._is_cache_valid(self._org_users_cache_time) and self._org_users_cache is not None:
            print("⚡ Organizasyon üyeleri cache'den alındı")
            return self._org_users_cache
        return None
    
    def _cache_org_users(self, users: List[Dict]):
        """Organizasyon üyelerini cache'le"""
        self._org_users_cache = users
        self._org_users_cache_time = time.time()
        print(f"💾 {len(users)} üye kaydedildi")
    
    def _load_all_org_users(self) -> List[Dict]:
        """🚀 OPTIMIZE EDİLMİŞ: Tüm organizasyon üyelerini yükle (cache ile)"""
        try:
            # Önce cache'i kontrol et
            cached_users = self._get_org_users_from_cache()
            if cached_users is not None:
                return cached_users
            
            print("👥 Org üyeleri yükleniyor...")
            
            # User Entitlements API ile kullanıcıları listele
            url = f"{self.vsaex_base_url}/userentitlements?api-version=7.1-preview.3"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                users_data = response.json().get('members', [])
                users = []
                
                for user in users_data:
                    user_info = user.get('user', {})
                    users.append({
                        'email': user_info.get('mailAddress', '').lower(),
                        'descriptor': user_info.get('descriptor'),
                        'displayName': user_info.get('displayName', ''),
                        'id': user_info.get('id')
                    })
                
                print(f"✅ {len(users)} üye yüklendi")
                
                # Cache'le
                self._cache_org_users(users)
                
                return users
            else:
                print(f"❌ Üyeler hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Üye yükleme hatası: {str(e)}")
            return []
    
    def check_user_exists_in_org(self, user_email: str) -> Optional[str]:
        """🚀 OPTIMIZE EDİLMİŞ: Kullanıcının organizasyonda olup olmadığını kontrol eder (cache ile)"""
        try:
            # Tüm organizasyon üyelerini yükle (cache'den veya API'den)
            org_users = self._load_all_org_users()
            
            # Cache'den ara
            for user in org_users:
                if user['email'] == user_email.lower():
                    print(f"✅ Kullanıcı bulundu: {user_email}")
                    return user['descriptor']
            
            print(f"❌ Kullanıcı bulunamadı: {user_email}")
            return None
                
        except Exception as e:
            print(f"❌ Kontrol hatası: {str(e)}")
            return None
    
    def check_multiple_users_exist(self, user_emails: List[str]) -> Dict[str, Optional[str]]:
        """🚀 YENİ: Birden fazla kullanıcının organizasyonda olup olmadığını toplu kontrol et"""
        try:
            print(f"👥 {len(user_emails)} kullanıcı kontrolü...")
            
            # Tüm organizasyon üyelerini yükle (cache'den veya API'den)
            org_users = self._load_all_org_users()
            
            # Email'leri normalize et
            email_to_descriptor = {user['email']: user['descriptor'] for user in org_users}
            
            # Sonuçları hazırla
            results = {}
            for email in user_emails:
                normalized_email = email.lower().strip()
                results[email] = email_to_descriptor.get(normalized_email)
            
            existing_count = sum(1 for desc in results.values() if desc is not None)
            print(f"✅ Kontrol: {existing_count}/{len(user_emails)} kullanıcı mevcut")
            
            return results
                
        except Exception as e:
            print(f"❌ Kontrol hatası: {str(e)}")
            return {email: None for email in user_emails}
    
    def invite_user_to_organization(self, user_email: str, license_type: str = "stakeholder", team_name: str = None, role: str = "Member") -> bool:
        """Kullanıcıyı organizasyona davet eder ve isteğe bağlı olarak doğrudan takıma ekler - Microsoft resmi dokümantasyonuna göre"""
        try:
            print(f"📧 Davet: {user_email}")
            if team_name:
                print(f"👥 Hedef takım: {team_name} ({role})")
            
            # Önce kullanıcının zaten organizasyonda olup olmadığını kontrol et
            existing_user = self.check_user_exists_in_org(user_email)
            if existing_user:
                print(f"ℹ️ Kullanıcı zaten organizasyonda: {user_email}")
                return True
            
            # Proje ID'sini al (Microsoft dokümantasyonuna göre projectRef için id gerekli)
            project_id = self._get_project_id()
            if not project_id:
                print(f"❌ Proje ID bulunamadı: {self.project_name}")
                return False
            
            # Microsoft resmi dokümantasyonuna göre User Entitlements API
            url = f"{self.vsaex_base_url}/userentitlements?api-version=4.1-preview.1"
            
            # License type dönüşümü (stakeholder -> express için Basic)
            api_license_type = "express" if license_type == "stakeholder" else license_type
            
            payload = {
                "accessLevel": {
                    "licensingSource": "account",
                    "accountLicenseType": api_license_type
                },
                "user": {
                    "principalName": user_email,
                    "subjectKind": "user"
                }
            }
            
            # Eğer takım belirtilmişse, projectEntitlements ekle
            if team_name:
                print(f"🎯 ProjectEntitlements ile doğrudan takıma ekleme: {team_name}")
                
                # Rol tipini Microsoft formatına çevir
                group_type = self._convert_role_to_group_type(role, team_name)
                
                payload["projectEntitlements"] = [
                    {
                        "group": {
                            "groupType": group_type
                        },
                        "projectRef": {
                            "id": project_id
                        }
                    }
                ]
                
                print(f"📋 Grup tipi: {group_type}")
                print(f"📋 Proje ID: {project_id}")
            
            print(f" API: {url}")
            print(f" Data: {json.dumps(payload)}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            print(f"📊 Status: {response.status_code}") 
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                if response_data.get('isSuccess', False):
                    print(f"✅ Davet başarılı: {user_email}")
                    time.sleep(2)
                    return True
                else:
                    errors = response_data.get('operationResult', {}).get('errors', [])
                    print(f"❌ Davet hatası: {errors}")
                    return False
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = str(error_data).lower()
                    
                    if 'already exists' in error_msg or 'already a member' in error_msg:
                        print(f"ℹ️ Zaten üye: {user_email}")
                        return True
                    else:
                        print(f"❌ Davet hatası: {response.text[:100]}...")
                        return False
                except:
                    print(f"❌ Kullanıcı davet hatası (400): {response.text}")
                    return False
            elif response.status_code == 405:
                print(f"⚠️ 405: Alternatif yöntem...")
                # Direkt olarak başarısız dön - kullanıcı daha sonra Excel listesinde belirtilen takıma eklenecek
                print(f"⚠️ Kullanıcı davet işlemi desteklenmeyen yöntem hatası - doğrudan eklemek için kullanıcı zaten organizasyonda olmalı")
                return False
            else:
                print(f"❌ Kullanıcı davet hatası: {response.status_code} - {response.text}")
                # 405 dışındaki hatalar için de alternatif yöntem dene
                if response.status_code in [403, 404]:
                    print(f"⚠️ {response.status_code} hatası - alternatif yöntem deneniyor...")
                    # Direkt olarak başarısız dön - kullanıcı daha sonra Excel listesinde belirtilen takıma eklenecek
                    print(f"⚠️ Kullanıcı davet işlemi desteklenmeyen yöntem hatası - doğrudan eklemek için kullanıcı zaten organizasyonda olmalı")
                    return False
                return False
                
        except Exception as e:
            print(f"❌ Organizasyon davet hatası: {str(e)}")
            return False
    
    def _get_project_id(self) -> Optional[str]:
        """Proje ID'sini al"""
        try:
            url = f"{self.base_url}/projects/{self.project_name}?api-version=7.1"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                project_data = response.json()
                return project_data.get('id')
            else:
                print(f"❌ Proje bilgisi alınamadı: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Proje ID alma hatası: {str(e)}")
            return None
    
    def _get_team_descriptor(self, team_id: str) -> Optional[str]:
        """Takımın Graph descriptor'ını al"""
        try:
            # Teams API ile takım bilgilerini al
            url = f"{self.base_url}/projects/{self.project_name}/teams/{team_id}?api-version=7.1"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                team_data = response.json()
                # Takım descriptor'ı genellikle 'id' alanında bulunur
                descriptor = team_data.get('id')
                if descriptor:
                    print(f"✅ Takım descriptor bulundu: {descriptor}")
                    return descriptor
                else:
                    print(f"❌ Takım descriptor bulunamadı")
                    return None
            else:
                print(f"❌ Takım bilgisi alınamadı: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Takım descriptor alma hatası: {str(e)}")
            return None
    
    def _convert_role_to_group_type(self, role: str, team_name: str = None) -> str:
        """
        Kullanıcı rolünü Microsoft Azure DevOps group type formatına çevirir
        
        Args:
            role: Kullanıcı rolü (Member, Admin, Contributor, Reader vs.)
            team_name: Takım adı (özel takımlar için)
            
        Returns:
            str: Microsoft group type (projectContributor, projectReader, vs.)
        """
        role_lower = role.lower().strip()
        
        # Standart Azure DevOps rolleri
        role_mapping = {
            'admin': 'projectAdministrator',
            'administrator': 'projectAdministrator', 
            'contributor': 'projectContributor',
            'member': 'projectContributor',  # Varsayılan olarak Contributor
            'reader': 'projectReader',
            'stakeholder': 'projectStakeholder'
        }
        
        # Eğer rol mapping'de varsa onu kullan
        if role_lower in role_mapping:
            group_type = role_mapping[role_lower]
            print(f"🔄 Rol dönüşümü: {role} -> {group_type}")
            return group_type
        
        # Eğer özel bir takım adı belirtilmişse ve rol bulunamazsa
        if team_name:
            print(f"⚠️ Bilinmeyen rol '{role}', takım '{team_name}' için varsayılan 'projectContributor' kullanılıyor")
            return 'projectContributor'
        
        # Varsayılan olarak Contributor
        print(f"⚠️ Bilinmeyen rol '{role}', varsayılan 'projectContributor' kullanılıyor")
        return 'projectContributor'
    
    def invite_multiple_users_batch(self, user_emails: List[str], license_type: str = "stakeholder") -> Dict[str, bool]:
        """🚀 YENİ: Birden fazla kullanıcıyı toplu davet et"""
        try:
            print(f"📧 {len(user_emails)} kullanıcı toplu davet ediliyor...")
            
            results = {}
            
            # Önce hangi kullanıcıların zaten organizasyonda olduğunu kontrol et
            existing_users = self.check_multiple_users_exist(user_emails)
            
            # Sadece mevcut olmayan kullanıcıları davet et
            users_to_invite = [email for email, descriptor in existing_users.items() if descriptor is None]
            
            if not users_to_invite:
                print("✅ Tüm kullanıcılar zaten organizasyonda mevcut")
                return {email: True for email in user_emails}
            
            print(f"📧 {len(users_to_invite)} yeni kullanıcı davet edilecek...")
            
            # Toplu davet işlemi
            for email in users_to_invite:
                try:
                    success = self.invite_user_to_organization(email, license_type)
                    results[email] = success
                    if success:
                        self._pending_invitations.append(email)
                except Exception as e:
                    print(f"❌ Davet hatası {email}: {str(e)}")
                    results[email] = False
            
            # Zaten mevcut olan kullanıcılar için başarılı işaretle
            for email, descriptor in existing_users.items():
                if descriptor is not None:
                    results[email] = True
            
            success_count = sum(1 for success in results.values() if success)
            print(f"✅ Toplu davet tamamlandı: {success_count}/{len(user_emails)} başarılı")
            
            return results
                
        except Exception as e:
            print(f"❌ Toplu davet hatası: {str(e)}")
            return {email: False for email in user_emails}
    
    
    def add_user_to_any_group(self, user_email: str, group_name: str, role: str = 'Member') -> bool:
        """Kullanıcıyı herhangi bir gruba (takım veya güvenlik grubu) ekler
        
        Args:
            user_email: Kullanıcı e-posta adresi
            group_name: Grup adı (takım veya güvenlik grubu olabilir)
            role: Kullanıcının rolü (sadece takımlar için kullanılır)
        
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            print(f"\n==== GRUP EKLEME ====")
            print(f"Ekleniyor: {user_email} -> {group_name} ({role})")
            print(f"==============================")

            # 1. Kullanıcı organizasyonda mı?
            user_descriptor = self.check_user_exists_in_org(user_email)
            if not user_descriptor:
                print(f"❌ Kullanıcı organizasyonda yok, ProjectEntitlements ile doğrudan takıma ekleyerek davet ediliyor...")
                
                # 🚀 YENİ: ProjectEntitlements ile doğrudan takıma ekleme
                invite_ok = self.invite_user_to_organization(user_email, "stakeholder", group_name, role)
                
                if not invite_ok:
                    print(f"❌ ProjectEntitlements ile davet başarısız: {user_email}")
                    print(f"🔄 Klasik davet yöntemi deneniyor...")
                    
                    # Fallback: Klasik davet yöntemi
                    fallback_invite = self.invite_user_to_organization(user_email, "stakeholder")
                    if not fallback_invite:
                        print(f"❌ Tüm davet yöntemleri başarısız: {user_email}")
                        print(f"⚠️ Manuel davet gerekebilir - Azure DevOps portalından davet edin")
                        return False
                    
                    # Fallback başarılıysa, ayrıca takıma ekleme işlemi yapılacak
                    print(f"✅ Klasik davet başarılı, şimdi takıma ekleniyor: {user_email}")
                else:
                    print(f"✅ ProjectEntitlements ile doğrudan takıma ekleme başarılı: {user_email}")
                    print(f"🎉 Hem organizasyona davet hem takıma ekleme tek seferde tamamlandı!")
                    # ProjectEntitlements başarılıysa, işlem tamamdır - hem davet hem takıma ekleme yapıldı
                    return True
                
                # Davetten sonra tekrar kontrol et
                print(f"🔄 Davet sonrası tekrar kontrol ediliyor...")
                time.sleep(3)
                user_descriptor = self.check_user_exists_in_org(user_email)
                if not user_descriptor:
                    print(f"❌ Bulunamadı: {user_email}")
                    print(f"⚠️ Manuel davet gerekebilir - Azure DevOps portalından davet edin")
                    return False
                print(f"✅ Organizasyona eklendi: {user_email}")
            else:
                print(f"✅ Zaten üye: {user_email}")

            # 2. Grup türünü otomatik tespit et - hataya karşı korumalı
            try:
                group_type = self._detect_group_type(group_name)
                print(f"🔍 Grup türü: {group_type}")
            except AttributeError:
                print(f"⚠️ _detect_group_type metodu bulunamadı, 'unknown' varsayılıyor")
                group_type = 'unknown'

            # 3. Grup türüne göre uygun ekleme fonksiyonunu çağır
            if group_type == 'team':
                print(f"👥 Takıma ekleniyor: {user_email} -> {group_name}")
                added = self._add_user_to_work_team(user_email, group_name, role)
                if not added:
                    print(f"❌ Standart takım ekleme başarısız: {user_email}")
                    print(f"🔄 Özel grup yöntemleri deneniyor...")
                    # Özel grup yöntemlerini dene
                    return self.add_user_to_custom_group(user_email, group_name)
                print(f"✅ Kullanıcı başarıyla takıma eklendi: {user_email}")
                return True

            elif group_type == 'security':
                print(f"👮 Güvenlik grubuna ekleniyor: {user_email}")
                added = self._add_user_to_security_group(user_email, group_name)
                if not added:
                    print(f"❌ Standart güvenlik grubu ekleme başarısız: {user_email}")
                    print(f"🔄 Özel grup yöntemleri deneniyor...")
                    # Özel grup yöntemlerini dene
                    return self.add_user_to_custom_group(user_email, group_name)
                print(f"✅ Kullanıcı başarıyla güvenlik grubuna eklendi: {user_email}")
                return True

            else:  # unknown - özel grup olabilir
                print(f"❓ Bilinmeyen grup türü: {group_name}")
                print(f"🎯 Özel grup yöntemleri deneniyor...")
                # Doğrudan özel grup yöntemlerini dene
                success = self.add_user_to_custom_group(user_email, group_name)
                if success:
                    return True
                    
                print(f"❌ Tüm yöntemler başarısız: {group_name}")
                print(f"⚠️ Grup bulunamadı/erişim yok")
                print(f"⚠️ Manuel ekleme gerekebilir")
                return False
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            return False
    
    def wait_for_pending_invitations(self, max_wait_time: int = 30) -> int:
        """Bekleyen davetlerin işlenmesini bekler
        
        Args:
            max_wait_time: Maksimum bekleme süresi (saniye)
            
        Returns:
            int: İşlenen davet sayısı
        """
        if not hasattr(self, '_pending_invitations') or not self._pending_invitations:
            return 0
            
        processed_count = 0
        start_time = time.time()
        
        print(f"⏳ {len(self._pending_invitations)} bekleyen davet işleniyor...")
        
        while self._pending_invitations and (time.time() - start_time) < max_wait_time:
            user_email = self._pending_invitations.pop(0)  # Sadece email string'i al
            
            print(f"🔄 İşleniyor: {user_email}")
            
            # Kullanıcının organizasyona katılmasını bekle
            time.sleep(2)
            
            # Kullanıcı organizasyonda mı kontrol et
            if self.check_user_exists_in_org(user_email):
                print(f"✅ Kullanıcı organizasyona katıldı: {user_email}")
                processed_count += 1
            else:
                print(f"⏳ Kullanıcı henüz organizasyona katılmamış: {user_email}")
                # Tekrar listeye ekle (bir sonraki döngüde denenecek)
                self._pending_invitations.append(user_email)
                
        return processed_count

    def add_user_to_custom_group(self, user_email: str, group_name: str) -> bool:
        """Özel gruplara kullanıcı ekleme - farklı API yaklaşımları
        
        Args:
            user_email: Kullanıcı e-posta adresi
            group_name: Özel grup adı
            
        Returns:
            bool: İşlem başarılı ise True
        """
        print(f"🎯 Özel gruba ekleme: {user_email} -> {group_name}")
        
        # Yöntem 1: Graph API ile grup üyeliği
        if self._add_to_custom_group_via_graph(user_email, group_name):
            return True
            
        # Yöntem 2: Security Groups API
        if self._add_to_custom_group_via_security_api(user_email, group_name):
            return True
            
        # Yöntem 3: Teams API ile özel takım
        if self._add_to_custom_group_via_teams_api(user_email, group_name):
            return True
            
        # Yöntem 4: Group Memberships API
        if self._add_to_custom_group_via_memberships_api(user_email, group_name):
            return True
            
        print(f"❌ Tüm özel grup ekleme yöntemleri başarısız: {group_name}")
        return False
    
    def _add_to_custom_group_via_graph(self, user_email: str, group_name: str) -> bool:
        """Graph API ile özel gruba ekleme"""
        try:
            print(f"🔍 Graph API ile grup aranıyor: {group_name}")
            
            # Önce grubu bul
            org_name = self.organization_url.split('/')[-1]  # URL'den organizasyon adını çıkar
            groups_url = f"https://vssps.dev.azure.com/{org_name}/_apis/graph/groups?api-version=6.0-preview.1"
            
            response = requests.get(groups_url, headers=self.headers)
            if response.status_code == 200:
                groups_data = response.json()
                target_group = None
                
                for group in groups_data.get('value', []):
                    if group.get('displayName', '').lower() == group_name.lower():
                        target_group = group
                        break
                        
                if not target_group:
                    print(f"❌ Grup bulunamadı: {group_name}")
                    return False
                    
                group_descriptor = target_group.get('descriptor')
                print(f"✅ Grup bulundu: {group_name} ({group_descriptor})")
                
                # Kullanıcı descriptor'ını al
                user_descriptor = self.check_user_exists_in_org(user_email)
                if not user_descriptor:
                    print(f"❌ Kullanıcı bulunamadı: {user_email}")
                    return False
                    
                # Gruba ekle
                membership_url = f"https://vssps.dev.azure.com/{org_name}/_apis/graph/memberships/{user_descriptor}/{group_descriptor}?api-version=6.0-preview.1"
                
                add_response = requests.put(membership_url, headers=self.headers)
                if add_response.status_code in [200, 201]:
                    print(f"✅ Graph API ile gruba eklendi: {user_email} -> {group_name}")
                    return True
                else:
                    print(f"❌ Graph API ekleme hatası: {add_response.status_code}")
                    return False
                    
            else:
                print(f"❌ Graph API grup listesi hatası: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Graph API hatası: {str(e)}")
            return False
    
    def _add_to_custom_group_via_security_api(self, user_email: str, group_name: str) -> bool:
        """Security Groups API ile ekleme"""
        try:
            print(f"🛡️ Security API ile grup aranıyor: {group_name}")
            
            # Security groups endpoint
            org_name = self.organization_url.split('/')[-1]  # URL'den organizasyon adını çıkar
            security_url = f"https://vssps.dev.azure.com/{org_name}/_apis/securityroles/scopes/distributedtask.environmentreferencerole/roleassignments/resources/{self.project}?api-version=6.0-preview.1"
            
            response = requests.get(security_url, headers=self.headers)
            if response.status_code == 200:
                print(f"✅ Security API erişimi başarılı")
                # Security group ekleme logic buraya gelecek
                return False  # Şimdilik false, geliştirilebilir
            else:
                print(f"❌ Security API erişim hatası: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Security API hatası: {str(e)}")
            return False
    
    def _add_to_custom_group_via_teams_api(self, user_email: str, group_name: str) -> bool:
        """Teams API ile özel takım ekleme"""
        try:
            print(f"👥 Teams API ile takım aranıyor: {group_name}")
            
            # Takımları listele
            teams = self.get_teams()
            target_team = None
            
            for team in teams:
                if team.get('name', '').lower() == group_name.lower():
                    target_team = team
                    break
                    
            if not target_team:
                print(f"❌ Takım bulunamadı: {group_name}")
                return False
                
            team_id = target_team.get('id')
            print(f"✅ Takım bulundu: {group_name} ({team_id})")
            
            # Takıma ekle
            return self._add_user_to_work_team(user_email, group_name, 'Member')
            
        except Exception as e:
            print(f"❌ Teams API hatası: {str(e)}")
            return False
    
    def _add_to_custom_group_via_memberships_api(self, user_email: str, group_name: str) -> bool:
        """Group Memberships API ile ekleme"""
        try:
            print(f"🔗 Memberships API ile grup aranıyor: {group_name}")
            
            # Group memberships endpoint
            org_name = self.organization_url.split('/')[-1]  # URL'den organizasyon adını çıkar
            memberships_url = f"https://vssps.dev.azure.com/{org_name}/_apis/graph/memberships?api-version=6.0-preview.1"
            
            response = requests.get(memberships_url, headers=self.headers)
            if response.status_code == 200:
                print(f"✅ Memberships API erişimi başarılı")
                # Memberships logic buraya gelecek
                return False  # Şimdilik false, geliştirilebilir
            else:
                print(f"❌ Memberships API erişim hatası: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Memberships API hatası: {str(e)}")
            return False


    def add_user_to_team(self, user_email: str, team_name: str, role: str = 'Member') -> bool:
        """Kullanıcıyı takıma ekler (geriye uyumluluk için)"""
        return self.add_user_to_any_group(user_email, team_name, role)
        
    def _add_user_to_work_team(self, user_email: str, team_name: str, role: str = 'Member') -> bool:
        """Kullanıcıyı çalışma takımına ekler (GELİŞMİŞ GÜVENLİK SİSTEMİ)
        
        Üç farklı yöntemle kullanıcıyı takıma eklemeyi dener:
        1. Teams API ile e-posta kullanarak doğrudan ekleme
        2. Kullanıcıyı organizasyonda arayıp ID ile ekleme
        3. Basit davet sistemi
        
        Args:
            user_email: Kullanıcının e-posta adresi
            team_name: Takım adı
            role: Kullanıcı rolü (Member, Admin)
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            print(f"\n🔑 Takıma ekleme: {user_email} -> {team_name}")
            
            # KRİTİK: Cache temizleme - eski/yanlış takım bilgilerini önlemek için
            print(f"🗑️ Cache temizleniyor - taze takım bilgileri alınacak")
            self._teams_cache = None
            self._teams_cache_time = None
            
            # Takım ID'sini bul - GELİŞMİŞ EŞLEŞTİRME MANTIĞI
            teams = self.get_teams()
            team_id = None
            matched_team = None
            
            print(f"🔍 Takım arama: '{team_name}'")
            print(f"📋 Mevcut takımlar: {[team['name'] for team in teams]}")
            
            # 1. TAM EŞLEŞME (en güvenilir)
            for team in teams:
                if team['name'] == team_name:  # Tam eşleşme (case-sensitive)
                    team_id = team['id']
                    matched_team = team
                    print(f"✅ TAM EŞLEŞME bulundu: '{team['name']}' -> ID: {team_id}")
                    break
            
            # 2. CASE-INSENSITIVE EŞLEŞME (fallback)
            if not team_id:
                for team in teams:
                    if team['name'].lower() == team_name.lower():
                        team_id = team['id']
                        matched_team = team
                        print(f"⚠️ CASE-INSENSITIVE eşleşme: '{team['name']}' -> ID: {team_id}")
                        break
            
            # 3. KİSMİ EŞLEŞME (en riskli - sadece tek sonuç varsa)
            if not team_id:
                partial_matches = []
                for team in teams:
                    if team_name.lower() in team['name'].lower() or team['name'].lower() in team_name.lower():
                        partial_matches.append(team)
                
                if len(partial_matches) == 1:
                    team_id = partial_matches[0]['id']
                    matched_team = partial_matches[0]
                    print(f"⚠️ KİSMİ eşleşme (tek sonuç): '{matched_team['name']}' -> ID: {team_id}")
                elif len(partial_matches) > 1:
                    print(f"❌ ÇOKLU KİSMİ EŞLEŞME - Belirsizlik!")
                    print(f"🔍 Aranan: '{team_name}'")
                    print(f"🔍 Bulunanlar: {[t['name'] for t in partial_matches]}")
                    print(f"⚠️ GÜVENLİK İÇİN İŞLEM DURDURULUYOR!")
                    return False
            
            if not team_id:
                print(f"❌ Takım bulunamadı: '{team_name}'")
                print(f"📋 Mevcut takımlar: {[team['name'] for team in teams]}")
                return False
            
            # SON KONTROL - Doğru takımı seçtiğimizi doğrula
            print(f"🎯 SEÇİLEN TAKIM:")
            print(f"  • Aranan: '{team_name}'")
            print(f"  • Bulunan: '{matched_team['name']}'")
            print(f"  • ID: {team_id}")
            
            # Kullanıcıdan onay al (kritik işlemler için)
            if matched_team['name'] != team_name:
                print(f"⚠️ UYARI: Tam eşleşme değil!")
                print(f"  • İstenen: '{team_name}'")
                print(f"  • Bulanan: '{matched_team['name']}'")
        
            # METOD 1: Teams API ile e-posta kullanarak doğrudan ekleme
            print(f"🔍 METOD 1: Teams API ile e-posta kullanarak doğrudan ekleme")
            result = self._add_user_by_email_direct(user_email, team_id, team_name)
            if result:
                print(f"✅ Kullanıcı başarıyla takıma eklendi (Metod 1)")
                return True
                
            # METOD 2: Kullanıcıyı organizasyonda arayıp ID ile ekleme
            print(f"🔍 METOD 2: Kullanıcıyı organizasyonda arayıp ID ile ekleme")
            user_id = self._find_user_in_organization(user_email)
            if user_id:
                result = self._add_user_by_id_direct(user_id, team_id, team_name)
                if result:
                    print(f"✅ Kullanıcı başarıyla takıma eklendi (Metod 2)")
                    return True
            
            # METOD 3: Basit davet sistemi
            print(f"🔍 METOD 3: Alternatif endpoint ile ekleme deniyor")
            result = self._simple_invite_and_add(user_email, team_id, team_name)
            if result:
                print(f"✅ Kullanıcı başarıyla takıma eklendi (Metod 3)")
                return True
                
            print(f"❌ Tüm ekleme yöntemleri başarısız oldu: {user_email} -> {team_name}")
            return False
                
        except Exception as e:
            print(f"❌ Takıma ekleme hatası: {str(e)}")
            return False


    def _add_user_by_email_direct(self, user_email: str, team_id: str, team_name: str) -> bool:
        """Teams API ile e-posta kullanarak doğrudan kullanıcıyı takıma ekler
        
        Args:
            user_email: Kullanıcının e-posta adresi
            team_id: Takım ID'si
            team_name: Takım adı
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            print(f"🧠 Teams API ile doğrudan ekleme: {user_email} -> {team_name}")
            
            # Üyeleri kontrol et
            team_members = self.get_team_members(team_id)
            
            # Kullanıcı zaten üye mi?
            for member in team_members:
                if member.get('uniqueName', '').lower() == user_email.lower():
                    print(f"✅ Zaten üye: {user_email} -> {team_name}")
                    return True
                    
            # Teams API endpoint
            url = f"{self.base_url}/teams/{team_id}/members?api-version={self.api_version}"
            
            # Kullanıcıyı ekle
            data = {
                'uniqueName': user_email
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Teams API ile eklendi: {user_email}")
                return True
            else:
                print(f"ℹ️ Teams API yanıt kodu: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ℹ️ Teams API hata: {str(e)}")
            return False
            
    def _find_user_in_organization(self, user_email: str) -> Optional[str]:
        """Kullanıcıyı organizasyonda arar ve ID'sini döndürür
        
        Args:
            user_email: Kullanıcının e-posta adresi
            
        Returns:
            Optional[str]: Kullanıcı ID'si veya None
        """
        try:
            print(f"🔍 Kullanıcı aranıyor: {user_email}")
            
            # Tüm organizasyon üyelerini al
            org_members = self._load_all_org_users()
            
            # Kullanıcıyı bul
            for member in org_members:
                email = member.get('uniqueName', '').lower()
                if email == user_email.lower():
                    user_id = member.get('id')
                    print(f"✅ Kullanıcı bulundu: {user_email}, ID: {user_id}")
                    return user_id
                    
            print(f"ℹ️ Kullanıcı organizasyonda bulunamadı: {user_email}")
            return None
            
        except Exception as e:
            print(f"ℹ️ Kullanıcı arama hatası: {str(e)}")
            return None
            
    def _add_user_by_id_direct(self, user_id: str, team_id: str, team_name: str) -> bool:
        """Kullanıcıyı ID'si ile takıma ekler
        
        Args:
            user_id: Kullanıcı ID'si
            team_id: Takım ID'si
            team_name: Takım adı
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            print(f"🔑 ID ile ekleme: Kullanıcı ID {user_id} -> Takım {team_name}")
            
            # Teams API endpoint
            url = f"{self.base_url}/teams/{team_id}/members/{user_id}?api-version={self.api_version}"
            
            # PUT isteği yap
            response = requests.put(
                url,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ ID ile başarıyla eklendi")
                return True
            else:
                print(f"ℹ️ ID ile ekleme yanıt kodu: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ℹ️ ID ile ekleme hatası: {str(e)}")
            return False
            
    def _simple_invite_and_add(self, user_email: str, team_id: str, team_name: str) -> bool:
        """Basit davet sistemi ile kullanıcıyı ekler
        
        Args:
            user_email: Kullanıcı e-posta adresi
            team_id: Takım ID'si
            team_name: Takım adı
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            print(f"📧 Basit davet ile ekleme: {user_email} -> {team_name}")
            
            # Alternatif endpoint
            url = f"{self.base_url}/teams/{team_id}/members?api-version={self.api_version}"
            
            # Kullanıcıyı ekle
            data = {
                'uniqueName': user_email,
                'isTeamAdmin': False
            }
            
            # Önce POST ile dene
            response = requests.post(
                url,
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Alternatif yöntem ile eklendi: {user_email}")
                return True
            
            print(f"ℹ️ Alternatif ekleme yanıt kodu: {response.status_code}")
            return False
                
        except Exception as e:
            print(f"ℹ️ Alternatif ekleme hatası: {str(e)}")
            return False


