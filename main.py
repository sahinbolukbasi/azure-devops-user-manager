#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AZURE DEVOPS KULLANICI EKLEME ARACI - PyQt5 SÜRÜM
Invite özelliği ile gelişmiş kullanıcı ekleme sistemi
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Uyarıları bastır
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['TK_SILENCE_DEPRECATION'] = '1'
import warnings
warnings.filterwarnings("ignore")

# Path ayarları
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# GUI modülünü import et
from gui.main_window import MainWindow

def main():
    """Ana uygulama fonksiyonu"""
    # PyQt5 uygulamasını oluştur
    app = QApplication(sys.argv)
    app.setApplicationName("Azure DevOps Kullanıcı Ekleme Aracı")
    app.setStyle('Fusion')
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.show()
    
    # Uygulama döngüsünü başlat
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())