# [PayPal-Donations](https://www.paypal.com/donate/?hosted_button_id=9LWWH273HEVC4 "Donate to YanaHeat") ⬅️✅

# IMG.py – Starry Image Generator

<img width="800" height="800" alt="GE" src="https://github.com/user-attachments/assets/fb9756f4-c9c8-43f4-b5a6-b0f9b8a7ef09" />

This Python script generates customizable starry images with text, a crescent moon, and scattered stars. It’s ideal for creating whimsical graphics like “Good Night” cards, with options for colors, rainbow effects, multi-line text, glow, and emojis.

## ✨ Features
- Randomized star positions, sizes, and colors (with optional rainbow mode)
- Multi-line text support (main line + optional second line)
- Background, text, and star colors using CSS names or hex codes
- Glow effect for neon-style text
- Emoji rendering (monochrome default; color with `pilmoji`)
- Incremental file naming to prevent overwrites
- Reproducible randomization via seed
- 

## 📦 Requirements
- Python 3.6+
- Pillow  
  ```bash
  pip install Pillow
  ```
- Optional: pilmoji for color emojis  
  ```bash
  pip install pilmoji
  ```

If emoji errors occur, upgrade `pilmoji` or downgrade `emoji` to version `1.7.0`.

## 📥 Installation

Install dependencies:

```bash
pip install Pillow
pip install pilmoji   # optional
```

## 🚀 Usage

Run the script:

```bash
python IMG.py [--text <text>] [--br <second_line>] [--bg_color <color>] \
[--text_color <color>] [--star_color <color>] [--num_stars <num>] \
[--image_size <size>] [--font_path <path>] [--font_size <size>] \
[--glow] [--rainbow] [--seed <seed>] [--output <file>]
```

### Arguments

| Argument | Description |
|---------|-------------|
| `--text` | Main text (default: `"Good Night"`) |
| `--br` | Second line text (optional) |
| `--bg_color` | Background color (CSS or hex) |
| `--text_color` | Text color |
| `--star_color` | Star/moon color (ignored with `--rainbow`) |
| `--num_stars` | Number of stars (default: 20) |
| `--image_size` | Image size in pixels (default: 800) |
| `--font_path` | Path to `.ttf` font |
| `--font_size` | Font size (default: 100) |
| `--glow` | Enable glow effect |
| `--rainbow` | Rainbow stars + moon |
| `--seed` | Random seed |
| `--output` | Output filename (default: `output.png`) |
| `--num` | The number of random star placed picture files to create |

### Example

```bash
python IMG.py --text "Good Evening. 💎" --br "Lets Connect. 🔁" --bg_color "blueviolet" --rainbow --output GE.png --num 7 --glow --image_size 1000
python IMG.py --text "Good Night. ⚡" --br "Lets Connect. 💥" --bg_color "blueviolet" --rainbow --output GN.png --num 7 --glow --image_size 1000
```

This creates a rainbow starry image with multi-line text on a blueviolet background, saved as `GE.png` (or `GE_01.png` if it already exists) x7.

## 📝 Notes
- Use CSS color names (`midnightblue`, `gold`, etc.) or hex (`#001080`)
- For color emojis, install `pilmoji`
- Custom fonts: download `.ttf` (e.g., Google Fonts) and pass via `--font_path`
- If text doesn’t fit, adjust `--font_size` or `--image_size`

## 📄 License
MIT License – see `LICENSE` for details.
