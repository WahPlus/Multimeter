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
    "i urinated in fridge once"
]

def generate_image():
    if random.randint(1, 100) == 1:
        text = random.choice(special)
    else:
        text = " ".join(random.sample(top_n_list('en', 100000), 5))

    print(text)

    font = ImageFont.truetype("/usr/share/fonts/TTF/FiraCodeNerdFont-Medium.ttf", 40)
    x1, y1, x2, y2 = font.getbbox(text)
    width = x2 - x1 + (y2 - y1) * 2
    height = (y2 - y1)*3
    img = Image.new("RGB", (width, height), random.randint(0x000000, 0xFFFFFF))
    draw = ImageDraw.Draw(img)
    rand3 = random.random()
    for i in range(int(rand3 * 20)):
        draw.line([(random.randint(0, int(width)), random.randint(0, int(height))), (random.randint(0, int(width)), random.randint(0, int(height)))], fill=random.randint(0x000000, 0xFFFFFF), width=3)
    draw.text((-x1 + (y2 - y1), -y1 + (y2 - y1)), text, fill=random.randint(0x000000, 0xFFFFFF), font_size=20, font=font)

    array = numpy.array(img)
    height, width = array.shape[:2]
    rand1 = random.random()
    rand2 = random.random()
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

    internet_value = rand1 * rand2 * rand3 * len(text)
    print(internet_value)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return round(internet_value, 2), text, buffer
