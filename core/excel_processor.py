import pandas as pd
import os

class ExcelProcessor:
    def __init__(self):
        self.required_columns = ['Team Name', 'User Email', 'Role', 'Action']
    
    def read_excel(self, file_path):
        """Excel dosyasını oku ve doğrula"""
        try:
            # Excel dosyasını oku
            df = pd.read_excel(file_path)
            
            # Sütun isimlerini temizle
            df.columns = df.columns.str.strip()
            
            # Gerekli sütunları kontrol et
            missing_columns = []
            for col in self.required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                raise Exception(f"Eksik sütunlar: {', '.join(missing_columns)}")
            
            # Veriyi temizle
            df = df.dropna(subset=['Team Name', 'User Email', 'Action'])
            
            # Email formatını kontrol et
            for index, row in df.iterrows():
                email = str(row['User Email']).strip()
                if '@' not in email:
                    raise Exception(f"Geçersiz email formatı (satır {index + 2}): {email}")
                
                action = str(row['Action']).strip().lower()
                if action not in ['add', 'remove']:
                    raise Exception(f"Geçersiz işlem (satır {index + 2}): {action}. 'Add' veya 'Remove' olmalı")
            
            return df
            
        except Exception as e:
            raise Exception(f"Excel dosyası okuma hatası: {str(e)}")
    
    def create_sample_template(self):
        """Örnek şablon dosyası oluştur"""
        try:
            # Örnek veri
            sample_data = {
                'Team Name': ['Development Team', 'QA Team', 'Development Team', 'DevOps Team'],
                'User Email': ['user1@example.com', 'user2@example.com', 'user3@example.com', 'user4@example.com'],
                'Role': ['Member', 'Admin', 'Contributor', 'Member'],
                'Action': ['Add', 'Add', 'Remove', 'Add']
            }
            
            df = pd.DataFrame(sample_data)
            
            # Excel dosyasına kaydet
            output_file = 'sample_template.xlsx'
            df.to_excel(output_file, index=False)
            
            return output_file
            
        except Exception as e:
            raise Exception(f"Şablon oluşturma hatası: {str(e)}")
    
    def validate_data(self, df):
        """Veri doğrulama"""
        errors = []
        
        for index, row in df.iterrows():
            row_num = index + 2  # Excel'de başlık satırı olduğu için +2
            
            # Team Name kontrolü
            if pd.isna(row['Team Name']) or str(row['Team Name']).strip() == '':
                errors.append(f"Satır {row_num}: Team Name boş olamaz")
            
            # User Email kontrolü
            email = str(row['User Email']).strip()
            if pd.isna(row['User Email']) or email == '':
                errors.append(f"Satır {row_num}: User Email boş olamaz")
            elif '@' not in email:
                errors.append(f"Satır {row_num}: Geçersiz email formatı: {email}")
            
            # Action kontrolü
            action = str(row['Action']).strip().lower()
            if action not in ['add', 'remove']:
                errors.append(f"Satır {row_num}: Geçersiz Action: {action} (Add veya Remove olmalı)")
            
            # Role kontrolü (opsiyonel)
            if not pd.isna(row['Role']):
                role = str(row['Role']).strip()
                valid_roles = ['Member', 'Admin', 'Contributor', 'Reader']
                if role not in valid_roles:
                    errors.append(f"Satır {row_num}: Geçersiz Role: {role} ({', '.join(valid_roles)} olmalı)")
        
        return errors