from PIL import Image

SIZES = {"sm": (160, 160), "md": (480, 480), "lg": (1200, 1200)}

# Pinned so thumbnail sharpness is a property of this file rather than of the
# installed Pillow's defaults. Both values are Pillow 10.2.0's defaults, so
# stating them changes no output; see DECISIONS.md "Thumbnail sharpness".
RESAMPLE = Image.Resampling.BICUBIC
REDUCING_GAP = 2.0
QUALITY = 88


def resize(src_path, size="md"):
    im = Image.open(src_path)
    im.thumbnail(SIZES[size], resample=RESAMPLE, reducing_gap=REDUCING_GAP)
    return im


def thumb(src_path, out_path, size="md"):
    resize(src_path, size).save(out_path, quality=QUALITY)
    return out_path
