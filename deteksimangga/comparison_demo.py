"""
Mango Ripeness Comparison Demo
Menampilkan perbandingan MATANG vs MENTAH side-by-side
dengan K-Means mask, fitur RGB/HSV, dan hasil klasifikasi MDC
"""

import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from leaf_identifier.image_processor import (
    resize_image, create_kmeans_mask, extract_rgb_features, extract_hsv_features
)
from leaf_identifier.classifier import classify_mango_mdc, load_centroids


# ====================== CONFIG ======================
MATANG_SAMPLE = "leaf_identifier/dataset/matang/matang (1).jpg"
MENTAH_SAMPLE = "leaf_identifier/dataset/mentah/mentah (1).jpg"
OUTPUT_FILE = "comparison_result.png"
IMG_WIDTH = 400
# ====================================================


def process_image(image_path):
    """Load, segment, extract features, classify. Return all results."""
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Cannot read: {image_path}")

    resized = resize_image(image, target_width=IMG_WIDTH)
    mask, masked_img, clustered_img = create_kmeans_mask(resized)

    rgb = extract_rgb_features(resized, mask)
    hsv = extract_hsv_features(resized, mask)

    cent_m, cent_mh, dist_th, conf_th = load_centroids('centroids.json')
    result, confidence, d_matang, d_mentah = classify_mango_mdc(
        rgb, hsv, cent_m, cent_mh, dist_th, conf_th
    )

    return {
        'original': resized,
        'mask': mask,
        'masked': masked_img,
        'clustered': clustered_img,
        'rgb': rgb,
        'hsv': hsv,
        'result': result,
        'confidence': confidence,
        'd_matang': d_matang,
        'd_mentah': d_mentah,
    }


def put_text(img, text, pos, color=(255, 255, 255), bg=(0, 0, 0), scale=0.5, thick=1):
    """Draw text with background rectangle."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), bl = cv2.getTextSize(text, font, scale, thick)
    x, y = pos
    cv2.rectangle(img, (x, y - th - bl), (x + tw, y + bl), bg, -1)
    cv2.putText(img, text, (x, y), font, scale, color, thick, cv2.LINE_AA)


def make_info_panel(rgb, hsv, result, confidence, d_mat, d_ment, label, panel_w, panel_h):
    """Create a text information panel for one sample."""
    panel = np.ones((panel_h, panel_w, 3), dtype=np.uint8) * 245

    # Title
    color = (39, 174, 96) if result == "MENTAH" else (230, 126, 34)
    cv2.putText(panel, f"{label} - {result}", (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2, cv2.LINE_AA)

    y = 70
    lines = [
        f"Confidence: {confidence:.1f}%",
        f"Distance to MATANG: {d_mat:.2f}",
        f"Distance to MENTAH: {d_ment:.2f}",
        "",
        "--- RGB ---",
        f"  Red   : {rgb['mean_red']:.1f}",
        f"  Green : {rgb['mean_green']:.1f}",
        f"  Blue  : {rgb['mean_blue']:.1f}",
        "",
        "--- HSV ---",
        f"  Hue        : {hsv['mean_hue']:.1f}",
        f"  Saturation : {hsv['mean_saturation']:.1f}",
        f"  Value      : {hsv['mean_value']:.1f}",
    ]
    for line in lines:
        cv2.putText(panel, line, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1, cv2.LINE_AA)
        y += 28

    return panel


def draw_rgb_bar(panel, rgb, x, y, w, h):
    """Draw RGB bar chart showing normalized values."""
    max_val = 255
    colors_bgr = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
    labels = ['R', 'G', 'B']
    vals = [rgb['mean_red'], rgb['mean_green'], rgb['mean_blue']]
    bar_w = w // 3 - 10
    for i in range(3):
        bh = int((vals[i] / max_val) * (h - 20))
        bx = x + i * (w // 3) + 5
        by = y + h - bh - 10
        cv2.rectangle(panel, (bx, by), (bx + bar_w, y + h - 10), colors_bgr[i], -1)
        cv2.putText(panel, f"{labels[i]}={vals[i]:.0f}", (bx, by - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, colors_bgr[i], 1, cv2.LINE_AA)


def draw_hsv_bar(panel, hsv, x, y, w, h):
    """Draw HSV bar chart."""
    max_h = 179
    max_sv = 255
    colors = [(255, 100, 100), (100, 200, 100), (200, 200, 200)]
    labels = ['H', 'S', 'V']
    vals = [hsv['mean_hue'], hsv['mean_saturation'], hsv['mean_value']]
    maxes = [max_h, max_sv, max_sv]
    bar_w = w // 3 - 10
    for i in range(3):
        bh = int((vals[i] / maxes[i]) * (h - 20))
        bx = x + i * (w // 3) + 5
        by = y + h - bh - 10
        cv2.rectangle(panel, (bx, by), (bx + bar_w, y + h - 10), colors[i], -1)
        cv2.putText(panel, f"{labels[i]}={vals[i]:.0f}", (bx, by - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, colors[i], 1, cv2.LINE_AA)


def main():
    print("=" * 60)
    print("MANGO RIPENESS COMPARISON DEMO")
    print("MATANG vs MENTAH — K-Means + RGB/HSV + MDC")
    print("=" * 60)

    # Process both samples
    print("\n[1/2] Processing MATANG sample...")
    matang = process_image(MATANG_SAMPLE)

    print("[2/2] Processing MENTAH sample...")
    mentah = process_image(MENTAH_SAMPLE)

    # Resize all images to a consistent display height
    DISP_H = 300
    col_w = IMG_WIDTH

    def prep(img):
        if img.shape[0] != DISP_H:
            ratio = DISP_H / img.shape[0]
            return cv2.resize(img, (int(img.shape[1] * ratio), DISP_H))
        return img.copy()

    for data in [matang, mentah]:
        data['original'] = prep(data['original'])
        data['masked'] = prep(data['masked'])
        data['clustered'] = prep(data['clustered'])
        m = data['mask']
        data['mask'] = prep(cv2.cvtColor(m, cv2.COLOR_GRAY2BGR) if len(m.shape) == 2 else m)

    h = DISP_H

    # --- Build the comparison canvas ---
    gap = 10
    title_h = 50
    bar_h = 120
    info_h = 300
    total_w = col_w * 2 + gap * 3
    total_h = title_h + h * 4 + gap * 5 + bar_h * 2 + info_h

    canvas = np.ones((total_h, total_w, 3), dtype=np.uint8) * 255

    def place(img, row, col):
        x = gap + col * (col_w + gap)
        y = title_h + row * (h + gap)
        rh, rw = img.shape[:2]
        cx = x + (col_w - rw) // 2
        canvas[y:y+rh, cx:cx+rw] = img[:rh, :rw]

    # Row labels
    row_labels = ["Original Image", "K-Means Mask (binary)", "K-Means Clustered", "Masked Mango"]
    for i, lbl in enumerate(row_labels):
        y = title_h + i * (h + gap) + h // 2
        cv2.putText(canvas, lbl, (gap, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (120, 120, 120), 1, cv2.LINE_AA)

    # Column headers
    for ci, (data, label) in enumerate([(matang, "MATANG"), (mentah, "MENTAH")]):
        cx = gap + ci * (col_w + gap) + col_w // 2 - 50
        color = (39, 174, 96) if label == "MENTAH" else (230, 126, 34)
        cv2.putText(canvas, f"--- {label} ---", (cx, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

    # Place images
    for ci, data in enumerate([matang, mentah]):
        place(data['original'], 0, ci)
        place(data['mask'], 1, ci)
        place(data['clustered'], 2, ci)
        place(data['masked'], 3, ci)

    # --- Bar Charts Section ---
    bar_y = title_h + 4 * (h + gap) + gap
    bar_y2 = bar_y + bar_h + gap

    # RGB bars
    cv2.putText(canvas, "RGB Comparison", (gap, bar_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 200), 1, cv2.LINE_AA)
    draw_rgb_bar(canvas, matang['rgb'], gap + 5, bar_y + 28, col_w - 10, bar_h - 38)
    draw_rgb_bar(canvas, mentah['rgb'], col_w + gap + 5, bar_y + 28, col_w - 10, bar_h - 38)

    # HSV bars
    cv2.putText(canvas, "HSV Comparison", (gap, bar_y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 200), 1, cv2.LINE_AA)
    draw_hsv_bar(canvas, matang['hsv'], gap + 5, bar_y2 + 28, col_w - 10, bar_h - 38)
    draw_hsv_bar(canvas, mentah['hsv'], col_w + gap + 5, bar_y2 + 28, col_w - 10, bar_h - 38)

    # --- Info Panel Section ---
    info_y = bar_y2 + bar_h + gap
    cv2.putText(canvas, "Classification Details", (gap, info_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 50), 1, cv2.LINE_AA)

    info_h_actual = total_h - info_y - gap
    matang_panel = make_info_panel(
        matang['rgb'], matang['hsv'], matang['result'], matang['confidence'],
        matang['d_matang'], matang['d_mentah'], "MATANG", col_w, info_h_actual
    )
    mentah_panel = make_info_panel(
        mentah['rgb'], mentah['hsv'], mentah['result'], mentah['confidence'],
        mentah['d_matang'], mentah['d_mentah'], "MENTAH", col_w, info_h_actual
    )

    canvas[info_y:info_y+info_h_actual, gap:gap+col_w] = matang_panel[:info_h_actual, :col_w]
    canvas[info_y:info_y+info_h_actual, gap+col_w+gap:gap+col_w+gap+col_w] = mentah_panel[:info_h_actual, :col_w]

    # Save
    cv2.imwrite(OUTPUT_FILE, canvas)
    print(f"\n{'=' * 60}")
    print(f"COMPARISON RESULT SAVED: {OUTPUT_FILE}")
    print(f"{'=' * 60}")

    # Terminal summary
    print(f"\n{'=' * 60}")
    print("TERMINAL SUMMARY")
    print(f"{'=' * 60}")
    for label, data in [("MATANG", matang), ("MENTAH", mentah)]:
        print(f"\n--- {label} ---")
        print(f"  Result: {data['result']} ({data['confidence']:.1f}%)")
        print(f"  RGB: R={data['rgb']['mean_red']:.1f}  G={data['rgb']['mean_green']:.1f}  B={data['rgb']['mean_blue']:.1f}")
        print(f"  HSV: H={data['hsv']['mean_hue']:.1f}  S={data['hsv']['mean_saturation']:.1f}  V={data['hsv']['mean_value']:.1f}")
        print(f"  Distance to MATANG centroid: {data['d_matang']:.2f}")
        print(f"  Distance to MENTAH centroid: {data['d_mentah']:.2f}")

    # Show image
    print(f"\nDisplaying comparison (press any key to close)...")
    cv2.namedWindow("Mango Ripeness Comparison", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Mango Ripeness Comparison", 1200, 800)
    cv2.imshow("Mango Ripeness Comparison", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\nDone!")


if __name__ == "__main__":
    main()
