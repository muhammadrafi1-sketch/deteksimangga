"""
Script 1: Feature Extraction
Script untuk ekstraksi fitur RGB dan HSV dari dataset mangga (matang/mentah)
Menampilkan summary table di terminal dengan kolom: Filename, R, G, B, H, S, V
"""

import os
import cv2
import numpy as np
from .image_processor import create_kmeans_mask, resize_image, extract_rgb_features, extract_hsv_features


def extract_features_from_dataset(dataset_path):
    """
    Ekstraksi fitur dari semua gambar dalam dataset
    
    Parameters:
    -----------
    dataset_path : str
        Path ke folder dataset (contoh: 'dataset/matang' atau 'dataset/mentah')
    
    Returns:
    --------
    list : List of dictionaries berisi fitur setiap gambar
    """
    features_list = []
    
    # Cek apakah folder dataset ada
    if not os.path.exists(dataset_path):
        print(f"❌ Folder {dataset_path} tidak ditemukan!")
        return features_list
    
    # Ambil semua file gambar (jpg, jpeg, png)
    image_files = [f for f in os.listdir(dataset_path) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if len(image_files) == 0:
        print(f"⚠️  Tidak ada gambar ditemukan di {dataset_path}")
        return features_list
    
    print(f"\n📂 Memproses {len(image_files)} gambar dari {dataset_path}...")
    print("=" * 80)
    
    for idx, filename in enumerate(image_files, 1):
        filepath = os.path.join(dataset_path, filename)
        
        # Baca gambar
        image = cv2.imread(filepath)
        
        if image is None:
            print(f"⚠️  Gagal membaca: {filename}")
            continue
        
        # Resize untuk konsistensi
        image = resize_image(image, target_width=400)
        
        # Segmentasi menggunakan K-Means
        mask, masked_image, clustered_image = create_kmeans_mask(image, k=2)
        
        # Ekstraksi fitur RGB
        rgb_features = extract_rgb_features(image, mask)
        
        # Ekstraksi fitur HSV
        hsv_features = extract_hsv_features(image, mask)
        
        # Jika ekstraksi gagal (tidak ada buah terdeteksi)
        if rgb_features is None or hsv_features is None:
            print(f"⚠️  [{idx}/{len(image_files)}] {filename} - Buah tidak terdeteksi")
            continue
        
        # Gabungkan semua fitur
        features = {
            'filename': filename,
            'R': rgb_features['mean_red'],
            'G': rgb_features['mean_green'],
            'B': rgb_features['mean_blue'],
            'H': hsv_features['mean_hue'],
            'S': hsv_features['mean_saturation'],
            'V': hsv_features['mean_value'],
            'pixel_count': rgb_features['pixel_count']
        }
        
        features_list.append(features)
        
        # Progress indicator
        print(f"✓ [{idx}/{len(image_files)}] {filename}")
    
    return features_list


def display_summary_table(features_list, category_name):
    """
    Menampilkan summary table di terminal
    
    Parameters:
    -----------
    features_list : list
        List of dictionaries berisi fitur gambar
    category_name : str
        Nama kategori (MATANG atau MENTAH)
    """
    if len(features_list) == 0:
        print(f"\n❌ Tidak ada data untuk ditampilkan dari kategori {category_name}")
        return
    
    print(f"\n{'=' * 100}")
    print(f"📊 SUMMARY TABLE - {category_name.upper()}")
    print(f"{'=' * 100}")
    
    # Header tabel
    header = f"{'Filename':<30} {'R':>8} {'G':>8} {'B':>8} {'H':>8} {'S':>8} {'V':>8} {'Pixels':>10}"
    print(header)
    print("-" * 100)
    
    # Data rows
    for features in features_list:
        row = (f"{features['filename']:<30} "
               f"{features['R']:>8.2f} "
               f"{features['G']:>8.2f} "
               f"{features['B']:>8.2f} "
               f"{features['H']:>8.2f} "
               f"{features['S']:>8.2f} "
               f"{features['V']:>8.2f} "
               f"{features['pixel_count']:>10}")
        print(row)
    
    print("-" * 100)
    
    # Statistik rata-rata
    avg_r = np.mean([f['R'] for f in features_list])
    avg_g = np.mean([f['G'] for f in features_list])
    avg_b = np.mean([f['B'] for f in features_list])
    avg_h = np.mean([f['H'] for f in features_list])
    avg_s = np.mean([f['S'] for f in features_list])
    avg_v = np.mean([f['V'] for f in features_list])
    
    avg_row = (f"{'RATA-RATA':<30} "
               f"{avg_r:>8.2f} "
               f"{avg_g:>8.2f} "
               f"{avg_b:>8.2f} "
               f"{avg_h:>8.2f} "
               f"{avg_s:>8.2f} "
               f"{avg_v:>8.2f} "
               f"{'-':>10}")
    print(avg_row)
    print("=" * 100)
    
    # Analisis untuk threshold
    print(f"\n💡 ANALISIS UNTUK THRESHOLD:")
    print(f"   • Rata-rata Hue (H): {avg_h:.2f}")
    print(f"   • Rata-rata Red/Green Ratio: {avg_r/avg_g:.2f}")
    print(f"   • Jumlah sampel: {len(features_list)}")


def main():
    """
    Main function untuk menjalankan ekstraksi fitur
    """
    print("\n" + "=" * 100)
    print("🥭 MANGO RIPENESS DETECTION - FEATURE EXTRACTION")
    print("=" * 100)
    
    # Path ke dataset
    base_path = os.path.join(os.path.dirname(__file__), 'dataset')
    matang_path = os.path.join(base_path, 'matang')
    mentah_path = os.path.join(base_path, 'mentah')
    
    # Ekstraksi fitur dari kategori MATANG
    print("\n🔍 Memproses kategori: MATANG")
    matang_features = extract_features_from_dataset(matang_path)
    display_summary_table(matang_features, "MATANG")
    
    # Ekstraksi fitur dari kategori MENTAH
    print("\n🔍 Memproses kategori: MENTAH")
    mentah_features = extract_features_from_dataset(mentah_path)
    display_summary_table(mentah_features, "MENTAH")
    
    # Rekomendasi threshold berdasarkan data
    if len(matang_features) > 0 and len(mentah_features) > 0:
        matang_avg_h = np.mean([f['H'] for f in matang_features])
        mentah_avg_h = np.mean([f['H'] for f in mentah_features])
        
        matang_avg_r = np.mean([f['R'] for f in matang_features])
        matang_avg_g = np.mean([f['G'] for f in matang_features])
        mentah_avg_r = np.mean([f['R'] for f in mentah_features])
        mentah_avg_g = np.mean([f['G'] for f in mentah_features])
        
        matang_rg_ratio = matang_avg_r / matang_avg_g
        mentah_rg_ratio = mentah_avg_r / mentah_avg_g
        
        # Threshold berada di tengah-tengah rata-rata kedua kategori
        recommended_hue = (matang_avg_h + mentah_avg_h) / 2
        recommended_rg_ratio = (matang_rg_ratio + mentah_rg_ratio) / 2
        
        print("\n" + "=" * 100)
        print("🎯 REKOMENDASI THRESHOLD:")
        print("=" * 100)
        print(f"   Hue Threshold: {recommended_hue:.2f}")
        print(f"   Red/Green Ratio Threshold: {recommended_rg_ratio:.2f}")
        print(f"\n   Logika Klasifikasi:")
        print(f"   • MATANG jika: Hue > {recommended_hue:.2f} DAN Red/Green Ratio > {recommended_rg_ratio:.2f}")
        print(f"   • MENTAH jika: Kondisi di atas tidak terpenuhi")
        print("=" * 100)
    
    print("\n✅ Ekstraksi fitur selesai!\n")


if __name__ == "__main__":
    main()
