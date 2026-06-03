"""
Main Entry Point
Aplikasi Desktop untuk Deteksi Kematangan Mangga
menggunakan K-Means clustering dan ekstraksi fitur warna RGB/HSV
"""

import sys
import os

# Add parent directory to path for package imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leaf_identifier.gui import create_gui


def main():
    """
    Fungsi utama untuk menjalankan aplikasi
    """
    print("=" * 50)
    print("Aplikasi Deteksi Kematangan Mangga")
    print("Pengolahan Citra Digital - K-Means Clustering")
    print("=" * 50)
    print("\nMemulai aplikasi...")
    
    # Jalankan GUI
    create_gui()
    
    print("\nAplikasi ditutup.")


if __name__ == "__main__":
    main()
