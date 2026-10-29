#!/usr/bin/env python3
"""
Ablation preprocessing script:
- Randomly sample N images from an input directory
- For each sampled image, create 3 "resolution degradation" variants via
  downsample -> upsample (same final size as original)
- Save into separate output directories (one per degradation level)
- Copy originals of the sampled set into an "original" directory for convenience

All paths and settings are editable in the CONFIG section.

Dependencies:
  pip install pillow
"""

from __future__ import annotations

import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

from PIL import Image, ImageOps

# ----------------------------
# CONFIG (EDIT THESE)
# ----------------------------

@dataclass
class Config:
    # Input directory containing images (can include subfolders if RECURSIVE=True)
    input_dir: Path = Path(r"D:\proj\lvlm\ablation_resolution")

    # Base output directory where processed images will be written
    output_base_dir: Path = Path(r"D:\proj\lvlm\ablation_resolution\downplayed")

    # Sampling
    sample_size: int = 100
    seed: int = 42
    recursive: bool = False  # if True, scans subdirectories too

    # What file extensions to treat as images
    exts: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")

    # Degradation settings:
    # Three levels defined by downsampling the *short side* to these pixel sizes,
    # then upsampling back to the original resolution.
    degrade_short_sides: Tuple[int, int, int] = (512, 256, 128)

    # Interpolation
    downsample_resample: int = Image.Resampling.BOX       # good for downsample (anti-alias)
    upsample_resample: int = Image.Resampling.BICUBIC     # common for upsample

    # Output format:
    # If None -> keep original extension; else force to ".jpg" or ".png"
    force_ext: Optional[str] = None  # e.g., ".jpg"

    # Only used if saving JPEG
    jpeg_quality: int = 95
    jpeg_optimize: bool = True
    jpeg_subsampling: int = 0  # 0=4:4:4 highest quality

    # If True, fixes EXIF orientation before resizing/saving
    exif_transpose: bool = True

CONFIG = Config()

# ----------------------------
# HELPERS
# ----------------------------

def list_images(input_dir: Path, exts: Tuple[str, ...], recursive: bool) -> List[Path]:
    if recursive:
        files = [p for p in input_dir.rglob("*") if p.is_file()]
    else:
        files = [p for p in input_dir.glob("*") if p.is_file()]

    exts_lower = set(e.lower() for e in exts)
    imgs = [p for p in files if p.suffix.lower() in exts_lower]
    return sorted(imgs)

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def compute_downsample_size_keep_aspect(w: int, h: int, short_side: int) -> Tuple[int, int]:
    # Keep aspect ratio; set min(w,h) to short_side
    if w <= 0 or h <= 0:
        raise ValueError(f"Invalid image size: {w}x{h}")

    if min(w, h) == short_side:
        return (w, h)

    if w <= h:
        new_w = short_side
        new_h = round(h * (short_side / w))
    else:
        new_h = short_side
        new_w = round(w * (short_side / h))

    new_w = max(1, int(new_w))
    new_h = max(1, int(new_h))
    return new_w, new_h

def save_image(img: Image.Image, out_path: Path, cfg: Config) -> None:
    safe_mkdir(out_path.parent)

    ext = out_path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        img.save(
            out_path,
            quality=cfg.jpeg_quality,
            optimize=cfg.jpeg_optimize,
            subsampling=cfg.jpeg_subsampling,
        )
    else:
        img.save(out_path)

def choose_output_path(in_path: Path, out_dir: Path, cfg: Config) -> Path:
    # Preserve filename; optionally force extension
    name = in_path.stem
    ext = cfg.force_ext if cfg.force_ext else in_path.suffix
    return out_dir / f"{name}{ext}"

def copy_original(in_path: Path, out_dir: Path, cfg: Config) -> None:
    out_path = choose_output_path(in_path, out_dir, cfg)
    safe_mkdir(out_path.parent)

    # If forcing extension, do a decode/encode; else plain copy
    if cfg.force_ext and cfg.force_ext.lower() != in_path.suffix.lower():
        with Image.open(in_path) as im:
            if cfg.exif_transpose:
                im = ImageOps.exif_transpose(im)
            im = im.convert("RGB") if cfg.force_ext.lower() in [".jpg", ".jpeg"] else im
            save_image(im, out_path, cfg)
    else:
        shutil.copy2(in_path, out_path)

def degrade_resolution(in_path: Path, out_dir: Path, short_side: int, cfg: Config) -> None:
    out_path = choose_output_path(in_path, out_dir, cfg)

    with Image.open(in_path) as im:
        if cfg.exif_transpose:
            im = ImageOps.exif_transpose(im)

        # Convert to RGB for JPEG to avoid mode issues (e.g., RGBA)
        if (cfg.force_ext or in_path.suffix).lower() in [".jpg", ".jpeg"]:
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")

        w, h = im.size

        # Downsample then upsample back to original size
        dw, dh = compute_downsample_size_keep_aspect(w, h, short_side)

        # If image is already smaller than short_side, we still do:
        # downsample-to-short_side would upscale, which is not "degradation".
        # So we cap the downsample short side to the original short side.
        orig_short = min(w, h)
        effective_short = min(short_side, orig_short)
        if effective_short != short_side:
            dw, dh = compute_downsample_size_keep_aspect(w, h, effective_short)

        small = im.resize((dw, dh), resample=cfg.downsample_resample)
        degraded = small.resize((w, h), resample=cfg.upsample_resample)

        save_image(degraded, out_path, cfg)

# ----------------------------
# MAIN
# ----------------------------

def main(cfg: Config) -> None:
    input_dir = cfg.input_dir.expanduser().resolve()
    output_base = cfg.output_base_dir.expanduser().resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    images = list_images(input_dir, cfg.exts, cfg.recursive)
    if len(images) == 0:
        raise RuntimeError(f"No images found in {input_dir} with extensions {cfg.exts}")

    if cfg.sample_size > len(images):
        raise ValueError(f"sample_size={cfg.sample_size} > available images={len(images)}")

    random.seed(cfg.seed)
    sampled = random.sample(images, cfg.sample_size)

    # Output dirs
    out_orig = output_base / "original"
    out_levels = [
        (s, output_base / f"degraded_short{int(s)}") for s in cfg.degrade_short_sides
    ]

    safe_mkdir(output_base)
    safe_mkdir(out_orig)
    for _, d in out_levels:
        safe_mkdir(d)

    print(f"Input dir:        {input_dir}")
    print(f"Output base dir:  {output_base}")
    print(f"Found images:     {len(images)}")
    print(f"Sampled images:   {len(sampled)} (seed={cfg.seed})")
    print("Degradation levels (short side):", cfg.degrade_short_sides)
    print()

    # Process
    for idx, in_path in enumerate(sampled, start=1):
        print(f"[{idx:03d}/{len(sampled)}] {in_path.name}")

        # Save original (sample subset)
        copy_original(in_path, out_orig, cfg)

        # Save degraded variants
        for short_side, out_dir in out_levels:
            degrade_resolution(in_path, out_dir, short_side, cfg)

    print("\nDone.")
    print("Wrote:")
    print(f"  - {out_orig}")
    for short_side, out_dir in out_levels:
        print(f"  - {out_dir}  (short_side={short_side})")

if __name__ == "__main__":
    main(CONFIG)