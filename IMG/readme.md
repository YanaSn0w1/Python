# [PayPal-Donations](https://www.paypal.com/donate/?hosted_button_id=9LWWH273HEVC4 "Donate to YanaHeat") ⬅️✅

# IMG.py – Starry Image Generator
```

This Python script generates customizable starry images with text, a crescent moon, and scattered stars. It’s ideal for creating whimsical graphics like “Good Night” cards, with options for colors, rainbow effects, multi-line text, glow, and emojis.

## ✨ Features
- Randomized star positions, sizes, and colors (with optional rainbow mode)
- Multi-line text support (main line + optional second line)
- Background, text, and star colors using CSS names or hex codes
- Glow effect for neon-style text
- Emoji rendering (monochrome default; color with `pilmoji`)
- Incremental file naming to prevent overwrites
- Reproducible randomization via seed. 

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

### Examples
<img width="1400" height="1400" alt="Hello_03" src="https://github.com/user-attachments/assets/70cb0677-5073-4575-8653-8c951c538fce" />

```bash
 python IMG.py --text "Just Saying Hello 👋 " --br "You can Gain 65+ Mutuals ✅" --text_color "blue" --bg_color "black" --rainbow --output Hello.png --glow --image_size 1400
```

<img width="800" height="800" alt="GE" src="https://github.com/user-attachments/assets/fb9756f4-c9c8-43f4-b5a6-b0f9b8a7ef09" />

```bash
python IMG.py --text "Follow Back, ✅" --br "Lets Connect. 💸" --bg_color "blueviolet" --rainbow --output GE.png
```

<img width="800" height="800" alt="Hello" src="https://github.com/user-attachments/assets/02037509-1d15-4a3d-94df-3ef4d6a8fe75" />

```bash
 python IMG.py --text "Who needs a" --br "follow back? 🔥" --bg_color "green" --rainbow --output FB.png
```

<img width="1200" height="1200" alt="HI_02_01" src="https://github.com/user-attachments/assets/0d68fe7d-6381-4deb-84ba-ba0f4cabbd72" />

```bash
 python IMG.py --text "Just Say Hi. 👋" --br "Gain 100 Followers." --bg_color "darkred" --rainbow --output HI.png --num 2 --glow --image_size 1200
```

<img width="1200" height="1200" alt="Hello_02_08" src="https://github.com/user-attachments/assets/cb06848f-9f09-43ef-bb5f-0200fb89efac" />

```bash
 python IMG.py --text "Say Hello 👋" --br "Let’s FollOw you 🤝" --text_color "thistle" --bg_color "teal" --rainbow --output Hello.png --num 2 --image_size 1200
```

<img width="1200" height="1200" alt="Hello_02_09" src="https://github.com/user-attachments/assets/6fa41b98-412a-44ad-b9a3-12cf96459d37" />

```bash
 python IMG.py --text "Results aren't Immediate." --br "Trust the process. ✅" --text_color "crimson" --bg_color "darkblue" --rainbow --output Hello.png --num 2 --image_size 1200
```

<img width="1200" height="1200" alt="Hello_02_02" src="https://github.com/user-attachments/assets/6e002cd5-2862-4b88-8098-5e9b58d1c1a2" />

```bash
 python IMG.py --text "Stay Safe. 🙏 😇" --br "Let's Connect. 💰 🚀" --text_color "blueviolet" --bg_color "chartreuse" --rainbow --output Hello.png --num 2 --image_size 1200
```

<img width="1300" height="1300" alt="Hello_01_10" src="https://github.com/user-attachments/assets/003c76a3-90e1-45b0-98b7-a9b9d926fe0f" />

```bash
 python IMG.py --text "Thank You God. 🌹 🙏" --br "For the Connect. 💰 💎" --text_color "gold" --bg_color "crimson" --rainbow --output Hello.png --num 2 --image_size 1300
```

<img width="1200" height="1200" alt="Hi" src="https://github.com/user-attachments/assets/d61cc88f-79ba-4832-aac9-b825676ebd5a" />

```bash
 python IMG.py --text "100% Follow Back 🔙 " --br "Just retweet and reply 🔁" --text_color "cornsilk" --bg_color "cadetblue" --rainbow --output Hi.png --image_size 1200
```

## 📝 Notes
- Use CSS color names (`midnightblue`, `gold`, etc.) or hex (`#001080`)
- For color emojis, install `pilmoji`
- Custom fonts: download `.ttf` (e.g., Google Fonts) and pass via `--font_path`
- If text doesn’t fit, adjust `--font_size` or `--image_size`

## 📄 License
MIT License – see `LICENSE` for details.
