# Color Swatches Reference

Generate a grid of named color swatches with names and hex codes.

## Step 1: Parse the Request

Extract two things from the user's message:
- **Count (N)**: how many colors they want (default to 10 if unspecified)
- **Color family**: the base color plus any qualifiers

Qualifiers modify the search, not the mode. Examples:
- "20 shades of purple" → N=20, family="purple"
- "10 dark purple shades" → N=10, family="dark purple"
- "deep red colors" → N=10 (default), family="deep red"
- "15 muted teal shades" → N=15, family="muted teal"

## Step 2: Search for Named Colors

Use web search to find real, named color shades for the requested family. Search with queries like:
- "named shades of [color family] with hex codes"
- "[color family] color names and hex values"
- "specific [qualifier] [color] shades list"

Run 2-3 searches to gather enough variety. You need at least N distinct named colors with hex codes.

**Requirements:**
- Every color must have a **real established name** (e.g., "Byzantium", "Wisteria", "Mauve") — do not invent names
- Every color must have a **hex code**
- Colors should be visibly distinct from each other — avoid near-duplicates
- If a qualifier was given (dark, light, muted, etc.), all colors should respect that qualifier — don't mix in light pastels when "dark" was requested
- If you can't find N distinct named colors, get as close as possible and tell the user the final count

## Step 3: Build the Grid

Use the Visualizer tool to render an SVG grid inline in the chat.

### Layout Rules

Determine columns from count:
- 1-4 colors: 2 columns
- 5-9 colors: 3 columns
- 10-16 colors: 4 columns
- 17+: 5 columns

Each cell contains (top to bottom):
1. A color swatch rectangle (filled with the hex color)
2. The color name (centered below the swatch)
3. The hex code (centered below the name, smaller text)

### Sizing

- Swatch size: divide the 600px usable width (680 minus margins) evenly across columns with 20px gaps between them
- Swatch height: equal to swatch width (square)
- Vertical spacing between rows: swatch height + 60px (room for two lines of text + padding)
- Text: color name at 12px (class="ts"), hex code at 12px (class="ts") — both centered under the swatch

### SVG Construction

- viewBox width: 680 (standard)
- viewBox height: calculate from rows × (swatch_height + 60) + 40 (top/bottom padding)
- Start content at x=40, y=20
- Use `text-anchor="middle"` for all text, anchored to swatch center
- Swatch rects get `rx="6"` for slight rounding
- Color name text: use `fill="var(--color-text-primary)"` (adapts to light/dark mode)
- Hex code text: use `fill="var(--color-text-secondary)"`
- Add a thin border to each swatch: `stroke="var(--color-border-tertiary)"` `stroke-width="0.5"` — this ensures very light colors remain visible against a white background

### Text Overflow

Some color names are long (e.g., "Mediterranean Blue"). Before placing text:
- Calculate swatch width
- If the name is longer than roughly (swatch_width / 6.5) characters, truncate or abbreviate
- Hex codes are always 7 chars (#XXXXXX) so they always fit

## Step 4: Save as File

After rendering inline, also save the SVG to `/mnt/user-data/outputs/` as a file.

Filename pattern: `[color-family]-swatches-[N].svg`
- Lowercase, hyphens for spaces
- Examples: `dark-purple-swatches-20.svg`, `teal-swatches-10.svg`

Use `create_file` to write the same SVG content to the output path, then `present_files` so the user can download it.

## Example

User: "Give me 6 shades of blue"

1. Parse: N=6, family="blue"
2. Search: find 6 named blues (e.g., Navy #000080, Cerulean #007BA7, Azure #0080FF, Cornflower #6495ED, Periwinkle #CCCCFF, Steel Blue #4682B4)
3. Grid: 3 columns × 2 rows, swatch ~187px wide
4. Render inline via Visualizer, save to `/mnt/user-data/outputs/blue-swatches-6.svg`
