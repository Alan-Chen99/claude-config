from PIL import Image

SIZES = {"sm": (160, 160), "md": (480, 480), "lg": (1200, 1200)}


def thumb(src_path, out_path, size="md"):
    im = Image.open(src_path)
    im.thumbnail(SIZES[size])
    im.save(out_path, quality=88)
    return out_path
