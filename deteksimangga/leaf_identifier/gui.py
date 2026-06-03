"""
GUI Module
Tkinter GUI untuk aplikasi deteksi kematangan mangga menggunakan K-Means clustering
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from .image_processor import (
    resize_image, 
    create_kmeans_mask,
    extract_rgb_features,
    extract_hsv_features
)
from .classifier import classify_mango_mdc, load_centroids


class MangoRipenessGUI:
    """
    Class untuk GUI aplikasi deteksi kematangan mangga
    """
    
    def __init__(self, root):
        """
        Inisialisasi GUI
        
        Parameters:
        -----------
        root : tk.Tk
            Root window Tkinter
        """
        self.root = root
        self.root.title("Deteksi Kematangan Mangga")
        self.root.geometry("1280x720")
        self.root.resizable(False, False)
        
        # Variable untuk menyimpan gambar
        self.current_image = None
        self.current_image_path = None
        
        # Load centroids untuk Minimum Distance Classifier
        try:
            self.centroid_matang, self.centroid_mentah, self.distance_threshold, self.confidence_threshold = load_centroids('centroids.json')
        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                "File centroids.json tidak ditemukan!\n\n"
                "Jalankan training terlebih dahulu:\n"
                "python -m leaf_identifier.train_classifier"
            )
            self.root.destroy()
            return
        
        # Setup GUI components
        self.setup_gui()
    
    def setup_gui(self):
        """
        Setup semua komponen GUI
        """
        # Title
        title_label = tk.Label(
            self.root,
            text="🥭 Deteksi Kematangan Mangga",
            font=("Arial", 18, "bold"),
            bg="#f39c12",
            fg="white",
            pady=10
        )
        title_label.pack(fill=tk.X)
        
        # Frame untuk preview gambar (side-by-side: original | mask)
        image_frame = tk.Frame(self.root, bg="#ecf0f1", pady=5)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Container untuk dua gambar
        images_container = tk.Frame(image_frame, bg="#ecf0f1")
        images_container.pack()
        
        # Frame kiri: Original Image
        left_frame = tk.Frame(images_container, bg="#ecf0f1")
        left_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            left_frame,
            text="Original Image",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack()
        
        self.image_label = tk.Label(
            left_frame,
            text="Belum ada gambar\ndipilih",
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#7f8c8d",
            relief=tk.SUNKEN,
            bd=2
        )
        self.image_label.pack(pady=5, padx=10)
        
        # Frame kanan: Mask Preview
        right_frame = tk.Frame(images_container, bg="#ecf0f1")
        right_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            right_frame,
            text="Mango Mask (K-Means)",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack()
        
        self.mask_label = tk.Label(
            right_frame,
            text="Mask akan muncul\ndi sini",
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#7f8c8d",
            relief=tk.SUNKEN,
            bd=2
        )
        self.mask_label.pack(pady=5, padx=10)
        
        # Tombol Upload
        upload_button = tk.Button(
            self.root,
            text="📁 Upload Gambar Mangga",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.upload_image
        )
        upload_button.pack(pady=10)
        
        # Frame untuk informasi RGB dan HSV
        info_frame = tk.Frame(self.root, bg="white")
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Frame RGB
        rgb_frame = tk.LabelFrame(
            info_frame,
            text="Informasi RGB",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2c3e50",
            padx=10,
            pady=5
        )
        rgb_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.rgb_red_label = tk.Label(rgb_frame, text="Red: -", font=("Arial", 10), bg="white", anchor="w")
        self.rgb_red_label.pack(fill=tk.X, pady=2)
        
        self.rgb_green_label = tk.Label(rgb_frame, text="Green: -", font=("Arial", 10), bg="white", anchor="w")
        self.rgb_green_label.pack(fill=tk.X, pady=2)
        
        self.rgb_blue_label = tk.Label(rgb_frame, text="Blue: -", font=("Arial", 10), bg="white", anchor="w")
        self.rgb_blue_label.pack(fill=tk.X, pady=2)
        
        # Frame HSV
        hsv_frame = tk.LabelFrame(
            info_frame,
            text="Informasi HSV",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2c3e50",
            padx=10,
            pady=5
        )
        hsv_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.hsv_hue_label = tk.Label(hsv_frame, text="Hue: -", font=("Arial", 10), bg="white", anchor="w")
        self.hsv_hue_label.pack(fill=tk.X, pady=2)
        
        self.hsv_saturation_label = tk.Label(hsv_frame, text="Saturation: -", font=("Arial", 10), bg="white", anchor="w")
        self.hsv_saturation_label.pack(fill=tk.X, pady=2)
        
        self.hsv_value_label = tk.Label(hsv_frame, text="Value: -", font=("Arial", 10), bg="white", anchor="w")
        self.hsv_value_label.pack(fill=tk.X, pady=2)
        
        # Configure grid weights untuk responsive
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        
        # Frame untuk hasil deteksi
        result_frame = tk.Frame(self.root, bg="white", pady=5)
        result_frame.pack(fill=tk.X, padx=20, pady=5)
        
        result_title = tk.Label(
            result_frame,
            text="HASIL DETEKSI KEMATANGAN",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        result_title.pack()
        
        self.result_label = tk.Label(
            result_frame,
            text="-",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#27ae60",
            pady=5
        )
        self.result_label.pack()
        
        # Label untuk confidence score
        self.confidence_label = tk.Label(
            result_frame,
            text="Confidence: -",
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d",
            pady=3
        )
        self.confidence_label.pack()
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Status: Siap",
            font=("Arial", 9),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def upload_image(self):
        """
        Handler untuk upload gambar mangga
        """
        # Buka file dialog
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar Mangga",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("PNG Files", "*.png"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Update status
        self.status_label.config(text="Status: Memproses gambar...")
        self.root.update()
        
        try:
            # Load gambar menggunakan OpenCV
            image = cv2.imread(file_path)
            
            if image is None:
                raise ValueError("Gagal membaca gambar")
            
            # Simpan gambar dan path
            self.current_image = image
            self.current_image_path = file_path
            
            # Resize untuk processing
            resized_image = resize_image(image, target_width=400)
            
            # Segmentasi mangga menggunakan K-Means (k=2)
            mask, masked_image, _ = create_kmeans_mask(resized_image)
            
            # Ekstraksi fitur warna RGB dengan K-Means masking
            rgb_features = extract_rgb_features(resized_image, mask)
            
            # Ekstraksi fitur warna HSV dengan K-Means masking
            hsv_features = extract_hsv_features(resized_image, mask)
            
            # Cek apakah mangga terdeteksi
            if rgb_features is None or hsv_features is None:
                # Mangga tidak terdeteksi
                self.display_image(file_path)
                self.display_mask(masked_image)
                self.clear_info()
                self.update_result("❌ Mangga tidak terdeteksi", 0.0)
                self.status_label.config(text="Status: Mangga tidak terdeteksi - coba gambar lain")
                return
            
            # Klasifikasi kematangan mangga menggunakan Minimum Distance Classifier
            # Mengembalikan tuple: (result, confidence, distance_matang, distance_mentah)
            result, confidence, dist_matang, dist_mentah = classify_mango_mdc(
                rgb_features, 
                hsv_features, 
                self.centroid_matang,
                self.centroid_mentah,
                self.distance_threshold,
                self.confidence_threshold
            )
            
            # Update GUI dengan hasil
            self.display_image(file_path)
            self.display_mask(masked_image)
            self.update_rgb_info(rgb_features)
            self.update_hsv_info(hsv_features)
            self.update_result(result, confidence)
            
            # Update status
            self.status_label.config(text=f"Status: Berhasil memproses - {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan:\n{str(e)}")
            self.status_label.config(text="Status: Error")
    
    def display_image(self, image_path):
        """
        Tampilkan preview gambar di GUI
        
        Parameters:
        -----------
        image_path : str
            Path ke file gambar
        """
        # Load gambar menggunakan PIL
        image = Image.open(image_path)
        
        # Resize untuk preview (maintain aspect ratio)
        max_width = 450
        max_height = 350
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert ke PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Update label and keep reference
        self.image_label.config(image=photo, text="")
        # Store reference in instance variable to prevent garbage collection
        self._current_photo = photo
    
    def display_mask(self, masked_image):
        """
        Tampilkan preview mask di GUI
        
        Parameters:
        -----------
        masked_image : numpy.ndarray
            Masked image dari create_kmeans_mask() (BGR format)
        """
        # Convert BGR ke RGB
        rgb_masked = cv2.cvtColor(masked_image, cv2.COLOR_BGR2RGB)
        
        # Convert numpy array ke PIL Image
        pil_image = Image.fromarray(rgb_masked)
        
        # Resize untuk preview (maintain aspect ratio)
        max_width = 450
        max_height = 350
        pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert ke PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # Update label and keep reference
        self.mask_label.config(image=photo, text="")
        # Store reference in instance variable to prevent garbage collection
        self._current_mask_photo = photo
    
    def clear_info(self):
        """
        Clear semua informasi RGB/HSV di GUI
        """
        self.rgb_red_label.config(text="Red: -")
        self.rgb_green_label.config(text="Green: -")
        self.rgb_blue_label.config(text="Blue: -")
        self.hsv_hue_label.config(text="Hue: -")
        self.hsv_saturation_label.config(text="Saturation: -")
        self.hsv_value_label.config(text="Value: -")
    
    def update_rgb_info(self, features):
        """
        Update informasi RGB di GUI
        
        Parameters:
        -----------
        features : dict
            Dictionary berisi mean_red, mean_green, mean_blue, mean_hue, mean_saturation, mean_value
        """
        self.rgb_red_label.config(text=f"Red: {features['mean_red']:.2f}")
        self.rgb_green_label.config(text=f"Green: {features['mean_green']:.2f}")
        self.rgb_blue_label.config(text=f"Blue: {features['mean_blue']:.2f}")
    
    def update_hsv_info(self, features):
        """
        Update informasi HSV di GUI
        
        Parameters:
        -----------
        features : dict
            Dictionary berisi mean_red, mean_green, mean_blue, mean_hue, mean_saturation, mean_value
        """
        self.hsv_hue_label.config(text=f"Hue: {features['mean_hue']:.2f}")
        self.hsv_saturation_label.config(text=f"Saturation: {features['mean_saturation']:.2f}")
        self.hsv_value_label.config(text=f"Value: {features['mean_value']:.2f}")
    
    def update_result(self, result, confidence):
        """
        Update hasil deteksi kematangan di GUI
        
        Parameters:
        -----------
        result : str
            Hasil klasifikasi ("MATANG", "MENTAH", atau "❌ Mangga tidak terdeteksi")
        confidence : float
            Confidence score (0-100%)
        """
        # Set warna berdasarkan hasil
        if "tidak terdeteksi" in result:
            color = "#95a5a6"  # Abu-abu untuk tidak terdeteksi
        elif result == "MATANG":
            color = "#e67e22"  # Orange untuk matang
        elif result == "MENTAH":
            color = "#27ae60"  # Hijau untuk mentah
        else:  # TIDAK YAKIN
            color = "#f39c12"  # Kuning untuk tidak yakin
        
        self.result_label.config(text=result, fg=color)
        
        # Update confidence label
        self.confidence_label.config(text=f"Confidence: {confidence}%")


def create_gui():
    """
    Fungsi untuk membuat dan menjalankan GUI
    """
    root = tk.Tk()
    app = MangoRipenessGUI(root)
    root.mainloop()
