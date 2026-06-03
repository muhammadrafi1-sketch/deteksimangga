"""
Test Dataset Module
Module untuk menguji akurasi klasifikasi menggunakan dataset dengan split 70/30
TIDAK menggunakan sklearn - implementasi manual
"""

import os
import random
from pathlib import Path

import cv2
from .image_processor import create_kmeans_mask, extract_rgb_features, extract_hsv_features
from .classifier import classify_mango_mdc


def load_dataset_images(dataset_path):
    """
    Load semua gambar dari folder dataset
    
    Parameters:
    -----------
    dataset_path : str
        Path ke folder dataset (harus berisi subfolder 'matang' dan 'mentah')
    
    Returns:
    --------
    dict : Dictionary berisi list gambar untuk setiap kelas
        {
            'matang': [(image_path, label), ...],
            'mentah': [(image_path, label), ...]
        }
    """
    
    dataset_path = Path(dataset_path)
    
    # Cek apakah folder dataset ada
    if not dataset_path.exists():
        raise FileNotFoundError(f"Folder dataset tidak ditemukan: {dataset_path}")
    
    # Path ke subfolder
    matang_path = dataset_path / "matang"
    mentah_path = dataset_path / "mentah"
    
    # Cek apakah subfolder ada
    if not matang_path.exists():
        raise FileNotFoundError(f"Folder matang tidak ditemukan: {matang_path}")
    if not mentah_path.exists():
        raise FileNotFoundError(f"Folder mentah tidak ditemukan: {mentah_path}")
    
    # Load gambar dari setiap folder
    dataset = {
        'matang': [],
        'mentah': []
    }
    
    # Ekstensi gambar yang valid
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    # Load gambar matang
    for img_file in matang_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            dataset['matang'].append((str(img_file), 'MATANG'))
    
    # Load gambar mentah
    for img_file in mentah_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            dataset['mentah'].append((str(img_file), 'MENTAH'))
    
    # Print summary
    print(f"Dataset loaded:")
    print(f"  - MATANG: {len(dataset['matang'])} gambar")
    print(f"  - MENTAH: {len(dataset['mentah'])} gambar")
    print(f"  - Total: {len(dataset['matang']) + len(dataset['mentah'])} gambar")
    
    return dataset


def split_dataset(dataset, train_ratio=0.7, random_seed=42):
    """
    Split dataset menjadi training dan testing set (70/30)
    Implementasi manual tanpa sklearn
    
    Parameters:
    -----------
    dataset : dict
        Dictionary berisi list gambar untuk setiap kelas
    train_ratio : float
        Rasio data training (default: 0.7 untuk 70%)
    random_seed : int
        Random seed untuk reproducibility
    
    Returns:
    --------
    tuple : (train_set, test_set)
        train_set : list - List of (image_path, label) untuk training
        test_set : list - List of (image_path, label) untuk testing
    """
    
    # Set random seed untuk reproducibility
    random.seed(random_seed)
    
    train_set = []
    test_set = []
    
    # Split untuk setiap kelas
    for class_name, images in dataset.items():
        # Shuffle gambar
        shuffled_images = images.copy()
        random.shuffle(shuffled_images)
        
        # Hitung jumlah data training
        n_train = int(len(shuffled_images) * train_ratio)
        
        # Split
        train_images = shuffled_images[:n_train]
        test_images = shuffled_images[n_train:]
        
        # Tambahkan ke set
        train_set.extend(train_images)
        test_set.extend(test_images)
    
    # Shuffle lagi untuk mencampur kelas
    random.shuffle(train_set)
    random.shuffle(test_set)
    
    print(f"\nDataset split:")
    print(f"  - Training: {len(train_set)} gambar ({train_ratio*100:.0f}%)")
    print(f"  - Testing: {len(test_set)} gambar ({(1-train_ratio)*100:.0f}%)")
    
    return train_set, test_set


def test_accuracy(test_set, centroid_matang, centroid_mentah, distance_threshold, confidence_threshold, verbose=False):
    """
    Hitung akurasi klasifikasi pada test set
    Implementasi manual tanpa sklearn
    
    Parameters:
    -----------
    test_set : list
        List of (image_path, label) untuk testing
    centroid_matang : numpy.ndarray
        Centroid untuk kelas MATANG
    centroid_mentah : numpy.ndarray
        Centroid untuk kelas MENTAH
    distance_threshold : float
        Threshold untuk jarak maksimum ke centroid
    confidence_threshold : float
        Threshold untuk confidence minimum
    verbose : bool
        Jika True, tampilkan detail setiap prediksi
    
    Returns:
    --------
    dict : Dictionary berisi metrik akurasi
        {
            'accuracy': float,
            'correct': int,
            'total': int,
            'confusion_matrix': dict
        }
    """
    
    correct = 0
    total = len(test_set)
    
    # Confusion matrix: {true_label: {predicted_label: count}}
    confusion_matrix = {
        'MATANG': {'MATANG': 0, 'MENTAH': 0, 'TIDAK YAKIN': 0},
        'MENTAH': {'MATANG': 0, 'MENTAH': 0, 'TIDAK YAKIN': 0}
    }
    
    print(f"\nTesting klasifikasi pada {total} gambar...")
    print("=" * 80)
    
    # Test setiap gambar
    for i, (image_path, true_label) in enumerate(test_set, 1):
        try:
            # Load gambar menggunakan OpenCV
            image = cv2.imread(image_path)
            if image is None:
                print(f"[{i}/{total}] SKIP: Gagal load {os.path.basename(image_path)}")
                total -= 1  # Kurangi total karena gambar tidak valid
                continue
            
            # Segmentasi mangga menggunakan K-Means (k=2)
            mask, _, _ = create_kmeans_mask(image)
            
            # Ekstraksi fitur RGB dan HSV dengan mask
            rgb_values = extract_rgb_features(image, mask)
            hsv_values = extract_hsv_features(image, mask)
            
            # Klasifikasi menggunakan MDC dengan threshold
            predicted_label, confidence, dist_matang, dist_mentah = classify_mango_mdc(
                rgb_values,
                hsv_values,
                centroid_matang,
                centroid_mentah,
                distance_threshold,
                confidence_threshold
            )
            
            # Cek apakah prediksi benar
            is_correct = (predicted_label == true_label)
            if is_correct:
                correct += 1
            
            # Update confusion matrix
            confusion_matrix[true_label][predicted_label] += 1
            
            # Print detail jika verbose
            if verbose:
                status = "✓ BENAR" if is_correct else "✗ SALAH"
                print(f"[{i}/{total}] {status} | True: {true_label:12s} | Pred: {predicted_label:12s} | Conf: {confidence:5.1f}% | {os.path.basename(image_path)}")
        
        except Exception as e:
            print(f"[{i}/{total}] ERROR: {os.path.basename(image_path)} - {str(e)}")
            total -= 1  # Kurangi total karena error
    
    # Hitung akurasi
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print("=" * 80)
    print(f"\nHasil Testing:")
    print(f"  - Benar: {correct}/{total}")
    print(f"  - Akurasi: {accuracy:.2f}%")
    
    # Print confusion matrix
    print(f"\nConfusion Matrix:")
    print(f"{'':15s} | {'Pred: MATANG':14s} | {'Pred: MENTAH':14s} | {'Pred: TIDAK YAKIN':18s}")
    print("-" * 70)
    print(f"{'True: MATANG':15s} | {confusion_matrix['MATANG']['MATANG']:14d} | {confusion_matrix['MATANG']['MENTAH']:14d} | {confusion_matrix['MATANG']['TIDAK YAKIN']:18d}")
    print(f"{'True: MENTAH':15s} | {confusion_matrix['MENTAH']['MATANG']:14d} | {confusion_matrix['MENTAH']['MENTAH']:14d} | {confusion_matrix['MENTAH']['TIDAK YAKIN']:18d}")
    
    # Hitung precision dan recall untuk setiap kelas (exclude TIDAK YAKIN)
    print(f"\nMetrik per Kelas:")
    
    # MATANG
    tp_matang = confusion_matrix['MATANG']['MATANG']
    fp_matang = confusion_matrix['MENTAH']['MATANG']
    fn_matang = confusion_matrix['MATANG']['MENTAH']
    
    precision_matang = (tp_matang / (tp_matang + fp_matang) * 100) if (tp_matang + fp_matang) > 0 else 0
    recall_matang = (tp_matang / (tp_matang + fn_matang) * 100) if (tp_matang + fn_matang) > 0 else 0
    
    print(f"  MATANG:")
    print(f"    - Precision: {precision_matang:.2f}%")
    print(f"    - Recall: {recall_matang:.2f}%")
    
    # MENTAH
    tp_mentah = confusion_matrix['MENTAH']['MENTAH']
    fp_mentah = confusion_matrix['MATANG']['MENTAH']
    fn_mentah = confusion_matrix['MENTAH']['MATANG']
    
    precision_mentah = (tp_mentah / (tp_mentah + fp_mentah) * 100) if (tp_mentah + fp_mentah) > 0 else 0
    recall_mentah = (tp_mentah / (tp_mentah + fn_mentah) * 100) if (tp_mentah + fn_mentah) > 0 else 0
    
    print(f"  MENTAH:")
    print(f"    - Precision: {precision_mentah:.2f}%")
    print(f"    - Recall: {recall_mentah:.2f}%")
    
    # Count TIDAK YAKIN predictions
    tidak_yakin_count = confusion_matrix['MATANG']['TIDAK YAKIN'] + confusion_matrix['MENTAH']['TIDAK YAKIN']
    print(f"\n  TIDAK YAKIN predictions: {tidak_yakin_count}/{total} ({tidak_yakin_count/total*100:.2f}%)")
    
    return {
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'confusion_matrix': confusion_matrix,
        'precision_matang': precision_matang,
        'recall_matang': recall_matang,
        'precision_mentah': precision_mentah,
        'recall_mentah': recall_mentah,
        'tidak_yakin_count': tidak_yakin_count
    }


def run_test(dataset_path="dataset", train_ratio=0.7, random_seed=42, verbose=False, centroids_path="centroids.json"):
    """
    Fungsi utama untuk menjalankan testing
    
    Parameters:
    -----------
    dataset_path : str
        Path ke folder dataset
    train_ratio : float
        Rasio data training (default: 0.7)
    random_seed : int
        Random seed untuk reproducibility
    verbose : bool
        Jika True, tampilkan detail setiap prediksi
    centroids_path : str
        Path ke file centroids.json (default: "centroids.json")
    
    Returns:
    --------
    dict : Dictionary berisi metrik akurasi
    """
    from .classifier import load_centroids
    
    print("=" * 80)
    print("TESTING AKURASI KLASIFIKASI MANGO")
    print("=" * 80)
    
    # Load centroids dan thresholds
    print(f"\nLoading centroids dari {centroids_path}...")
    centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = load_centroids(centroids_path)
    print(f"✓ Centroids loaded")
    print(f"  - Distance threshold: {distance_threshold:.4f}")
    print(f"  - Confidence threshold: {confidence_threshold:.2f}%")
    
    # Load dataset
    dataset = load_dataset_images(dataset_path)
    
    # Split dataset
    train_set, test_set = split_dataset(dataset, train_ratio=train_ratio, random_seed=random_seed)
    
    # Test akurasi
    results = test_accuracy(test_set, centroid_matang, centroid_mentah, distance_threshold, confidence_threshold, verbose=verbose)
    
    print("\n" + "=" * 80)
    print("TESTING SELESAI")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    # Jalankan testing dengan verbose=True untuk melihat detail
    # Path relatif dari root project
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset")
    
    results = run_test(
        dataset_path=dataset_path,
        train_ratio=0.7,
        random_seed=42,
        verbose=True  # Set False untuk output ringkas
    )
