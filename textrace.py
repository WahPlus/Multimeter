from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import numpy, math, random, io
from wordfreq import top_n_list

special = [
    "where am i right now",
    "do not type here please",
    "please help me get out",
    "please let me out now",
    "it hurts please help me",
    "multimeter is better than everything",
    "hello this is john halide",
    "also i use arch btw",
    "halide three is never coming",
    "hello very cool pineapple man",
    "i see you through screen",
    "casio is a cool company",
    "rust is the best language",
    "cube is very not cool",
    "multimeter is very very awesome",
    "i hide my true sexuality",
    "i tried eating my phone",
    "i urinated in fridge once",
    "ok ok ok ok ok"
]

def hex_to_rgb(hex_color: int) -> tuple[int, int, int]:
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return r, g, b

def relative_luminance(hex_color: int) -> float:
    r, g, b = hex_to_rgb(hex_color)
    def linearize(c: int) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast(color1: int, color2: int) -> float:
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)  # 1.0 to 21.0
    normalized = (ratio - 1) / 20.0              # 0.0 to 1.0 linear
    return math.log1p(normalized * (math.e - 1))

def generate_image():
    if random.randint(1, 100) == 1:
        text = random.choice(special)
    else:
        text = " ".join(random.sample(top_n_list('en', 100000), 5))

    print(text)

    font = ImageFont.truetype("/usr/share/fonts/TTF/FiraCodeNerdFont-Medium.ttf", 40)
    x1, y1, x2, y2 = font.getbbox(text)
    width = x2 - x1 + (y2 - y1) * 2
    height = (y2 - y1) * 3
    col1 = random.randint(0x000000, 0xFFFFFF)
    col2 = random.randint(0x000000, 0xFFFFFF)
    img = Image.new("RGB", (width, height), col1)
    draw = ImageDraw.Draw(img)
    rand3 = random.random()
    for i in range(int(rand3 * 20)):
        draw.line([(random.randint(0, int(width)), random.randint(0, int(height))), (random.randint(0, int(width)), random.randint(0, int(height)))], fill=random.randint(0x000000, 0xFFFFFF), width=3)
    draw.text((-x1 + (y2 - y1), -y1 + (y2 - y1)), text, fill=col2, font_size=20, font=font)

    array = numpy.array(img)
    height, width = array.shape[:2]
    rand1 = random.random()
    rand2 = random.random() * 2 - 1
    for x in range(width):
        shift = int((math.sin(x / 50) * (y2 - y1) / 3) * rand1 + x * rand2 / 3)
        array[:, x] = numpy.roll(array[:, x], shift, axis=0)
    for y in range(height):
        shift = int((math.sin(y / 50) * (y2 - y1) / 3) * rand1 + y * rand2 / 3)
        array[y, :] = numpy.roll(array[y, :], shift, axis=0)
    img = Image.fromarray(array)
    for i in range(5):
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        img = img.filter(ImageFilter.EDGE_ENHANCE)

    internet_value = len(text) * (abs(rand2) * 3 + rand1 + rand3 - contrast(col1, col2)) / 8
    print(contrast(col1, col2))
    print(internet_value)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return round(internet_value, 2), text, buffer