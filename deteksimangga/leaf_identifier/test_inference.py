"""
Script 2: Inference Script
Script untuk testing klasifikasi mangga pada single image
Menampilkan hasil dengan OpenCV window (text label + bounding box)
"""

import os
import sys
import cv2
import numpy as np
from .image_processor import create_kmeans_mask, resize_image, extract_rgb_features, extract_hsv_features, get_bounding_box
from .classifier import classify_mango, get_classification_info


def draw_result_on_image(image, mask, result, confidence, rgb_features, hsv_features):
    """
    Menggambar hasil klasifikasi pada gambar
    
    Parameters:
    -----------
    image : numpy.ndarray
        Gambar input dalam format BGR
    mask : numpy.ndarray
        Binary mask untuk area buah
    result : str
        Hasil klasifikasi (MATANG atau MENTAH)
    confidence : float
        Confidence score
    rgb_features : dict
        Fitur RGB
    hsv_features : dict
        Fitur HSV
    
    Returns:
    --------
    numpy.ndarray : Gambar dengan hasil klasifikasi
    """
    # Copy gambar untuk menggambar
    output_image = image.copy()
    
    # Dapatkan bounding box
    bbox = get_bounding_box(mask)
    
    if bbox is not None:
        x, y, w, h = bbox
        
        # Tentukan warna berdasarkan hasil
        # MATANG = Hijau, MENTAH = Merah
        if result == "MATANG":
            color = (0, 255, 0)  # Hijau (BGR)
        else:
            color = (0, 0, 255)  # Merah (BGR)
        
        # Gambar bounding box
        cv2.rectangle(output_image, (x, y), (x + w, y + h), color, 3)
        
        # Gambar label di atas bounding box
        label = f"{result} ({confidence:.1f}%)"
        
        # Hitung ukuran text untuk background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        font_thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        # Gambar background untuk text (agar lebih mudah dibaca)
        cv2.rectangle(output_image, 
                     (x, y - text_height - baseline - 10), 
                     (x + text_width + 10, y), 
                     color, 
                     -1)  # -1 = filled rectangle
        
        # Gambar text
        cv2.putText(output_image, 
                   label, 
                   (x + 5, y - baseline - 5), 
                   font, 
                   font_scale, 
                   (255, 255, 255),  # Putih
                   font_thickness)
    
    # Tambahkan informasi fitur di pojok kiri atas
    info_y = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 1
    
    # Background untuk info
    cv2.rectangle(output_image, (10, 10), (300, 200), (0, 0, 0), -1)
    cv2.rectangle(output_image, (10, 10), (300, 200), (255, 255, 255), 2)
    
    # Informasi fitur
    red_green_ratio = rgb_features['mean_red'] / rgb_features['mean_green']
    
    info_lines = [
        f"RGB: R={rgb_features['mean_red']:.1f} G={rgb_features['mean_green']:.1f} B={rgb_features['mean_blue']:.1f}",
        f"HSV: H={hsv_features['mean_hue']:.1f} S={hsv_features['mean_saturation']:.1f} V={hsv_features['mean_value']:.1f}",
        f"R/G Ratio: {red_green_ratio:.2f}",
        f"Pixels: {rgb_features['pixel_count']}"
    ]
    
    for i, line in enumerate(info_lines):
        cv2.putText(output_image, 
                   line, 
                   (20, info_y + i * 30), 
                   font, 
                   font_scale, 
                   (255, 255, 255), 
                   font_thickness)
    
    return output_image


def test_single_image(image_path):
    """
    Test klasifikasi pada single image
    
    Parameters:
    -----------
    image_path : str
        Path ke file gambar
    """
    print("\n" + "=" * 80)
    print("🥭 MANGO RIPENESS DETECTION - INFERENCE TEST")
    print("=" * 80)
    
    # Cek apakah file ada
    if not os.path.exists(image_path):
        print(f"❌ File tidak ditemukan: {image_path}")
        return
    
    # Baca gambar
    print(f"\n📂 Membaca gambar: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"❌ Gagal membaca gambar: {image_path}")
        return
    
    print(f"✓ Gambar berhasil dibaca: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Resize untuk konsistensi
    print("\n🔄 Resize gambar...")
    image = resize_image(image, target_width=600)
    print(f"✓ Gambar diresize: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Segmentasi menggunakan K-Means
    print("\n🎯 Segmentasi K-Means (k=2)...")
    mask, masked_image, clustered_image = create_kmeans_mask(image, k=2)
    print("✓ Segmentasi selesai")
    
    # Ekstraksi fitur RGB
    print("\n🔍 Ekstraksi fitur RGB...")
    rgb_features = extract_rgb_features(image, mask)
    
    if rgb_features is None:
        print("❌ Gagal ekstraksi fitur RGB (buah tidak terdeteksi)")
        return
    
    print(f"✓ RGB Features:")
    print(f"   • Red: {rgb_features['mean_red']:.2f}")
    print(f"   • Green: {rgb_features['mean_green']:.2f}")
    print(f"   • Blue: {rgb_features['mean_blue']:.2f}")
    print(f"   • Pixels: {rgb_features['pixel_count']}")
    
    # Ekstraksi fitur HSV
    print("\n🔍 Ekstraksi fitur HSV...")
    hsv_features = extract_hsv_features(image, mask)
    
    if hsv_features is None:
        print("❌ Gagal ekstraksi fitur HSV (buah tidak terdeteksi)")
        return
    
    print(f"✓ HSV Features:")
    print(f"   • Hue: {hsv_features['mean_hue']:.2f}")
    print(f"   • Saturation: {hsv_features['mean_saturation']:.2f}")
    print(f"   • Value: {hsv_features['mean_value']:.2f}")
    
    # Klasifikasi
    print("\n🤖 Klasifikasi...")
    result, confidence = classify_mango(rgb_features, hsv_features)
    
    # Dapatkan informasi lengkap
    info = get_classification_info(rgb_features, hsv_features)
    
    print(f"\n{'=' * 80}")
    print(f"📊 HASIL KLASIFIKASI")
    print(f"{'=' * 80}")
    print(f"   Hasil: {result}")
    print(f"   Confidence: {confidence:.1f}%")
    print(f"   Jarak ke MATANG: {info['distance_matang']:.2f}")
    print(f"   Jarak ke MENTAH: {info['distance_mentah']:.2f}")
    
    red_green_ratio = rgb_features['mean_red'] / rgb_features['mean_green']
    print(f"\n   Red/Green Ratio: {red_green_ratio:.2f}")
    print(f"{'=' * 80}")
    
    # Gambar hasil pada gambar
    print("\n🎨 Menggambar hasil...")
    result_image = draw_result_on_image(image, mask, result, confidence, rgb_features, hsv_features)
    
    # Tampilkan hasil dengan OpenCV window
    print("\n👁️  Menampilkan hasil (tekan tombol apapun untuk keluar)...")
    
    # Buat window dengan ukuran yang sesuai
    window_name = "Mango Ripeness Detection - Result"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Tampilkan gambar asli, mask, dan hasil
    # Gabungkan dalam satu display
    display_height = result_image.shape[0]
    display_width = result_image.shape[1]
    
    # Resize mask dan clustered untuk display
    mask_display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    # Gabungkan horizontal: Original | Mask | Result
    combined = np.hstack([image, mask_display, result_image])
    
    # Tampilkan
    cv2.imshow(window_name, combined)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n✅ Inference selesai!\n")


def main():
    """
    Main function untuk menjalankan inference
    """
    # Cek argumen command line
    if len(sys.argv) < 2:
        print("\n❌ Usage: python test_inference.py <path_to_image>")
        print("\nContoh:")
        print("   python test_inference.py dataset/matang/mango1.jpg")
        print("   python test_inference.py test_images/test_mango.png")
        return
    
    # Ambil path gambar dari argumen
    image_path = sys.argv[1]
    
    # Jalankan inference
    test_single_image(image_path)


if __name__ == "__main__":
    main()
