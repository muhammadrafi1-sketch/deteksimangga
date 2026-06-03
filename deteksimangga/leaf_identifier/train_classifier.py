"""
Training Script untuk Minimum Distance Classifier
Menghitung centroid MATANG dan MENTAH dari dataset, lalu menyimpan ke centroids.json
"""

import sys
import os

# Tambahkan parent directory ke sys.path agar bisa import leaf_identifier
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from leaf_identifier.classifier import train_classifier, save_centroids


def main():
    """
    Main function untuk training classifier
    
    Workflow:
    1. Load semua gambar dari dataset/matang/ dan dataset/mentah/
    2. Ekstrak features [R, G, B, H, S, V] dari setiap gambar
    3. Hitung centroid (mean) untuk setiap kelas
    4. Simpan centroid ke centroids.json
    
    Usage:
        python -m leaf_identifier.train_classifier
        python -m leaf_identifier.train_classifier dataset/
    """
    
    # Default dataset path
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        # Asumsi script dijalankan dari root project
        dataset_path = 'dataset'
    
    # Validasi dataset path
    if not os.path.exists(dataset_path):
        print(f"❌ ERROR: Dataset path tidak ditemukan: {dataset_path}")
        print("\nPastikan struktur folder seperti ini:")
        print("  dataset/")
        print("    ├── matang/")
        print("    │   ├── mangga1.jpg")
        print("    │   ├── mangga2.jpg")
        print("    │   └── ...")
        print("    └── mentah/")
        print("        ├── mangga1.jpg")
        print("        ├── mangga2.jpg")
        print("        └── ...")
        sys.exit(1)
    
    matang_path = os.path.join(dataset_path, 'matang')
    mentah_path = os.path.join(dataset_path, 'mentah')
    
    if not os.path.exists(matang_path):
        print(f"❌ ERROR: Folder 'matang' tidak ditemukan: {matang_path}")
        sys.exit(1)
    
    if not os.path.exists(mentah_path):
        print(f"❌ ERROR: Folder 'mentah' tidak ditemukan: {mentah_path}")
        sys.exit(1)
    
    try:
        # Training: hitung centroid dari dataset
        centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = train_classifier(dataset_path)
        
        # Simpan centroid ke file JSON
        output_path = 'centroids.json'
        save_centroids(centroid_matang, centroid_mentah, distance_threshold, confidence_threshold, output_path)
        
        print("\n✅ TRAINING SELESAI!")
        print(f"Centroid disimpan ke: {output_path}")
        print("\nSekarang Anda bisa:")
        print("  1. Jalankan GUI: python -m leaf_identifier.main")
        print("  2. Jalankan inference: python -m leaf_identifier.inference <path_gambar>")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
