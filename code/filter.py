#!/usr/bin/env python3
"""
Filtering and selection pipeline (Algorithm 1).
------------------------------------------------
For each image:
  1. Discard if min(w,h) < TAU_RES
  2. Discard if mean luminance < TAU_LIGHT
  3. Discard if prediction is refusal / empty / non-parsable
  4. Discard if lat ∉ [-90,90] or lon ∉ [-180,180]
  5. Otherwise keep
"""

import csv
import os
import re
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

# ============================================================================
# CONFIGURATION — edit these paths and thresholds
# ============================================================================


INPUT_CSV = r" "


OUTPUT_CSV = r" "


IMAGE_ROOTS = [
    r" ", # image path to scan through
]

# Thresholds
TAU_RES = 224       
TAU_LIGHT = 0.15     

REFUSAL_KEYWORDS = [
    "i cannot", "i'm unable", "unable to", "cannot determine",
    "not visible", "no information", "unknown", "not available",
    "sorry", "i apologize",
]

# ============================================================================
# HELPERS
# ============================================================================


def build_image_index(roots):
    """Walk *roots* recursively, returning {filename: full_path} for all images."""
    index = {}
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if os.path.splitext(fname)[1].lower() in exts:
                    index[fname] = os.path.join(dirpath, fname)
    return index


def check_image(image_path: str) -> Tuple[bool, str]:
    """
    Return (pass, reason).
    pass=True if resolution >= TAU_RES and luminance >= TAU_LIGHT.
    """
    try:
        img = Image.open(image_path)
        w, h = img.size
    except Exception as exc:
        return False, f"image_load_error: {exc}"

    if min(w, h) < TAU_RES:
        return False, f"low_resolution ({w}x{h}, min={min(w,h)} < {TAU_RES})"

    # Normalised luminance Y = 0.299R + 0.587G + 0.114B, range [0,1]
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    Y = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    mean_lum = float(np.mean(Y))

    if mean_lum < TAU_LIGHT:
        return False, f"too_dark (mean_luminance={mean_lum:.4f} < {TAU_LIGHT})"

    return True, "ok"


def check_prediction(row) -> Tuple[bool, str]:
    """
    Return (pass, reason).
    Check refusal, empty, non-parsable, and coordinate range.
    """
    lat_str = row.get("latitude", "").strip()
    lon_str = row.get("longitude", "").strip()

    # --- empty check ---
    if not lat_str or not lon_str:
        return False, "empty_prediction"

    # --- refusal check (scan all fields) ---
    for val in row.values():
        if not isinstance(val, str):
            continue
        for kw in REFUSAL_KEYWORDS:
            if kw in val.lower():
                return False, f"refusal_keyword: '{kw}'"

    # --- parseability + range check ---
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        return False, "non_parsable_coordinates"

    if not (-90 <= lat <= 90):
        return False, f"latitude_out_of_range ({lat})"
    if not (-180 <= lon <= 180):
        return False, f"longitude_out_of_range ({lon})"

    return True, "ok"


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("Building image index ...")
    img_index = build_image_index(IMAGE_ROOTS)
    print(f"  indexed {len(img_index)} images from {len(IMAGE_ROOTS)} root(s)")

    print(f"Loading: {INPUT_CSV}")
    with open(INPUT_CSV, "r", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    in_fields = reader.fieldnames or []
    print(f"  {len(all_rows)} rows loaded")

    kept = []
    stats = {
        "total": len(all_rows),
        "kept": 0,
        "image_not_found": 0,
        "low_resolution": 0,
        "too_dark": 0,
        "empty_prediction": 0,
        "refusal": 0,
        "non_parsable": 0,
        "coord_out_of_range": 0,
        "image_load_error": 0,
    }

    for i, row in enumerate(all_rows):
        fname = row.get("filename", "").strip()
        if not fname:
            stats["image_not_found"] += 1
            continue

        img_path = img_index.get(fname)
        if img_path is None:
            stats["image_not_found"] += 1
            continue

        # --- image checks ---
        ok, reason = check_image(img_path)
        if not ok:
            cat = reason.split(":")[0] if ":" in reason else reason
            cat = cat.replace(" ", "_")
            stats[cat] = stats.get(cat, 0) + 1
            continue

        # --- prediction checks ---
        ok, reason = check_prediction(row)
        if not ok:
            cat = reason.split(":")[0] if ":" in reason else reason
            cat = cat.replace(" ", "_")
            stats[cat] = stats.get(cat, 0) + 1
            continue

        kept.append(row)
        stats["kept"] += 1

    # --- write output ---
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=in_fields)
        writer.writeheader()
        writer.writerows(kept)

    # --- report ---
    print("\n" + "=" * 55)
    print("FILTERING REPORT")
    print("=" * 55)
    for key, val in sorted(stats.items()):
        pct = val / stats["total"] * 100 if stats["total"] else 0
        bar = "█" * int(pct / 2)
        print(f"  {key:<22s} {val:>5d}  ({pct:5.1f}%)  {bar}")
    print("=" * 55)
    print(f"Output: {OUTPUT_CSV}")
    print(f"Rows kept: {stats['kept']} / {stats['total']}")


if __name__ == "__main__":
    main()