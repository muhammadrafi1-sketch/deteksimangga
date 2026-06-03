"""
Image Processor Module
Modul untuk memproses gambar mangga: resize, segmentasi K-Means, 
ekstraksi RGB, dan ekstraksi HSV dengan masking untuk isolasi area buah
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans


def load_image(image_path):
    """
    Load gambar dari file path
    
    Parameters:
    -----------
    image_path : str
        Path ke file gambar
    
    Returns:
    --------
    numpy.ndarray : Gambar dalam format BGR (OpenCV)
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Gagal membaca gambar: {image_path}")
    return image


def create_kmeans_mask(image, k=2):
    """
    Membuat mask menggunakan K-Means Clustering untuk memisahkan buah mangga dari background
    
    K-Means Clustering adalah algoritma unsupervised learning yang mengelompokkan
    pixel berdasarkan kesamaan warna. Dengan k=2, kita membagi gambar menjadi 2 cluster:
    - Cluster 1: Area buah mangga (foreground)
    - Cluster 2: Background
    
    Parameters:
    -----------
    image : numpy.ndarray
        Gambar input dalam format BGR (OpenCV)
    k : int
        Jumlah cluster untuk K-Means (default: 2)
    
    Returns:
    --------
    tuple : (mask, masked_image, clustered_image)
        mask : numpy.ndarray - Binary mask (0 atau 255) untuk area buah
        masked_image : numpy.ndarray - Gambar dengan mask applied (untuk preview)
        clustered_image : numpy.ndarray - Hasil clustering (untuk visualisasi)
    """
    # Resize gambar untuk mempercepat K-Means (max 800px pada sisi terpanjang)
    original_shape = image.shape
    max_dim = 800
    height, width = image.shape[:2]
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    else:
        resized = image
    
    # Reshape gambar dari (height, width, 3) menjadi (height*width, 3)
    # Setiap pixel menjadi satu data point dengan 3 fitur (B, G, R)
    pixel_values = resized.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)
    
    # Jalankan K-Means Clustering
    # n_clusters=k : Jumlah cluster yang diinginkan
    # random_state=42 : Seed untuk reproducibility
    # n_init=10 : Jumlah inisialisasi berbeda untuk menemukan hasil terbaik
    # max_iter=300 : Maksimal iterasi untuk konvergensi
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(pixel_values)
    
    # Konversi cluster centers ke uint8 (0-255)
    # Konversi cluster centers ke uint8 untuk representasi warna
    centers = kmeans.cluster_centers_
    centers = np.uint8(centers)
    
    # Ganti setiap pixel dengan warna cluster center-nya
    # labels adalah array 1D, gunakan untuk indexing centers
    # Flatten labels untuk indexing yang benar
    segmented_image = centers[labels]
    
    # Reshape kembali ke dimensi gambar resized
    clustered_image = segmented_image.reshape(resized.shape)
    
    # Tentukan cluster mana yang merupakan buah mangga
    # Asumsi: Buah mangga memiliki intensitas warna lebih tinggi dari background
    # Hitung rata-rata intensitas setiap cluster
    cluster_intensities = [np.mean(centers[i].astype(np.float32)) for i in range(k)]
    
    # Cluster dengan intensitas lebih tinggi dianggap sebagai buah
    fruit_cluster = np.argmax(cluster_intensities)
    
    # Buat binary mask: 255 untuk buah, 0 untuk background (pada resized image)
    mask_resized = np.zeros(resized.shape[:2], dtype=np.uint8)
    mask_resized[labels.reshape(resized.shape[:2]) == fruit_cluster] = 255
    
    # Apply morphological operations untuk menghilangkan noise
    # Closing: Menghilangkan lubang kecil di dalam objek
    # Opening: Menghilangkan noise kecil di luar objek
    kernel = np.ones((5, 5), np.uint8)
    mask_resized = cv2.morphologyEx(mask_resized, cv2.MORPH_CLOSE, kernel)
    mask_resized = cv2.morphologyEx(mask_resized, cv2.MORPH_OPEN, kernel)
    
    # Upscale mask kembali ke ukuran original
    mask = cv2.resize(mask_resized, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_NEAREST)
    
    # Upscale clustered_image kembali ke ukuran original
    clustered_image = cv2.resize(clustered_image, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_NEAREST)
    
    # Buat masked image untuk preview
    # bitwise_and: Operasi AND antara gambar dan mask
    # Pixel dengan mask=0 akan menjadi hitam, mask=255 tetap asli
    masked_image = cv2.bitwise_and(image, image, mask=mask)
    
    return mask, masked_image, clustered_image


def resize_image(image, target_width=400):
    """
    Resize gambar dengan mempertahankan aspect ratio
    
    Parameters:
    -----------
    image : numpy.ndarray
        Gambar input dalam format BGR (OpenCV)
    target_width : int
        Lebar target untuk resize (default: 400)
    
    Returns:
    --------
    numpy.ndarray : Gambar yang sudah diresize
    """
    height, width = image.shape[:2]
    aspect_ratio = height / width
    target_height = int(target_width * aspect_ratio)
    
    resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized


def extract_rgb_features(image, mask):
    """
    Ekstraksi fitur RGB dari gambar
    Menghitung rata-rata nilai Red, Green, Blue HANYA dari area buah mangga (berdasarkan mask)
    
    Parameters:
    -----------
    image : numpy.ndarray
        Gambar input dalam format BGR (OpenCV)
    mask : numpy.ndarray
        Binary mask untuk area buah (hasil dari K-Means)
    
    Returns:
    --------
    dict : Dictionary berisi mean_red, mean_green, mean_blue, pixel_count
           Jika buah tidak terdeteksi, return None
    """
    # Hitung jumlah pixel buah (pixel dengan mask=255)
    pixel_count = np.count_nonzero(mask)
    
    # Jika tidak ada pixel buah terdeteksi
    if pixel_count == 0:
        print("⚠️  Tidak ada area buah terdeteksi!")
        return None
    
    # Ekstrak pixel buah saja menggunakan mask
    # mask > 0 menghasilkan boolean array
    # image[mask > 0] mengambil hanya pixel dengan mask=255
    fruit_pixels = image[mask > 0]
    
    # OpenCV menggunakan format BGR, bukan RGB
    # Channel 0 = Blue, Channel 1 = Green, Channel 2 = Red
    mean_blue = np.mean(fruit_pixels[:, 0])
    mean_green = np.mean(fruit_pixels[:, 1])
    mean_red = np.mean(fruit_pixels[:, 2])
    
    return {
        'mean_red': round(mean_red, 2),
        'mean_green': round(mean_green, 2),
        'mean_blue': round(mean_blue, 2),
        'pixel_count': pixel_count
    }


def extract_hsv_features(image, mask):
    """
    Ekstraksi fitur HSV dari gambar
    Menghitung rata-rata nilai Hue, Saturation, Value HANYA dari area buah mangga
    
    HSV Color Space:
    - Hue (H): Warna dasar (0-179 di OpenCV, 0-360 derajat di teori)
      * 0-30: Merah-Oranye
      * 30-60: Kuning-Hijau
      * 60-120: Hijau
    - Saturation (S): Intensitas warna (0-255)
      * 0: Abu-abu (tidak berwarna)
      * 255: Warna murni
    - Value (V): Kecerahan (0-255)
      * 0: Hitam
      * 255: Terang
    
    Parameters:
    -----------
    image : numpy.ndarray
        Gambar input dalam format BGR (OpenCV)
    mask : numpy.ndarray
        Binary mask untuk area buah
    
    Returns:
    --------
    dict : Dictionary berisi mean_hue, mean_saturation, mean_value
           Jika buah tidak terdeteksi, return None
    """
    # Hitung jumlah pixel buah
    pixel_count = np.count_nonzero(mask)
    
    if pixel_count == 0:
        print("⚠️  Tidak ada area buah terdeteksi!")
        return None
    
    # Konversi BGR ke HSV
    # cv2.cvtColor: Fungsi OpenCV untuk konversi color space
    # COLOR_BGR2HSV: Konversi dari BGR (format OpenCV) ke HSV
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Ekstrak pixel buah saja menggunakan mask
    fruit_pixels_hsv = hsv_image[mask > 0]
    
    # Hitung rata-rata setiap channel HSV
    # Channel 0 = Hue (0-179)
    # Channel 1 = Saturation (0-255)
    # Channel 2 = Value (0-255)
    mean_hue = np.mean(fruit_pixels_hsv[:, 0])
    mean_saturation = np.mean(fruit_pixels_hsv[:, 1])
    mean_value = np.mean(fruit_pixels_hsv[:, 2])
    
    return {
        'mean_hue': round(mean_hue, 2),
        'mean_saturation': round(mean_saturation, 2),
        'mean_value': round(mean_value, 2)
    }


def get_bounding_box(mask):
    """
    Mendapatkan bounding box dari mask untuk visualisasi
    
    Parameters:
    -----------
    mask : numpy.ndarray
        Binary mask untuk area buah
    
    Returns:
    --------
    tuple : (x, y, w, h) koordinat dan ukuran bounding box
            None jika tidak ada kontur terdeteksi
    """
    # Cari kontur dari mask
    # cv2.findContours: Mencari outline objek dalam binary image
    # RETR_EXTERNAL: Hanya ambil kontur terluar
    # CHAIN_APPROX_SIMPLE: Kompresi kontur (hapus point redundan)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return None
    
    # Ambil kontur terbesar (asumsi: buah mangga adalah objek terbesar)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Dapatkan bounding rectangle
    # cv2.boundingRect: Mengembalikan (x, y, width, height)
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    return (x, y, w, h)
