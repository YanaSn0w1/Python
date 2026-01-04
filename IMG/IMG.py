import argparse
import random
import math
import os
import colorsys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate customizable good night/morning images.")
parser.add_argument('--text', type=str, default="Good Night")
parser.add_argument('--br', type=str, default=None)
parser.add_argument('--bg_color', type=str, default="dark blue")
parser.add_argument('--text_color', type=str, default="white")
parser.add_argument('--star_color', type=str, default="orange")
parser.add_argument('--num_stars', type=int, default=20)
parser.add_argument('--image_size', type=int, default=800)
parser.add_argument('--font_path', type=str, default=None)
parser.add_argument('--font_size', type=int, default=100)
parser.add_argument('--glow', action='store_true')
parser.add_argument('--rainbow', action='store_true')
parser.add_argument('--seed', type=int, default=None)
parser.add_argument('--output', type=str, default='output.png')
parser.add_argument('--num', type=int, default=1, help='Number of images to generate')
args = parser.parse_args()

# Set random seed if provided
if args.seed is not None:
    random.seed(args.seed)

# Color mapping
bg_map = {
    "dark blue": (0, 0, 50),
    "black": (0, 0, 0),
    "navy": (0, 0, 128)
}

def get_rgb(color_str, default=(0, 0, 0)):
    try:
        return ImageColor.getrgb(color_str)
    except ValueError:
        return default

bg_rgb = bg_map.get(args.bg_color.lower(), get_rgb(args.bg_color, (0, 0, 50)))
text_rgb = get_rgb(args.text_color, (255, 255, 255))
star_rgb = get_rgb(args.star_color, (255, 165, 0))

def random_rainbow():
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
    return (int(r * 255), int(g * 255), int(b * 255))

# MAIN LOOP
for n in range(args.num):

    # Offset seed so each output is unique but reproducible
    if args.seed is not None:
        random.seed(args.seed + n)

    img = Image.new('RGB', (args.image_size, args.image_size), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype(args.font_path, args.font_size) if args.font_path else ImageFont.load_default().font_variant(size=args.font_size)
    except IOError:
        print("Font not found; using default.")
        font = ImageFont.load_default().font_variant(size=args.font_size)

    # Star function
    def draw_star(draw, cx, cy, size, color):
        points = []
        for i in range(5):
            angle = i * 4 * math.pi / 5 - math.pi / 2
            points.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
            angle += 2 * math.pi / 5
            points.append((cx + size / 2 * math.cos(angle), cy + size / 2 * math.sin(angle)))
        draw.polygon(points, fill=color)

    # Moon
    moon_x, moon_y = args.image_size - 200, 100
    moon_size = 100

    if args.rainbow:
        for i in range(10):
            color = random_rainbow()
            draw.arc((moon_x, moon_y, moon_x + moon_size, moon_y + moon_size),
                     start=90, end=270, fill=color, width=1)
        draw.arc((moon_x + 20, moon_y, moon_x + moon_size + 20, moon_y + moon_size),
                 start=90, end=270, fill=bg_rgb, width=10)
    else:
        draw.arc((moon_x, moon_y, moon_x + moon_size, moon_y + moon_size),
                 start=90, end=270, fill=star_rgb, width=10)
        draw.arc((moon_x + 20, moon_y, moon_x + moon_size + 20, moon_y + moon_size),
                 start=90, end=270, fill=bg_rgb, width=10)

    # Stars
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

    # Text
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
        max_width = max(max_width, width)

    text_x = (args.image_size - max_width) / 2
    text_y = (args.image_size - total_height) / 2

    # Glow
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

    # Draw main text
    for i, line in enumerate(lines):
        line_y = text_y + sum(line_heights[:i])
        draw.text((text_x, line_y), line, fill=text_rgb, font=font)

    # Save with incremental naming
    base_name, ext = os.path.splitext(args.output)

    if args.num > 1:
        output_path = f"{base_name}_{n+1:02d}{ext}"
    else:
        output_path = args.output

    counter = 1
    while os.path.exists(output_path):
        output_path = f"{base_name}_{n+1:02d}_{counter:02d}{ext}"
        counter += 1

    img.save(output_path)
    print(f"Image saved as {output_path}")
