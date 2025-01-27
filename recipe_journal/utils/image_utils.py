"""Image management module for compressing image files."""

from django.core.files import File
from io import BytesIO
from PIL import Image

def compress_image(image, quality=50):
    """
    Compresses an image by reducing its quality and returns a new File object.

    Parameters:
    - image (File): The image to compress.
    - quality (int, optional): The compression quality level (between 1 and 100).

    Returns:
    - File: A new compressed image as a File object.
    """
    img = Image.open(image)
    rgb_img = img.convert("RGB")
    img_io = BytesIO()
    rgb_img.save(img_io, format=img.format, quality=quality)

    new_image = File(img_io, name=image.name)
    return new_image