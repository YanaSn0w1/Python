import argparse
import random
import math
import os
import colorsys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

try:
    from pilmoji import Pilmoji
except ImportError:
    Pilmoji = None

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate customizable good night/morning images.")
parser.add_argument('--text', type=str, default="Good Night", help='Main text to display (e.g., "Good Morning")')
parser.add_argument('--br', type=str, default=None, help='Second line text (e.g., "Lets Connect") for multi-line')
parser.add_argument('--bg_color', type=str, default="dark blue", help='Background color (dark blue, black, navy, CSS name like midnightblue, or hex like #000050)')
parser.add_argument('--text_color', type=str, default="white", help='Text color (CSS name like white or hex like #FFFFFF)')
parser.add_argument('--star_color', type=str, default="orange", help='Star/moon base color (CSS name like orange or hex like #FFA500); ignored if --rainbow is used')
parser.add_argument('--num_stars', type=int, default=20, help='Number of stars (e.g., 20)')
parser.add_argument('--image_size', type=int, default=800, help='Image size (square, e.g., 800 for 800x800)')
parser.add_argument('--font_path', type=str, default=None, help='Path to custom .ttf font (e.g., Pacifico-Regular.ttf for cursive)')
parser.add_argument('--font_size', type=int, default=100, help='Font size')
parser.add_argument('--glow', action='store_true', help='Add glow effect to text (non-Pilmoji path)')
parser.add_argument('--rainbow', action='store_true', help='Enable rainbow colors for stars and moon (overrides --star_color)')
parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
parser.add_argument('--output', type=str, default='output.png', help='Output file name (e.g., good_morning.png)')
parser.add_argument('--num', type=int, default=1, help='Number of images to generate')
args = parser.parse_args()

# Set random seed if provided
if args.seed is not None:
    random.seed(args.seed)

# Color mapping for legacy named backgrounds
bg_map = {
    "dark blue": (0, 0, 50),
    "black": (0, 0, 0),
    "navy": (0, 0, 128)
}

# Get RGB for colors (supports CSS names and hex)
def get_rgb(color_str, default=(0, 0, 0)):
    try:
        return ImageColor.getrgb(color_str)
    except ValueError:
        return default

# Background: Use map if matched, else CSS/hex
bg_rgb = bg_map.get(args.bg_color.lower(), get_rgb(args.bg_color, (0, 0, 50)))

# Text color: Directly use CSS/hex
text_rgb = get_rgb(args.text_color, (255, 255, 255))

# Star/moon base (unless rainbow)
star_rgb = get_rgb(args.star_color, (255, 165, 0))

# Function to get random rainbow color (HSV for vibrant spectrum)
def random_rainbow():
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
    return (int(r * 255), int(g * 255), int(b * 255))

# Function for 5-pointed star
def draw_star(draw, cx, cy, size, color):
    points = []
    for i in range(5):
        angle = i * 4 * math.pi / 5 - math.pi / 2
        points.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
        angle += 2 * math.pi / 5
        points.append((cx + size / 2 * math.cos(angle), cy + size / 2 * math.sin(angle)))
    draw.polygon(points, fill=color)

# MAIN LOOP
for n in range(args.num):
    if args.seed is not None:
        random.seed(args.seed + n)

    # Create image
    img = Image.new('RGB', (args.image_size, args.image_size), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # Load font (use custom if provided, else default)
    try:
        if args.font_path:
            font = ImageFont.truetype(args.font_path, args.font_size)
        else:
            font = ImageFont.load_default().font_variant(size=args.font_size)
    except IOError:
        print("Font not found; using default.")
        font = ImageFont.load_default().font_variant(size=args.font_size)

    # Add moon (crescent) - rainbow gradient if enabled
    moon_x, moon_y = args.image_size - 200, 100
    moon_size = 100
    if args.rainbow:
        for i in range(10):
            color = random_rainbow()
            draw.arc(
                (moon_x, moon_y, moon_x + moon_size, moon_y + moon_size),
                start=90,
                end=270,
                fill=color,
                width=1
            )
        draw.arc(
            (moon_x + 20, moon_y, moon_x + moon_size + 20, moon_y + moon_size),
            start=90,
            end=270,
            fill=bg_rgb,
            width=10
        )
    else:
        draw.arc(
            (moon_x, moon_y, moon_x + moon_size, moon_y + moon_size),
            start=90,
            end=270,
            fill=star_rgb,
            width=10
        )
        draw.arc(
            (moon_x + 20, moon_y, moon_x + moon_size + 20, moon_y + moon_size),
            start=90,
            end=270,
            fill=bg_rgb,
            width=10
        )

    # Add randomized stars
    for _ in range(args.num_stars):
        x = random.randint(50, args.image_size - 50)
        y = random.randint(50, args.image_size - 50)
        size = random.randint(5, 15)
        if args.rainbow:
            color = random_rainbow()
        else:
            color = (
                max(0, star_rgb[0] + random.randint(-20, 20)),
                max(0, star_rgb[1] + random.randint(-20, 20)),
                max(0, star_rgb[2] + random.randint(-20, 20))
            )
        draw_star(draw, x, y, size, color)

    # Add multi-line text (from --text and optional --br)
    lines = [args.text]
    if args.br:
        lines.append(args.br)

    line_heights = []
    total_height = 0
    max_width = 0

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        line_heights.append(height)
        total_height += height
        if width > max_width:
            max_width = width

    # Center the block
    text_x = (args.image_size - max_width) / 2
    text_y = (args.image_size - total_height) / 2

    if Pilmoji:
        # Emoji-safe path: no blur here, just clean emoji + text
        full_text = "\n".join(lines)
        with Pilmoji(img) as pilmoji:
            pilmoji.text((int(text_x), int(text_y)), full_text, fill=text_rgb, font=font)
    else:
        # Glow (Pillow-only path)
        if args.glow:
            for i, line in enumerate(lines):
                line_y = text_y + sum(line_heights[:i])
                for dx in [-2, 0, 2]:
                    for dy in [-2, 0, 2]:
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((text_x + dx, line_y + dy), line, fill=text_rgb, font=font)
            img = img.filter(ImageFilter.GaussianBlur(2))
            draw = ImageDraw.Draw(img)

        # Draw main text lines
        for i, line in enumerate(lines):
            line_y = text_y + sum(line_heights[:i])
            draw.text((text_x, line_y), line, fill=text_rgb, font=font)

    # Save with incremental naming to avoid overwrite
    base_name, ext = os.path.splitext(args.output)

    if args.num > 1:
        # Base name per index (e.g., output_01.png, output_02.png)
        base_with_index = f"{base_name}_{n+1:02d}"
        output_path = f"{base_with_index}{ext}"
    else:
        base_with_index = base_name
        output_path = args.output

    counter = 1
    while os.path.exists(output_path):
        output_path = f"{base_with_index}_{counter:02d}{ext}"
        counter += 1

    img.save(output_path)
    print(f"Image saved as {output_path}")
