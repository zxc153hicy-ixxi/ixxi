#!/usr/bin/env python3
"""
pixelate.py - Convert an image to pixel art.

A Python/Pillow port of pixelit (https://github.com/giventofly/pixelit) by
Jose Moreira. The original is browser/canvas code; this reproduces its
algorithm so it can run headless in a sandbox.

Pipeline (mirrors pixelit's draw -> pixelate -> convertPalette -> resizeImage):
  1. pixelate  : downscale to `scale`% of original, then upscale back with
                 nearest-neighbour. Lower scale = blockier.
  2. palette   : (optional) snap every pixel to the nearest colour in a fixed
                 palette by Euclidean RGB distance.
  3. grayscale : (optional) average the channels.
  4. resize    : (optional) clamp to max width/height, proportionally, shrink-only.

Faithful to pixelit, `--scale` is a PERCENTAGE in [1..50]: HIGHER = MORE detail
(less pixelated). It is NOT a block size.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required. Install with: pip install Pillow --break-system-packages")

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PALETTES_FILE = SCRIPT_DIR.parent / "references" / "palettes.json"


def pixelate(img, scale):
    """Downscale to `scale`% then upscale with nearest-neighbour.

    `scale` is clamped to [1, 50]; values outside fall back to pixelit's
    default of 8. Smaller scale -> fewer source pixels survive -> blockier.
    """
    if not 1 <= scale <= 50:
        scale = 8
    w, h = img.size
    frac = scale * 0.01
    small_w = max(1, round(w * frac))
    small_h = max(1, round(h * frac))
    small = img.resize((small_w, small_h), Image.BILINEAR)
    return small.resize((w, h), Image.NEAREST)


def convert_palette(img, palette):
    """Snap each pixel to the nearest palette colour by Euclidean RGB distance."""
    rgb = img.convert("RGB")
    arr = np.asarray(rgb, dtype=np.int32)
    h, w, _ = arr.shape
    flat = arr.reshape(-1, 3)
    pal = np.asarray(palette, dtype=np.int32)
    dists = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    nearest = pal[dists.argmin(axis=1)].astype(np.uint8)
    return Image.fromarray(nearest.reshape(h, w, 3), "RGB")


def convert_grayscale(img):
    """Average the channels (matches pixelit's simple mean, not luma)."""
    rgb = img.convert("RGB")
    arr = np.asarray(rgb, dtype=np.uint16)
    avg = arr.mean(axis=2).astype(np.uint8)
    return Image.fromarray(np.stack([avg] * 3, axis=2), "RGB")


def resize_image(img, max_width=None, max_height=None):
    """Shrink proportionally so the image fits within both bounds. Never enlarges."""
    if not max_width and not max_height:
        return img
    w, h = img.size
    ratios = []
    if max_width and w > max_width:
        ratios.append(max_width / w)
    if max_height and h > max_height:
        ratios.append(max_height / h)
    if not ratios:
        return img
    ratio = min(ratios)
    return img.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.NEAREST)


def load_palettes():
    if not PALETTES_FILE.exists():
        return {}
    with open(PALETTES_FILE) as f:
        return json.load(f)


def resolve_palette(name_or_path):
    """Return a list of [r,g,b] from a named preset or a JSON file path."""
    if not name_or_path:
        return None
    presets = load_palettes()
    if name_or_path in presets:
        return presets[name_or_path]
    p = Path(name_or_path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    preset_list = ", ".join(presets) if presets else "(none)"
    raise SystemExit(
        f"Unknown palette '{name_or_path}'. Presets: {preset_list}. "
        "Or pass a path to a JSON file of [[r,g,b],...]."
    )


def process(input_path, output_path, scale=8, palette=None,
            grayscale=False, max_width=None, max_height=None):
    img = Image.open(input_path).convert("RGB")
    img = pixelate(img, scale)
    if grayscale:
        img = convert_grayscale(img)
    if palette is not None:
        img = convert_palette(img, palette)
    img = resize_image(img, max_width, max_height)
    img.save(output_path)
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert an image to pixel art (Pillow port of pixelit)."
    )
    parser.add_argument("input", nargs="?", help="Path to the source image.")
    parser.add_argument("output", nargs="?", help="Path to write the pixelated image.")
    parser.add_argument(
        "--scale", type=int, default=8,
        help="Pixelit scale 1-50 (percent of detail kept). LOWER = blockier. Default 8.",
    )
    parser.add_argument(
        "--palette", default=None,
        help="Named preset (e.g. emberwake) or path to a JSON [[r,g,b],...] file.",
    )
    parser.add_argument("--grayscale", action="store_true", help="Convert to grayscale.")
    parser.add_argument("--max-width", type=int, default=None, help="Clamp output width (shrink only).")
    parser.add_argument("--max-height", type=int, default=None, help="Clamp output height (shrink only).")
    parser.add_argument("--list-palettes", action="store_true", help="List preset palettes and exit.")
    args = parser.parse_args(argv)

    if args.list_palettes:
        for name, colors in load_palettes().items():
            print(f"{name}: {len(colors)} colors")
        return

    if not args.input or not args.output:
        parser.error("input and output are required (unless using --list-palettes)")

    palette = resolve_palette(args.palette)
    out = process(
        args.input, args.output, scale=args.scale, palette=palette,
        grayscale=args.grayscale, max_width=args.max_width, max_height=args.max_height,
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
