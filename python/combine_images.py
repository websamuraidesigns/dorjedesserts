from PIL import Image
from pathlib import Path
import argparse
import sys

# Directories (relative to repo root)
dirs = {
    "is_it_cake": Path("images/cakes/is_it_cake"),
    "sophisticaked": Path("images/cakes/sophisticaked"),
    "themed": Path("images/cakes/themed"),
}

OUT = Path("images/hero-background.jpg")
TARGET_HEIGHT = 400

def pick_first_image(p: Path, index: int):
    if not p.exists() or not p.is_dir():
        return None
    # Select images by filename (sorted, case-insensitive).
    files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        files.extend(list(p.glob(ext)))
    if not files:
        return None
    # Sort by name (case-insensitive) and return the first
    files_sorted = sorted(files, key=lambda x: x.name.lower())
    return files_sorted[index]


def open_and_resize(p: Path, h: int):
    img = Image.open(p).convert("RGB")
    w = int(img.width / img.height * h)
    # Use modern Resampling if available
    resample = getattr(Image, "Resampling", Image).LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    return img.resize((w, h), resample)


def main():
    parser = argparse.ArgumentParser(description="Combine three category images into a hero background")
    parser.add_argument("--indexes", nargs=3, type=int, default=[0, 0, 0],
                        help="Indexes of images to pick from each folder (1-based). Default is 0 for all, which picks the first image sorted by name.")
    parser.add_argument("--mode", choices=("side-by-side", "blend"), default="side-by-side",
                        help="Layout mode: 'side-by-side' places images next to each other; 'blend' overlays them with partial transparency")
    args = parser.parse_args()
    picked = []
    index = 0
    for key in ("is_it_cake", "sophisticaked", "themed"):
        imgp = pick_first_image(dirs[key], args.indexes[index])
        if imgp is None:
            print(f"No images found in {dirs[key]} — skipping.")
        else:
            print(f"Picked for {key}: {imgp}")
            picked.append(imgp)
        index += 1

    if len(picked) < 3:
        print("Need one image from each folder. Aborting.")
        return

    imgs = [open_and_resize(p, TARGET_HEIGHT) for p in picked]

    if args.mode == "side-by-side":
        total_w = sum(i.width for i in imgs)
        combined = Image.new("RGB", (total_w, TARGET_HEIGHT))

        x = 0
        for im in imgs:
            combined.paste(im, (x, 0))
            x += im.width

    else:  # blend mode
        # Resize images to same height (already done) and crop to common width (smallest width)
        common_w = min(i.width for i in imgs)
        cropped = []
        for im in imgs:
            # center-crop width to common_w
            if im.width > common_w:
                left = (im.width - common_w) // 2
                im = im.crop((left, 0, left + common_w, TARGET_HEIGHT))
            cropped.append(im.convert("RGBA"))

        base = cropped[0].copy()
        # Overlay second and third images with partial transparency masks
        mask2 = Image.new("L", base.size, int(255 * 0.5))
        base.paste(cropped[1], (0, 0), mask2)
        mask3 = Image.new("L", base.size, int(255 * 0.4))
        base.paste(cropped[2], (0, 0), mask3)

        combined = base.convert("RGB")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.save(OUT, quality=95)
    print(f"Saved combined image: {OUT} ({combined.width}x{combined.height})")


if __name__ == "__main__":
    main()
