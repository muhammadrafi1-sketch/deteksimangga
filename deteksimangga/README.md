# Mango Ripeness Detection System

Aplikasi desktop untuk deteksi kematangan mangga menggunakan **K-Means Clustering** dan ekstraksi fitur warna RGB/HSV.

## 🎯 Fitur Utama

- **K-Means Segmentation (k=2)**: Memisahkan mangga dari background secara otomatis
- **Color Feature Extraction**: Ekstraksi fitur RGB dan HSV dari area mangga yang tersegmentasi
- **Ripeness Classification**: Klasifikasi MATANG vs MENTAH menggunakan **Minimum Distance Classifier** (centroid-based)
- **GUI Application**: Interface desktop dengan Tkinter untuk upload dan preview hasil
- **Inference Script**: Script standalone untuk testing single image dengan OpenCV visualization
- **Feature Extraction Tool**: Script untuk ekstraksi fitur dari dataset dengan output tabel terminal

## 📋 Requirements

```
opencv-python>=4.8.0
numpy>=1.24.0
scikit-learn>=1.3.0
Pillow>=10.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

### 0. Training Classifier (REQUIRED - First Time Setup)

Sebelum menggunakan aplikasi, train classifier untuk menghitung centroids dari dataset:

```bash
python -m leaf_identifier.train_classifier
```

**Prasyarat:**
- Dataset harus tersedia di `dataset/matang/` dan `dataset/mentah/`
- Minimal 5-10 gambar per kelas untuk hasil optimal

**Output:**
- File `centroids.json` berisi centroid MATANG dan MENTAH
- Terminal menampilkan summary: jumlah gambar, nilai centroid [R,G,B,H,S,V]

**Catatan:** Training hanya perlu dilakukan sekali. Jalankan ulang jika dataset berubah.

### 1. GUI Application (Main)

Jalankan aplikasi desktop dengan GUI:

```bash
python -m leaf_identifier.main
```

**Cara Penggunaan:**
1. Klik tombol "📁 Upload Gambar Mangga"
2. Pilih file gambar mangga (.jpg, .jpeg, .png)
3. Aplikasi akan menampilkan:
   - Preview gambar original
   - Mask hasil K-Means segmentation
   - Fitur warna RGB (Red, Green, Blue)
   - Fitur warna HSV (Hue, Saturation, Value)
   - Hasil klasifikasi: **MATANG** atau **MENTAH**
   - Confidence score (%)

### 2. Feature Extraction (Script 1)

Ekstraksi fitur dari dataset untuk analisis:

```bash
python -m leaf_identifier.extract_features
```

**Output:**
- Tabel terminal dengan kolom: Filename, R, G, B, H, S, V
- Proses semua gambar di `dataset/matang/` dan `dataset/mentah/`
- Berguna untuk analisis distribusi fitur dan tuning threshold

### 3. Inference Script (Script 2)

Testing single image dengan visualisasi OpenCV:

```bash
python -m leaf_identifier.inference <path_to_image>
```

**Contoh:**
```bash
python -m leaf_identifier.inference test_images/mangga1.jpg
```

**Output:**
- Terminal: Hasil klasifikasi, confidence, dan nilai fitur RGB/HSV
- OpenCV Windows:
  - Original Image
  - K-Means Segmentation Mask
  - Annotated Result (bounding box + label MATANG/MENTAH)

## 🧠 How It Works

### 1. K-Means Segmentation (k=2)

```python
# Segmentasi mangga dari background menggunakan K-Means clustering
mask, masked_image = segment_mango_kmeans(image)
```

**Proses:**
- Reshape image menjadi array 2D (pixels × RGB channels)
- K-Means clustering dengan k=2 (2 cluster: mangga vs background)
- Pilih cluster terbesar sebagai mangga (asumsi: mangga adalah objek dominan)
- Generate binary mask untuk isolasi area mangga

### 2. Color Feature Extraction

```python
# Ekstraksi fitur RGB + HSV dari area mangga yang ter-mask
features = extract_color_features(image)
```

**Fitur yang diekstrak:**
- **RGB**: mean_red, mean_green, mean_blue (0-255)
- **HSV**: mean_hue (0-179), mean_saturation (0-255), mean_value (0-255)

**Catatan:** Hanya pixel di dalam mask yang digunakan untuk perhitungan rata-rata.

### 3. Ripeness Classification

```python
# Klasifikasi menggunakan Minimum Distance Classifier
result, dist_matang, dist_mentah = classify_mango_mdc(rgb_features, hsv_features, centroids)
```

**Minimum Distance Classifier (MDC):**

MDC adalah metode klasifikasi **pattern recognition** berbasis geometri, **BUKAN machine learning**.

**Cara Kerja:**
1. **Training Phase**: Hitung centroid (mean) untuk setiap kelas dari dataset
   - Centroid MATANG = rata-rata [R, G, B, H, S, V] dari semua gambar matang
   - Centroid MENTAH = rata-rata [R, G, B, H, S, V] dari semua gambar mentah

2. **Classification Phase**: Hitung jarak Euclidean dari input ke setiap centroid
   ```
   distance = sqrt((R1-R2)² + (G1-G2)² + (B1-B2)² + (H1-H2)² + (S1-S2)² + (V1-V2)²)
   ```

3. **Decision**: Pilih kelas dengan jarak terkecil (minimum distance)
   ```
   IF distance_to_matang < distance_to_mentah:
       → MATANG
   ELSE:
       → MENTAH
   ```

**Mengapa MDC, bukan ML?**
- MDC = statistical/geometric classifier (simple math: mean, distance)
- Tidak ada training iteratif, gradient descent, atau optimization
- Tidak ada model weights/parameters yang di-learn
- Hanya menghitung rata-rata dan jarak Euclidean

**Confidence Calculation:**
```python
# Confidence berdasarkan selisih jarak
total_dist = dist_matang + dist_mentah
if result == "MATANG":
    confidence = (dist_mentah / total_dist) * 100
else:
    confidence = (dist_matang / total_dist) * 100
```

Semakin besar selisih jarak, semakin tinggi confidence.

## 📁 Project Structure

```
leaf_identifier/
├── leaf_identifier/
│   ├── __init__.py
│   ├── main.py                    # Entry point GUI application
│   ├── gui.py                     # Tkinter GUI implementation
│   ├── image_processor.py         # K-Means segmentation + feature extraction
│   ├── classifier.py              # MDC classifier + training logic
│   ├── config_loader.py           # JSON config loader
│   ├── train_classifier.py        # Training script: generate centroids
│   ├── extract_features.py        # Script 1: Dataset feature extraction
│   ├── inference.py               # Script 2: Single image inference
│   ├── centroids.json             # Trained centroids (generated by train_classifier.py)
│   └── dataset/
│       ├── matang/                # Ripe mango images (training data)
│       └── mentah/                # Unripe mango images (training data)
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Centroids File (`centroids.json`)

File ini di-generate otomatis oleh `train_classifier.py` dan berisi centroid untuk setiap kelas:

```json
{
    "matang": [R, G, B, H, S, V],
    "mentah": [R, G, B, H, S, V]
}
```

**Contoh:**
```json
{
    "matang": [180.5, 120.3, 45.2, 15.8, 180.0, 200.5],
    "mentah": [90.2, 150.8, 80.5, 85.3, 120.0, 180.2]
}
```

**Kapan perlu re-train:**
- Dataset berubah (gambar ditambah/dihapus)
- Akurasi klasifikasi menurun
- Kondisi pencahayaan dataset berubah signifikan

**Cara re-train:**
```bash
python -m leaf_identifier.train_classifier
```

## 🎨 Color Space Explanation

### RGB (Red, Green, Blue)
- **Range**: 0-255 per channel
- **Usage**: Komponen warna dasar untuk perhitungan jarak Euclidean dalam MDC

### HSV (Hue, Saturation, Value)
- **Hue**: 0-179 (OpenCV scale) - Warna dasar (0=Red, 30=Yellow, 60=Green, 120=Cyan, 150=Blue)
- **Saturation**: 0-255 - Intensitas warna (0=grayscale, 255=vivid)
- **Value**: 0-255 - Brightness (0=black, 255=bright)
- **Usage**: Hue menangkap transisi hijau → kuning/orange (kematangan), digunakan dalam perhitungan jarak MDC

## 📊 Example Output

### Terminal (extract_features.py):
```
=============================================================
FEATURE EXTRACTION - MANGO RIPENESS DATASET
=============================================================

Processing dataset/matang/...
Processing dataset/mentah/...

=============================================================
FEATURE SUMMARY
=============================================================
Filename              R       G       B       H       S       V
-------------------------------------------------------------
mangga_matang_1.jpg   180.5   120.3   45.2    25.3    180.1   180.5
mangga_mentah_1.jpg   80.2    140.5   60.1    65.8    150.2   140.5
...
=============================================================
```

### OpenCV Window (inference.py):
- Bounding box hijau (MENTAH) atau orange (MATANG)
- Label: "MATANG (dist: 45.2)" atau "MENTAH (dist: 38.7)" dengan confidence %
- 3 windows: Original, Mask, Annotated Result

## 🐛 Troubleshooting

**"Mangga tidak terdeteksi":**
- Pastikan mangga adalah objek terbesar di gambar
- Background terlalu kompleks → crop gambar lebih dekat
- Lighting terlalu gelap/terang → adjust exposure

**Klasifikasi tidak akurat:**
- Re-train classifier: `python -m leaf_identifier.train_classifier`
- Pastikan dataset memiliki cukup sample (minimal 5-10 per kelas)
- Periksa kualitas gambar dataset (lighting, focus, background)
- Jalankan `extract_features.py` untuk analisis distribusi fitur

**Import error:**
- Pastikan menjalankan dari root directory project
- Gunakan `python -m leaf_identifier.main` bukan `python leaf_identifier/main.py`

## 📝 License

ENOWX-64LQ3-S6SMF-8TH2V-VHHIE

## 👨‍💻 Development

**Tech Stack:**
- Python 3.8+
- OpenCV (cv2) - Image processing
- scikit-learn - K-Means clustering
- NumPy - Array operations
- Tkinter - GUI framework
- Pillow (PIL) - Image loading for GUI

**Key Algorithms:**
- K-Means Clustering (k=2) untuk segmentasi
- Color space conversion (RGB → HSV)
- Minimum Distance Classifier (centroid-based pattern recognition)

---

**Developed for Digital Image Processing Course**
