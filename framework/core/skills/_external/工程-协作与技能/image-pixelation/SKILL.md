---
name: image-pixelation
description: Convert images to pixel art / retro 8-bit style. Use this skill whenever the user wants to "pixelate", "pixellate", "pixel-art", "8-bit", "retro-fy", or "downsample" an image, apply a fixed retro color palette to a photo, or batch-convert images into a blocky low-res look. Trigger even if the user only describes the effect (e.g. "make this look like an old video game sprite", "give this photo that chunky NES vibe", "snap these colors to a 12-color palette") without saying the word pixelate. A Pillow port of the pixelit library.
---

# Image Pixelation

Convert any image into pixel art. This is a headless Python/Pillow port of
the browser-based [pixelit](https://github.com/giventofly/pixelit) library, so
it runs in the sandbox without a browser/canvas.

## When to use

Use whenever someone wants a blocky, low-resolution, retro/8-bit look applied
to an image, optionally snapped to a fixed color palette. Works on a single
image or a batch.

## The effect, in plain terms

Pixelation = shrink the image down small, then blow it back up with smoothing
turned off. The fewer pixels survive the shrink, the chunkier the result. An
optional second pass snaps every pixel to the nearest color in a fixed palette
to get the classic limited-color retro look.

## How to run

The script lives at `scripts/pixelate.py`. It needs Pillow and numpy:

```bash
pip install Pillow numpy --break-system-packages
```

Basic usage:

```bash
python scripts/pixelate.py INPUT OUTPUT [options]
```

Options:

- `--scale N` — pixelit scale, integer **1-50**, percent of detail kept.
  **This is faithful to pixelit: HIGHER = MORE detail (less blocky), LOWER = chunkier.**
  It is NOT a block size. Default `8`. Good values to try: `4` (very blocky),
  `8` (default retro), `16` (mild), `32` (subtle).
- `--palette NAME_OR_PATH` — snap colors to a preset (see below) or a path to a
  JSON file shaped `[[r,g,b], ...]`. Omit to keep the original colors.
- `--grayscale` — average channels to grayscale before palette snapping.
- `--max-width N` / `--max-height N` — clamp output dimensions proportionally
  (shrink-only; never enlarges).
- `--list-palettes` — print the bundled presets and exit.

## Important: the scale parameter is counterintuitive

Because this faithfully mirrors pixelit, `--scale` is a *percentage of detail
retained*, not a pixel/block size. If a user says "pixelate at size 32" meaning
"big chunky 32px blocks", that is the OPPOSITE of `--scale 32` (which is barely
pixelated). When the user's intent is "chunkier", LOWER the scale. Confirm intent
if ambiguous.

## Bundled palettes

Six 12-color fantasy palettes (from the source repo's `palettes_12b`) live in
`references/palettes.json`:

| Name | Theme |
|------|-------|
| `emberwake` | fire, earth, warmth |
| `frostveil` | ice, silver, moonlight |
| `sunken_citadel` | ruins, metal, ghost light |
| `starfall` | sky, violet, gold |
| `mirethorn` | swamp, decay, magic |
| `azureglass` | sea, mineral, coral |

(Note: the source repo's last `azureglass` color was malformed/truncated; it has
been completed to a valid RGB triple here.)

## Examples

**Default retro look:**
```bash
python scripts/pixelate.py photo.jpg out.png --scale 8
```

**Very blocky + fire palette:**
```bash
python scripts/pixelate.py hero.png sprite.png --scale 4 --palette emberwake
```

**Batch a folder:**
```bash
for f in *.png; do
  python scripts/pixelate.py "$f" "pixelated_$f" --scale 8 --palette frostveil
done
```

**Custom palette from a JSON file:**
```bash
python scripts/pixelate.py in.png out.png --palette my_palette.json
```

## Pipeline order

Matches pixelit's `draw -> pixelate -> convertPalette -> resizeImage`:
pixelate first, then optional grayscale, then optional palette snap, then
optional resize. The functions in `pixelate.py` are independent and can be
imported and recomposed if a different order is needed.
