#!/usr/bin/env python3
"""
Convert a directory of RGB images to grayscale.

- Reads images from INPUT_DIR
- Converts to grayscale (luminance) and saves to OUTPUT_DIR
- Preserves filenames; optionally forces an output extension/format
- All file paths/settings are editable in the CONFIG section

Dependencies:
  pip install pillow
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List

from PIL import Image, ImageOps

# ----------------------------
# CONFIG (EDIT THESE)
# ----------------------------

@dataclass
class Config:
    input_dir: Path = Path(r" ")          # directory with 100 RGB images
    output_dir: Path = Path(r" ")   # where grayscale images go

    # If True, scans subfolders too
    recursive: bool = False

    # Extensions to include
    exts: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")

    # If None: keep original extension
    # Else: force output extension, e.g. ".jpg" or ".png"
    force_ext: Optional[str] = None

    # If True, fixes EXIF orientation (common for JPEGs) before conversion
    exif_transpose: bool = True

    # If True, save as 3-channel grayscale (L->RGB) so models expecting RGB still work
    save_as_3channel: bool = True

    # JPEG options (only used when output is .jpg/.jpeg)
    jpeg_quality: int = 95
    jpeg_optimize: bool = True
    jpeg_subsampling: int = 0  # 0=4:4:4

CONFIG = Config()

# ----------------------------
# HELPERS
# ----------------------------

def list_images(input_dir: Path, exts: Tuple[str, ...], recursive: bool) -> List[Path]:
    exts_lower = set(e.lower() for e in exts)
    if recursive:
        files = [p for p in input_dir.rglob("*") if p.is_file()]
    else:
        files = [p for p in input_dir.glob("*") if p.is_file()]
    return sorted([p for p in files if p.suffix.lower() in exts_lower])

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def out_path_for(in_path: Path, out_dir: Path, force_ext: Optional[str]) -> Path:
    ext = force_ext if force_ext is not None else in_path.suffix
    return out_dir / f"{in_path.stem}{ext}"

def save_image(img: Image.Image, path: Path, cfg: Config) -> None:
    ensure_dir(path.parent)
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        img.save(
            path,
            quality=cfg.jpeg_quality,
            optimize=cfg.jpeg_optimize,
            subsampling=cfg.jpeg_subsampling,
        )
    else:
        img.save(path)

# ----------------------------
# MAIN
# ----------------------------

def main(cfg: Config) -> None:
    input_dir = cfg.input_dir.expanduser().resolve()
    output_dir = cfg.output_dir.expanduser().resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    ensure_dir(output_dir)

    imgs = list_images(input_dir, cfg.exts, cfg.recursive)
    if not imgs:
        raise RuntimeError(f"No images found in {input_dir} with extensions {cfg.exts}")

    print(f"Input:   {input_dir}")
    print(f"Output:  {output_dir}")
    print(f"Images:  {len(imgs)}")
    print(f"Force ext: {cfg.force_ext!r}")
    print(f"Save as 3-channel: {cfg.save_as_3channel}")
    print()

    for i, in_path in enumerate(imgs, start=1):
        out_path = out_path_for(in_path, output_dir, cfg.force_ext)

        with Image.open(in_path) as im:
            if cfg.exif_transpose:
                im = ImageOps.exif_transpose(im)

            # Convert to grayscale (luminance)
            gray = im.convert("L")

            # Optionally convert back to 3-channel (RGB) grayscale
            if cfg.save_as_3channel:
                gray = gray.convert("RGB")

            save_image(gray, out_path, cfg)

        print(f"[{i:03d}/{len(imgs)}] {in_path.name} -> {out_path.name}")

    print("\nDone.")

if __name__ == "__main__":
    main(CONFIG)