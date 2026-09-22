import logging

from PIL import Image

logger = logging.getLogger(__name__)

SIZES = {"sm": (160, 160), "md": (480, 480), "lg": (1200, 1200)}

# Thumbnail sharpness is a property of this file, not of whichever default the
# installed Pillow carries. Image.thumbnail()'s own default has been BICUBIC,
# but a default is the library's to change and a change here is visible to
# customers and invisible in review. See CLAUDE.md, "Pillow is pinned at
# 10.2.0".
RESAMPLE = Image.Resampling.BICUBIC


def thumb(src_path, out_path, size="md"):
    im = Image.open(src_path)
    im.thumbnail(SIZES[size], resample=RESAMPLE)
    im.save(out_path, quality=88)
    logger.debug("rendered %s -> %s (%s)", src_path, out_path, size)
    return out_path
