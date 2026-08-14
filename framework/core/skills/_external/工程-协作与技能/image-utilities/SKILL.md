---
name: image-utilities
description: Generate or manipulate images. Use when the user asks for "shades of [color]", "color palette", "pixelate", "convert [format] to [format]", "resize image", "rescale image", or any request involving image generation or image manipulation.
---

# Image Utilities

Image generation and manipulation workflows.

## Mode Detection

**STOP:** This is a branching skill, not a workflow. The four modes below are mutually exclusive. Read ONLY the ONE reference file for the detected mode. NEVER read any other files.

Determine mode from user request:

**Color swatches mode**:
- Triggers: "shades of [color]", "color swatches", "color palette", "[N] shades of [color]", "show me some [color] colors", "named [color] shades"
- Qualifier words like "dark", "deep", "light", "pale", "muted", "vivid" before the color name are part of the color request, not a separate mode
- **Read**: `references/color-swatches-reference.md`

**TODO: Image pixellation mode**:
- Triggers: "pixelate", "pixellation", "pixel art", "reduce to [N] colors", "bit palette"
- **Read**: `references/image-pixellation-reference.md` *Not yet implemented*

**TODO: Image conversion mode**:
- Triggers: "convert [format] to [format]", "webp to png", "change format", "save as [format]"
- **Read**: `references/image-conversion-reference.md` *Not yet implemented*

**TODO: Image rescaling mode**:
- Triggers: "resize", "rescale", "scale down", "make smaller/larger", "change dimensions"
- **Read**: `references/image-rescaling-reference.md` *Not yet implemented*

If ambiguous, ask user which mode.

**REMINDER:** Each mode is a SEPARATE BRANCH. Read ONLY the single reference file listed for the detected mode. Do NOT read files for other modes.

## Workflow

1. Detect mode from triggers above
2. Read the appropriate reference doc for that mode
3. Follow the workflow in that reference doc
4. Present completed file(s) to user

**REMINDER:** NEVER DO ALL FOUR MODES. Pick and run one mode.
