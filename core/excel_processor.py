import os
import pandas as pd

class ExcelProcessor:
    def __init__(self):
        # Basitleştirilmiş şablon - sadece gerekli kolonlar
        self.required_columns = ['User Email', 'Action']
        # İsteğe bağlı kolonlar
        self.optional_columns = ['Team Name', 'License Type']
        # Azure DevOps REST API desteklenen license türleri
        self.valid_license_types = ['stakeholder', 'express', 'advanced', 'earlyAdopter']
        # Stakeholder = Ücretsiz temel erişim
        # Express = Basic license (Visual Studio Community)
        # Advanced = Visual Studio Professional/Enterprise
        # EarlyAdopter = Test Features
    
    def read_excel(self, file_path):
        """Excel dosyasını oku ve doğrula - PyQt5 GUI uyumlu format"""
        try:
            print(f"📂 Excel dosyası okunuyor: {file_path}")
            
            # Excel dosyasını oku
            df = pd.read_excel(file_path)
            print(f"📊 {len(df)} satır okundu")
            
            # Sütun isimlerini temizle
            df.columns = df.columns.str.strip()
            print(f"📋 Sütunlar: {list(df.columns)}")
            
            # Gerekli sütunları kontrol et
            missing_columns = []
            for col in self.required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                raise Exception(f"Eksik sütunlar: {', '.join(missing_columns)}. Mevcut sütunlar: {list(df.columns)}")
            
            # Veriyi temizle - sadece gerekli kolonlar
            df = df.dropna(subset=['User Email', 'Action'])
            print(f"🧹 Temizleme sonrası: {len(df)} satır")
            
            # Email formatını kontrol et
            for index, row in df.iterrows():
                email = str(row['User Email']).strip()
                if '@' not in email:
                    raise Exception(f"Geçersiz email formatı (satır {index + 2}): {email}")
                
                action = str(row['Action']).strip().lower()
                if action not in ['add', 'remove']:
                    raise Exception(f"Geçersiz işlem (satır {index + 2}): {action}. 'Add' veya 'Remove' olmalı")
            
            # PyQt5 GUI için uygun formata çevir
            users = []
            for index, row in df.iterrows():
                user_data = {
                    'User Email': str(row['User Email']).strip(),
                    'Action': str(row['Action']).strip(),
                    'Team Name': str(row.get('Team Name', '')).strip() if 'Team Name' in df.columns else '',
                    'License Type': str(row.get('License Type', 'stakeholder')).strip() if 'License Type' in df.columns else 'stakeholder'
                }
                users.append(user_data)
                team_info = f" -> {user_data['Team Name']}" if user_data['Team Name'] else ""
                print(f"✅ Kullanıcı {index+1}: {user_data['User Email']}{team_info} ({user_data['Action']}) [License: {user_data['License Type']}]")
            
            result = {
                'users': users,
                'total_count': len(users)
            }
            
            print(f"✅ Excel okuma başarılı: {len(users)} kullanıcı bulundu")
            return result
            
        except Exception as e:
            error_msg = f"Excel dosyası okuma hatası: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def create_sample_template(self, output_path=None):
        """Örnek şablon oluştur"""
        try:
            if not output_path:
                # Kullanıcının masaüstüne kaydet
                desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                output_path = os.path.join(desktop_path, 'azure_devops_template.xlsx')
            
            print(f"Şablon oluşturuluyor: {output_path}")
            
            # Basitleştirilmiş örnek veri - Azure DevOps REST API uyumlu
            data = {
                'User Email': [
                    'user1@company.com',
                    'user2@company.com', 
                    'user3@company.com',
                    'user4@company.com',
                    'user5@company.com'
                ],
                'Action': [
                    'add',
                    'add',
                    'add', 
                    'add',
                    'remove'
                ],
                'Team Name': [
                    'Development Team',
                    'Marketing Team',
                    'Finance Team',
                    'HR Team',
                    'Development Team'
                ],
                'License Type': [
                    'stakeholder',
                    'express',
                    'stakeholder',
                    'express',
                    'stakeholder'
                ]
            }
            
            print("DataFrame oluşturuluyor...")
            df = pd.DataFrame(data)
            
            print("Excel dosyası yazılıyor...")
            # Dizin yoksa oluştur
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            try:
                # Excel yazıcısını oluştur
                writer = pd.ExcelWriter(output_path, engine='openpyxl')
                
                # DataFrame'i Excel'e yaz
                df.to_excel(writer, index=False, sheet_name='Users')
                
                # Sütun genişliklerini ayarla
                worksheet = writer.sheets['Users']
                for i, col in enumerate(df.columns):
                    max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + i)].width = max_length
                
                # Başlık formatını ayarla
                from openpyxl.styles import Font, PatternFill, Alignment
                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                    cell.alignment = Alignment(horizontal='center')
                
                # Kaydet ve kapat
                writer.close()
                print(f"Excel dosyası başarıyla oluşturuldu: {output_path}")
            except Exception as excel_error:
                print(f"Excel yazma hatası: {excel_error}")
                # Alternatif yöntem dene
                df.to_excel(output_path, index=False)
                print(f"Excel dosyası alternatif yöntemle oluşturuldu: {output_path}")
            
            return output_path
        except Exception as e:
            import traceback
            print(f"Şablon oluşturma hatası: {e}")
            print(traceback.format_exc())
            return None
    
    def validate_data(self, df):
        """Veri doğrulama"""
        errors = []
        
        # Tüm gerekli sütunların var olduğunu kontrol et
        for col in self.required_columns:
            if col not in df.columns:
                errors.append(f"Eksik sütun: {col}")
                return errors
        
        print(f"Excel doğrulama: {len(df)} satır kontrol ediliyor")
        
        for index, row in df.iterrows():
            row_num = index + 2  # Excel'de başlık satırı olduğu için +2
            
            # Team Name kontrolü
            team_name = str(row.get('Team Name', '')).strip()
            if pd.isna(row.get('Team Name')) or team_name == '':
                errors.append(f"Satır {row_num}: Team Name boş olamaz")
            else:
                print(f"Satır {row_num}: Team Name = '{team_name}'")
            
            # User Email kontrolü
            email = str(row.get('User Email', '')).strip()
            if pd.isna(row.get('User Email')) or email == '':
                errors.append(f"Satır {row_num}: User Email boş olamaz")
            elif '@' not in email:
                errors.append(f"Satır {row_num}: Geçersiz email formatı: {email}")
            else:
                print(f"Satır {row_num}: User Email = '{email}'")
            
            # Action kontrolü
            action = str(row.get('Action', '')).strip().lower()
            if pd.isna(row.get('Action')) or action == '':
                errors.append(f"Satır {row_num}: Action boş olamaz")
            elif action not in ['add', 'remove']:
                errors.append(f"Satır {row_num}: Geçersiz Action değeri: {action}. 'add' veya 'remove' olmalı")
            else:
                print(f"Satır {row_num}: Action = '{action}'")
            
            # Role kontrolü (sadece Action=add için gerekli)
            if action == 'add':
                role = str(row.get('Role', 'Member')).strip()
                if pd.isna(row.get('Role')) or role == '':
                    print(f"Satır {row_num}: Role belirtilmemiş, varsayılan 'Member' kullanılacak")
                else:
                    print(f"Satır {row_num}: Role = '{role}'")
                    valid_roles = ['Member', 'Admin', 'Contributor', 'Reader']
                    if role not in valid_roles:
                        errors.append(f"Satır {row_num}: Geçersiz Role: {role} ({', '.join(valid_roles)} olmalı)")
        
        if errors:
            print(f"Excel doğrulama: {len(errors)} hata bulundu")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Excel doğrulama: Tüm veriler geçerli")
            
        return errors