"""
Classifier Module
Minimum Distance Classifier untuk membedakan mangga MATANG dan MENTAH
berdasarkan jarak Euclidean ke centroid kelas
"""

import numpy as np
import json
import os


def train_classifier(dataset_path):
    """
    Hitung centroid (mean features) untuk kelas MATANG dan MENTAH dari dataset
    serta threshold otomatis untuk klasifikasi
    
    Centroid adalah titik pusat dari setiap kelas dalam feature space 6-dimensi [R, G, B, H, S, V].
    Dihitung dengan cara mengambil rata-rata (mean) dari semua feature vector dalam kelas tersebut.
    
    Threshold dihitung otomatis dari distribusi jarak intra-class untuk menentukan
    batas keputusan yang reliable.
    
    Parameters:
    -----------
    dataset_path : str
        Path ke folder dataset yang berisi subfolder 'matang/' dan 'mentah/'
    
    Returns:
    --------
    tuple : (centroid_matang, centroid_mentah, distance_threshold, confidence_threshold)
        centroid_matang : numpy.ndarray - Feature vector [R, G, B, H, S, V] untuk kelas MATANG
        centroid_mentah : numpy.ndarray - Feature vector [R, G, B, H, S, V] untuk kelas MENTAH
        distance_threshold : float - Threshold jarak maksimal untuk klasifikasi valid
        confidence_threshold : float - Threshold confidence minimal untuk klasifikasi yakin
    """
    from .image_processor import load_image, resize_image, create_kmeans_mask, extract_rgb_features, extract_hsv_features
    import glob
    
    # Inisialisasi list untuk menyimpan features
    matang_features = []
    mentah_features = []
    
    # Path ke folder MATANG dan MENTAH
    matang_path = os.path.join(dataset_path, 'matang')
    mentah_path = os.path.join(dataset_path, 'mentah')
    
    print("=" * 60)
    print("TRAINING MINIMUM DISTANCE CLASSIFIER")
    print("=" * 60)
    
    # Proses gambar MATANG
    print(f"\n[1/2] Memproses gambar MATANG dari: {matang_path}")
    matang_images = glob.glob(os.path.join(matang_path, '*.jpg')) + \
                    glob.glob(os.path.join(matang_path, '*.jpeg')) + \
                    glob.glob(os.path.join(matang_path, '*.png'))
    
    for img_path in matang_images:
        try:
            # Load dan proses gambar
            image = load_image(img_path)
            resized = resize_image(image)
            mask, masked_image, clustered_image = create_kmeans_mask(resized)
            
            # Ekstrak features
            rgb_features = extract_rgb_features(resized, mask)
            hsv_features = extract_hsv_features(resized, mask)
            
            # Gabungkan menjadi feature vector [R, G, B, H, S, V]
            feature_vector = [
                rgb_features['mean_red'],
                rgb_features['mean_green'],
                rgb_features['mean_blue'],
                hsv_features['mean_hue'],
                hsv_features['mean_saturation'],
                hsv_features['mean_value']
            ]
            matang_features.append(feature_vector)
            print(f"  ✓ {os.path.basename(img_path)}")
        except Exception as e:
            print(f"  ✗ {os.path.basename(img_path)}: {str(e)}")
    
    # Proses gambar MENTAH
    print(f"\n[2/2] Memproses gambar MENTAH dari: {mentah_path}")
    mentah_images = glob.glob(os.path.join(mentah_path, '*.jpg')) + \
                    glob.glob(os.path.join(mentah_path, '*.jpeg')) + \
                    glob.glob(os.path.join(mentah_path, '*.png'))
    
    for img_path in mentah_images:
        try:
            # Load dan proses gambar
            image = load_image(img_path)
            resized = resize_image(image)
            mask, masked_image, clustered_image = create_kmeans_mask(resized)
            
            # Ekstrak features
            rgb_features = extract_rgb_features(resized, mask)
            hsv_features = extract_hsv_features(resized, mask)
            
            # Gabungkan menjadi feature vector [R, G, B, H, S, V]
            feature_vector = [
                rgb_features['mean_red'],
                rgb_features['mean_green'],
                rgb_features['mean_blue'],
                hsv_features['mean_hue'],
                hsv_features['mean_saturation'],
                hsv_features['mean_value']
            ]
            mentah_features.append(feature_vector)
            print(f"  ✓ {os.path.basename(img_path)}")
        except Exception as e:
            print(f"  ✗ {os.path.basename(img_path)}: {str(e)}")
    
    # Hitung centroid (mean) untuk setiap kelas
    if len(matang_features) == 0 or len(mentah_features) == 0:
        raise ValueError("Dataset tidak lengkap! Pastikan ada gambar di folder matang/ dan mentah/")
    
    matang_features = np.array(matang_features)
    mentah_features = np.array(mentah_features)
    
    centroid_matang = np.mean(matang_features, axis=0)
    centroid_mentah = np.mean(mentah_features, axis=0)
    
    # Hitung threshold otomatis
    distance_threshold, confidence_threshold = calculate_thresholds(
        matang_features, mentah_features, centroid_matang, centroid_mentah
    )
    
    print("\n" + "=" * 60)
    print("HASIL TRAINING")
    print("=" * 60)
    print(f"Total gambar MATANG: {len(matang_features)}")
    print(f"Total gambar MENTAH: {len(mentah_features)}")
    print(f"\nCentroid MATANG [R, G, B, H, S, V]:")
    print(f"  {centroid_matang}")
    print(f"\nCentroid MENTAH [R, G, B, H, S, V]:")
    print(f"  {centroid_mentah}")
    print(f"\nThreshold Otomatis:")
    print(f"  Distance Threshold: {distance_threshold:.2f}")
    print(f"  Confidence Threshold: {confidence_threshold:.2f}%")
    print("=" * 60)
    
    return centroid_matang, centroid_mentah, distance_threshold, confidence_threshold


def calculate_thresholds(matang_features, mentah_features, centroid_matang, centroid_mentah):
    """
    Hitung threshold otomatis untuk distance dan confidence berdasarkan distribusi training data
    
    Algoritma:
    1. Hitung jarak setiap sample ke centroid kelasnya sendiri (intra-class distance)
    2. Distance threshold = mean + 2*std dari intra-class distances
    3. Confidence threshold = 60% (empiris untuk balance antara precision dan recall)
    
    Parameters:
    -----------
    matang_features : numpy.ndarray
        Array of feature vectors untuk kelas MATANG
    mentah_features : numpy.ndarray
        Array of feature vectors untuk kelas MENTAH
    centroid_matang : numpy.ndarray
        Centroid kelas MATANG
    centroid_mentah : numpy.ndarray
        Centroid kelas MENTAH
    
    Returns:
    --------
    tuple : (distance_threshold, confidence_threshold)
        distance_threshold : float - Jarak maksimal untuk klasifikasi valid
        confidence_threshold : float - Confidence minimal untuk klasifikasi yakin
    """
    # Hitung jarak intra-class untuk MATANG
    distances_matang = []
    for feature in matang_features:
        dist = np.linalg.norm(feature - centroid_matang)
        distances_matang.append(dist)
    
    # Hitung jarak intra-class untuk MENTAH
    distances_mentah = []
    for feature in mentah_features:
        dist = np.linalg.norm(feature - centroid_mentah)
        distances_mentah.append(dist)
    
    # Gabungkan semua intra-class distances
    all_intra_distances = distances_matang + distances_mentah
    
    # Hitung statistik
    mean_distance = np.mean(all_intra_distances)
    std_distance = np.std(all_intra_distances)
    
    # Distance threshold: mean + 2*std (cover ~95% data normal)
    # Sample yang jaraknya > threshold dianggap outlier/tidak yakin
    distance_threshold = mean_distance + 2 * std_distance
    
    # Confidence threshold: 60% (empiris)
    # Confidence < 60% berarti jarak ke kedua centroid hampir sama (ambiguous)
    confidence_threshold = 60.0
    
    return distance_threshold, confidence_threshold


def classify_mango_mdc(rgb_features, hsv_features, centroid_matang, centroid_mentah, 
                       distance_threshold=None, confidence_threshold=None):
    """
    Klasifikasi mangga menggunakan Minimum Distance Classifier dengan threshold-based decision
    
    Algoritma:
    1. Bentuk feature vector [R, G, B, H, S, V] dari input
    2. Hitung jarak Euclidean ke centroid MATANG dan MENTAH
    3. Pilih kelas dengan jarak terkecil (minimum distance)
    4. Validasi dengan threshold:
       - Jika jarak > distance_threshold → TIDAK YAKIN (terlalu jauh dari kedua kelas)
       - Jika confidence < confidence_threshold → TIDAK YAKIN (ambiguous, jarak hampir sama)
       - Jika lolos threshold → MATANG atau MENTAH
    
    Jarak Euclidean:
    d = sqrt((x1-x2)^2 + (y1-y2)^2 + ... + (z1-z2)^2)
    
    Parameters:
    -----------
    rgb_features : dict
        Dictionary berisi mean_red, mean_green, mean_blue
    hsv_features : dict
        Dictionary berisi mean_hue, mean_saturation, mean_value
    centroid_matang : numpy.ndarray
        Centroid kelas MATANG [R, G, B, H, S, V]
    centroid_mentah : numpy.ndarray
        Centroid kelas MENTAH [R, G, B, H, S, V]
    distance_threshold : float, optional
        Jarak maksimal untuk klasifikasi valid (default: None = no threshold)
    confidence_threshold : float, optional
        Confidence minimal untuk klasifikasi yakin (default: None = no threshold)
    
    Returns:
    --------
    tuple : (result, confidence, distance_matang, distance_mentah)
        result : str - "MATANG", "MENTAH", atau "TIDAK YAKIN"
        confidence : float - Confidence score 0-100%
        distance_matang : float - Jarak ke centroid MATANG
        distance_mentah : float - Jarak ke centroid MENTAH
    """
    
    # Bentuk feature vector dari input [R, G, B, H, S, V]
    feature_vector = np.array([
        rgb_features['mean_red'],
        rgb_features['mean_green'],
        rgb_features['mean_blue'],
        hsv_features['mean_hue'],
        hsv_features['mean_saturation'],
        hsv_features['mean_value']
    ])
    
    # Hitung jarak Euclidean ke setiap centroid
    # Euclidean distance: sqrt(sum((x - centroid)^2))
    distance_matang = np.linalg.norm(feature_vector - centroid_matang)
    distance_mentah = np.linalg.norm(feature_vector - centroid_mentah)
    
    # Klasifikasi: pilih kelas dengan jarak minimum
    if distance_matang < distance_mentah:
        result = "MATANG"
        min_distance = distance_matang
        max_distance = distance_mentah
    else:
        result = "MENTAH"
        min_distance = distance_mentah
        max_distance = distance_matang
    
    # Hitung confidence berdasarkan rasio jarak
    # Confidence tinggi jika jarak ke kelas terpilih jauh lebih kecil dari kelas lain
    # Formula: confidence = (1 - min_distance / (min_distance + max_distance)) * 100
    confidence = calculate_confidence_mdc(min_distance, max_distance)
    
    # Threshold-based validation (jika threshold disediakan)
    if distance_threshold is not None or confidence_threshold is not None:
        # Check 1: Apakah sample terlalu jauh dari kedua centroid?
        if distance_threshold is not None and min_distance > distance_threshold:
            result = "TIDAK YAKIN"
        
        # Check 2: Apakah confidence terlalu rendah (ambiguous)?
        elif confidence_threshold is not None and confidence < confidence_threshold:
            result = "TIDAK YAKIN"
    
    return result, confidence, distance_matang, distance_mentah


def calculate_confidence_mdc(min_distance, max_distance):
    """
    Hitung confidence score berdasarkan rasio jarak ke centroid
    
    Logika:
    - Jika min_distance << max_distance → confidence tinggi (yakin)
    - Jika min_distance ≈ max_distance → confidence rendah (ragu)
    
    Parameters:
    -----------
    min_distance : float
        Jarak ke centroid terdekat
    max_distance : float
        Jarak ke centroid terjauh
    
    Returns:
    --------
    float : Confidence score (0-100%)
    """
    # Hindari division by zero
    if min_distance + max_distance == 0:
        return 50.0
    
    # Confidence berdasarkan rasio jarak
    # Semakin besar selisih jarak, semakin tinggi confidence
    confidence = (1 - min_distance / (min_distance + max_distance)) * 100
    
    # Clamp ke range 0-100
    confidence = max(0, min(100, confidence))
    
    return round(confidence, 2)


def save_centroids(centroid_matang, centroid_mentah, distance_threshold=None, 
                   confidence_threshold=None, output_path='centroids.json'):
    """
    Simpan centroid dan threshold ke file JSON
    
    Parameters:
    -----------
    centroid_matang : numpy.ndarray
        Centroid kelas MATANG
    centroid_mentah : numpy.ndarray
        Centroid kelas MENTAH
    distance_threshold : float, optional
        Threshold jarak maksimal untuk klasifikasi valid
    confidence_threshold : float, optional
        Threshold confidence minimal untuk klasifikasi yakin
    output_path : str
        Path file output JSON
    """
    centroids = {
        'centroid_matang': centroid_matang.tolist(),
        'centroid_mentah': centroid_mentah.tolist(),
        'distance_threshold': distance_threshold,
        'confidence_threshold': confidence_threshold
    }
    
    with open(output_path, 'w') as f:
        json.dump(centroids, f, indent=4)
    
    print(f"\n✓ Centroids dan thresholds disimpan ke: {output_path}")


def load_centroids(centroids_path='centroids.json'):
    """
    Load centroid dan threshold dari file JSON
    
    Parameters:
    -----------
    centroids_path : str
        Path ke file centroids JSON
    
    Returns:
    --------
    tuple : (centroid_matang, centroid_mentah, distance_threshold, confidence_threshold)
        centroid_matang : numpy.ndarray
        centroid_mentah : numpy.ndarray
        distance_threshold : float or None
        confidence_threshold : float or None
    """
    if not os.path.exists(centroids_path):
        raise FileNotFoundError(
            f"File centroids tidak ditemukan: {centroids_path}\n"
            f"Jalankan training terlebih dahulu: python -m leaf_identifier.train_classifier"
        )
    
    with open(centroids_path, 'r') as f:
        centroids = json.load(f)
    
    centroid_matang = np.array(centroids['centroid_matang'])
    centroid_mentah = np.array(centroids['centroid_mentah'])
    distance_threshold = centroids.get('distance_threshold', None)
    confidence_threshold = centroids.get('confidence_threshold', None)
    
    return centroid_matang, centroid_mentah, distance_threshold, confidence_threshold


def classify_mango(rgb_features, hsv_features, centroids_path='centroids.json'):
    """
    Wrapper function untuk klasifikasi mangga dengan auto-load centroids
    
    Parameters:
    -----------
    rgb_features : dict
        Dictionary berisi mean_red, mean_green, mean_blue
    hsv_features : dict
        Dictionary berisi mean_hue, mean_saturation, mean_value
    centroids_path : str
        Path ke file centroids JSON (default: 'centroids.json')
    
    Returns:
    --------
    tuple : (result, confidence)
        result : str - "MATANG", "MENTAH", atau "TIDAK YAKIN"
        confidence : float - Confidence score 0-100%
    """
    # Load centroids dan thresholds
    centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = load_centroids(centroids_path)
    
    # Klasifikasi menggunakan MDC
    result, confidence, _, _ = classify_mango_mdc(
        rgb_features, hsv_features,
        centroid_matang, centroid_mentah,
        distance_threshold, confidence_threshold
    )
    
    return result, confidence


def get_classification_info(rgb_features, hsv_features, centroids_path='centroids.json'):
    """
    Get detailed classification information including distances
    
    Parameters:
    -----------
    rgb_features : dict
        Dictionary berisi mean_red, mean_green, mean_blue
    hsv_features : dict
        Dictionary berisi mean_hue, mean_saturation, mean_value
    centroids_path : str
        Path ke file centroids JSON (default: 'centroids.json')
    
    Returns:
    --------
    dict : Classification details
        {
            'result': str - "MATANG", "MENTAH", atau "TIDAK YAKIN"
            'confidence': float - Confidence score 0-100%
            'distance_matang': float - Jarak ke centroid MATANG
            'distance_mentah': float - Jarak ke centroid MENTAH
        }
    """
    # Load centroids dan thresholds
    centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = load_centroids(centroids_path)
    
    # Klasifikasi menggunakan MDC
    result, confidence, dist_matang, dist_mentah = classify_mango_mdc(
        rgb_features, hsv_features,
        centroid_matang, centroid_mentah,
        distance_threshold, confidence_threshold
    )
    
    return {
        'result': result,
        'confidence': confidence,
        'distance_matang': dist_matang,
        'distance_mentah': dist_mentah
    }
