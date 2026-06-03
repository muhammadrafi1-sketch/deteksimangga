"""
Inference Script (Script 2)
Script untuk inferensi single image dengan output visual menggunakan OpenCV window
Menampilkan hasil klasifikasi kematangan mangga (MATANG/MENTAH) dengan bounding box dan teks
"""

import cv2
import numpy as np
import sys
from pathlib import Path

from .image_processor import resize_image, extract_rgb_features, extract_hsv_features, create_kmeans_mask
from .classifier import classify_mango_mdc, load_centroids


def draw_result_on_image(image, result, confidence, mask):
    """
    Gambar hasil klasifikasi pada image dengan bounding box dan teks
    
    Parameters:
    -----------
    image : numpy.ndarray
        Original image (BGR format)
    result : str
        Hasil klasifikasi ("MATANG" atau "MENTAH")
    confidence : float
        Confidence score (0-100%)
    mask : numpy.ndarray
        Binary mask dari K-Means segmentation
    
    Returns:
    --------
    numpy.ndarray
        Image dengan annotation (BGR format)
    """
    # Copy image untuk annotation
    annotated = image.copy()
    
    # Cari contours dari mask untuk bounding box
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        # Ambil contour terbesar (asumsi: mangga adalah objek terbesar)
        largest_contour = max(contours, key=lambda c: cv2.contourArea(c))
        
        # Dapatkan bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Tentukan warna box berdasarkan hasil
        if result == "MATANG":
            box_color = (0, 140, 255)  # Orange (BGR)
            text_color = (0, 140, 255)
        elif result == "MENTAH":
            box_color = (0, 255, 0)  # Green (BGR)
            text_color = (0, 255, 0)
        else:  # TIDAK YAKIN
            box_color = (0, 0, 255)  # Red (BGR)
            text_color = (0, 0, 255)
        
        # Gambar bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 3)
        
        # Siapkan teks hasil
        result_text = f"{result} ({confidence:.1f}%)"
        
        # Ukuran font dan thickness
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 3
        
        # Hitung ukuran teks untuk background rectangle
        (text_width, text_height), baseline = cv2.getTextSize(
            result_text, font, font_scale, thickness
        )
        
        # Posisi teks (di atas bounding box)
        text_x = x
        text_y = y - 10
        
        # Jika teks keluar dari frame atas, taruh di dalam box
        if text_y - text_height < 0:
            text_y = y + text_height + 10
        
        # Gambar background rectangle untuk teks (semi-transparent)
        overlay = annotated.copy()
        cv2.rectangle(
            overlay,
            (text_x, text_y - text_height - baseline),
            (text_x + text_width, text_y + baseline),
            (0, 0, 0),
            -1
        )
        # Blend overlay dengan original (alpha=0.6)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
        
        # Gambar teks
        cv2.putText(
            annotated,
            result_text,
            (text_x, text_y),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA
        )
    
    return annotated


def main():
    """
    Main function untuk inference single image
    """
    # Cek argument
    if len(sys.argv) < 2:
        print("Usage: python -m leaf_identifier.inference <path_to_image>")
        print("Example: python -m leaf_identifier.inference test_images/mangga1.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Validasi file exists
    if not Path(image_path).exists():
        print(f"Error: File tidak ditemukan - {image_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"MANGO RIPENESS DETECTION - INFERENCE")
    print(f"{'='*60}")
    print(f"Image: {image_path}")
    print(f"{'='*60}\n")
    
    # Load centroids untuk Minimum Distance Classifier
    print("Loading centroids...")
    try:
        centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = load_centroids('centroids.json')
    except FileNotFoundError:
        print("❌ ERROR: File centroids.json tidak ditemukan!")
        print("\nJalankan training terlebih dahulu:")
        print("  python -m leaf_identifier.train_classifier")
        sys.exit(1)
    
    # Load image
    print("Loading image...")
    image = cv2.imread(str(image_path))
    
    if image is None:
        print("Error: Gagal membaca gambar")
        sys.exit(1)
    
    # Resize untuk processing (optional, untuk konsistensi)
    print("Preprocessing...")
    resized_image = resize_image(image, target_width=800)
    
    # Segmentasi mangga menggunakan K-Means (k=2)
    print("Segmenting mango using K-Means (k=2)...")
    mask, masked_image, clustered_image = create_kmeans_mask(resized_image)
    
    # Ekstraksi fitur warna (RGB + HSV) dengan K-Means masking
    print("Extracting color features (RGB + HSV)...")
    rgb_features = extract_rgb_features(resized_image, mask)
    hsv_features = extract_hsv_features(resized_image, mask)
    
    if hsv_features is None:
        print("\n❌ MANGGA TIDAK TERDETEKSI")
        print("Coba gambar lain dengan mangga yang lebih jelas.\n")
        
        # Tampilkan image dan mask untuk debugging
        cv2.imshow("Original Image", resized_image)
        cv2.imshow("K-Means Mask", masked_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        sys.exit(0)
    
    # Klasifikasi kematangan mangga menggunakan Minimum Distance Classifier
    print("Classifying ripeness using Minimum Distance Classifier...")
    result, confidence, dist_matang, dist_mentah = classify_mango_mdc(
        rgb_features, 
        hsv_features,
        centroid_matang,
        centroid_mentah,
        distance_threshold,
        confidence_threshold
    )
    
    # Print hasil ke terminal
    print(f"\n{'='*60}")
    print(f"HASIL DETEKSI")
    print(f"{'='*60}")
    print(f"Kematangan: {result}")
    print(f"Confidence: {confidence:.2f}%")
    print(f"{'='*60}")
    print(f"\nFITUR WARNA:")
    print(f"  RGB:")
    print(f"    - Red   : {rgb_features['mean_red']:.2f}")
    print(f"    - Green : {rgb_features['mean_green']:.2f}")
    print(f"    - Blue  : {rgb_features['mean_blue']:.2f}")
    print(f"  HSV:")
    print(f"    - Hue        : {hsv_features['mean_hue']:.2f}")
    print(f"    - Saturation : {hsv_features['mean_saturation']:.2f}")
    print(f"    - Value      : {hsv_features['mean_value']:.2f}")
    print(f"{'='*60}\n")
    
    # Gambar hasil pada image
    annotated_image = draw_result_on_image(resized_image, result, confidence, mask)
    
    # Tampilkan hasil dengan OpenCV window
    print("Displaying result... (Press any key to close)")
    
    # Window untuk original image
    cv2.imshow("Original Image", resized_image)
    
    # Window untuk K-Means mask
    cv2.imshow("K-Means Segmentation", masked_image)
    
    # Window untuk hasil klasifikasi dengan annotation
    cv2.imshow("Ripeness Detection Result", annotated_image)
    
    # Wait untuk key press
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\nInference selesai!")


if __name__ == "__main__":
    main()
