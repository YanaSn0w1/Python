IMG.py - Customizable Image GeneratorExample Image 

<img width="800" height="800" alt="GE" src="https://github.com/user-attachments/assets/e59cb4dd-b03a-4292-96cd-a97f3ac7a79d" />


OverviewThis Python script (IMG.py) generates simple, customizable images with a starry night theme, including text, a crescent moon, and scattered stars. It's inspired by "Good Night" graphics but can be tweaked for various messages, colors, rainbow effects, multi-line text, and even emojis. Perfect for creating social media posts, cards, or fun visuals.Features include:Randomized star positions and sizes
Support for CSS color names or hex codes
Rainbow mode for vibrant, multi-colored stars and moon
Multi-line text (main text + optional second line)
Glow effect for neon-like text
Emoji support (monochrome by default; color via pilmoji library)
Incremental file naming to avoid overwrites

RequirementsPython 3.x
Required libraries: Pillow (for image processing)Install with: pip install pillow

Optional for color emojis: pilmojiInstall with: pip install pilmoji (may require fixing dependencies like emoji version)

Optional custom fonts: Download .ttf files (e.g., from Google Fonts) for cursive styles

No additional setup needed beyond Python and the libraries.UsageRun the script from the command line with various flags to customize the output. Default output is output.png, but use --output to specify a file name—it will append _01, _02, etc., if the file exists.Basic Command

python IMG.py --text "Good Night" --output good_night.png

ExamplesWith multi-line text and rainbow:

python IMG.py --text "Good Evening" --br "Lets Connect" --bg_color "blueviolet" --rainbow --output GE.png

With emojis (install pilmoji for color support):

python IMG.py --text "Follow Back, ✅" --br "Lets Connect. 💸" --bg_color "blueviolet" --rainbow --output follow.png

Orange background with glow:

python IMG.py --text "Sweet Dreams" --bg_color "orange" --glow --output dreams.png

Custom font and more stars:

python IMG.py --text "Starry Night" --font_path "path/to/Pacifico-Regular.ttf" --num_stars 50 --seed 42 --output starry.png

Run python IMG.py --help for a full list of options.Flags--text: Main text (default: "Good Night")
--br: Optional second line text
--bg_color: Background color (CSS name like "black" or hex like "#000000"; defaults to "dark blue")
--text_color: Text color (CSS/hex; default: "white")
--star_color: Star/moon base color (CSS/hex; default: "orange"; ignored in rainbow mode)
--num_stars: Number of stars (default: 20)
--image_size: Square image size in pixels (default: 800)
--font_path: Path to custom .ttf font
--font_size: Font size (default: 100)
--glow: Enable text glow effect
--rainbow: Enable rainbow colors for stars/moon
--seed: Random seed for reproducibility
--output: Output file name (default: "output.png")

TroubleshootingEmojis not rendering? Use a font with emoji support (e.g., Arial) or install pilmoji for color. If errors occur (e.g., with emoji library), upgrade pilmoji or downgrade emoji to 1.7.0.
Font issues? Specify --font_path to a .ttf file. Defaults to system font like Arial.
Colors not working? Ensure CSS names are valid (e.g., "midnightblue"); see W3Schools Color Names.

ContributingFeel free to fork and submit pull requests! Suggestions for new features (e.g., more shapes, animations) welcome.LicenseMIT License - Free to use, modify, and distribute.

