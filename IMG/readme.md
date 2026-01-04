

# IMG.py - Starry Image Generator

This Python script generates customizable starry images with text, a crescent moon, and scattered stars. It's ideal for creating whimsical graphics like "Good Night" cards, with options for colors, rainbow effects, multi-line text, glow, and emojis.

## Features
- Randomized star positions, sizes, and colors (with rainbow mode).
- Multi-line text support (main line + optional second line).
- Background, text, and star colors using CSS names or hex codes.
- Glow effect for neon-style text.
- Emoji rendering (monochrome default; color with `pilmoji`).
- Incremental file naming to prevent overwrites.
- Reproducible randomization via seed.

## Requirements
- Python 3.6+
- Pillow library (`pip install Pillow`)
- Optional: `pilmoji` for color emojis (`pip install pilmoji`)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git

Install the required Python package:bash

pip install Pillow

For color emojis (optional):bash

pip install pilmoji

If errors occur with emoji dependency, upgrade pilmoji or downgrade emoji to 1.7.0.

UsageRun the script with the following command:bash

python IMG.py [--text <text>] [--br <second_line>] [--bg_color <color>] [--text_color <color>] [--star_color <color>] [--num_stars <num>] [--image_size <size>] [--font_path <path>] [--font_size <size>] [--glow] [--rainbow] [--seed <seed>] [--output <file>]

Arguments--text: Main text (default: "Good Night", required for custom).
--br: Second line text (optional).
--bg_color: Background color (CSS/hex, default: "dark blue").
--text_color: Text color (CSS/hex, default: "white").
--star_color: Star/moon color (CSS/hex, default: "orange"; ignored with --rainbow).
--num_stars: Number of stars (default: 20).
--image_size: Square size in pixels (default: 800).
--font_path: Path to custom .ttf font (optional).
--font_size: Font size (default: 100).
--glow: Enable text glow (optional).
--rainbow: Rainbow stars/moon (optional).
--seed: Random seed for reproducibility (optional).
--output: Output file (default: "output.png").

Examplebash

python IMG.py --text "Good Evening" --br "Lets Connect" --bg_color "blueviolet" --rainbow --output GE.png

This creates a rainbow starry image with multi-line text on a blueviolet background, saved as GE.png (or GE_01.png if it exists).OutputImage saved as specified (with increment if needed).
Console message confirming the save path.

NotesUse CSS color names (e.g., "midnightblue") or hex (e.g., "#001080"). See W3Schools.
For emojis, install pilmoji; otherwise, they may appear monochrome or as boxes.
Custom fonts: Download .ttf (e.g., Pacifico from Google Fonts) and use --font_path.
If text doesn't fit, adjust --font_size or --image_size.

LicenseMIT License - see LICENSE for details.
```
