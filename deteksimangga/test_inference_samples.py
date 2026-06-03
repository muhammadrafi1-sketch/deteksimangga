"""
Quick test script untuk threshold-based classifier tanpa GUI
"""

import cv2
from pathlib import Path
from leaf_identifier.image_processor import resize_image, extract_rgb_features, extract_hsv_features, create_kmeans_mask
from leaf_identifier.classifier import classify_mango_mdc, load_centroids

def test_sample(image_path, expected_class):
    """Test single image and return result"""
    print(f"\nTesting: {image_path}")
    print(f"Expected: {expected_class}")
    
    # Load centroids
    centroid_matang, centroid_mentah, distance_threshold, confidence_threshold = load_centroids('centroids.json')
    
    # Load and process image
    image = cv2.imread(str(image_path))
    resized_image = resize_image(image, target_width=800)
    
    # Segmentation
    mask, masked_image, clustered_image = create_kmeans_mask(resized_image)
    
    # Feature extraction
    rgb_features = extract_rgb_features(resized_image, mask)
    hsv_features = extract_hsv_features(resized_image, mask)
    
    # Classification
    result, confidence, distance_matang, distance_mentah = classify_mango_mdc(
        rgb_features, 
        hsv_features,
        centroid_matang,
        centroid_mentah,
        distance_threshold,
        confidence_threshold
    )
    
    # Check correctness
    correct = "✓" if result == expected_class or result == "TIDAK YAKIN" else "✗"
    
    print(f"Result: {result} ({confidence:.1f}%)")
    print(f"Status: {correct}")
    
    return result, confidence, result == expected_class or result == "TIDAK YAKIN"

def main():
    """Test multiple samples"""
    dataset_path = Path("leaf_identifier/dataset")
    
    test_cases = [
        (dataset_path / "matang" / "matang (1).jpg", "MATANG"),
        (dataset_path / "matang" / "matang (5).jpg", "MATANG"),
        (dataset_path / "matang" / "143.jpg", "MATANG"),  # Low confidence case
        (dataset_path / "mentah" / "mentah (2).jpg", "MENTAH"),
        (dataset_path / "mentah" / "mentah (5).jpg", "MENTAH"),
        (dataset_path / "mentah" / "mentah (10).jpg", "MENTAH"),
    ]
    
    print("="*60)
    print("THRESHOLD-BASED CLASSIFIER TEST")
    print("="*60)
    
    results = []
    for image_path, expected in test_cases:
        if image_path.exists():
            result, confidence, correct = test_sample(image_path, expected)
            results.append((image_path.name, expected, result, confidence, correct))
        else:
            print(f"\nSkipping: {image_path} (not found)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    correct_count = sum(1 for r in results if r[4])
    total_count = len(results)
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\nTotal: {total_count}")
    print(f"Correct: {correct_count}")
    print(f"Accuracy: {accuracy:.2f}%")
    
    print("\nDetailed Results:")
    for name, expected, result, confidence, correct in results:
        status = "✓" if correct else "✗"
        print(f"  {status} {name:20s} | Expected: {expected:12s} | Got: {result:12s} ({confidence:.1f}%)")

if __name__ == "__main__":
    main()
