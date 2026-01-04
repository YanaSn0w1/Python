

## IMG.py - Simple Image Generator

This script creates fun, starry images with custom text, colors, and effects. Great for quick graphics like "Good Night" cards.

### Setup
- Install Python 3.
- Run `pip install pillow` for image tools.
- For color emojis: `pip install pilmoji` (fix any errors by upgrading or downgrading `emoji` to 1.7.0).

### How to Run
Save as `IMG.py` and use commands like these in your terminal:

Basic:

python IMG.py --text "Good Night" --output gn.png

With second line and rainbow:

python IMG.py --text "Good Evening" --br "Lets Connect" --bg_color "blueviolet" --rainbow --output ge.png

With emojis:

python IMG.py --text "Follow Back " --br "Lets Connect " --bg_color "blueviolet" --rainbow --output fb.png

Glow effect:

python IMG.py --text "Sweet Dreams" --bg_color "orange" --glow --output dreams.png

See `--help` for all options:

python IMG.py --help

### Tips
- Use CSS colors like "black" or "#FF0000".
- For custom fonts, add `--font_path "yourfont.ttf"`.
- Files save with numbers if name exists (e.g., gn_01.png).

### Issues?
- Emojis: Install pilmoji; use a emoji-friendly font.
- Colors: Check https://www.w3schools.com/colors/colors_names.asp.

Free to use (MIT License).

