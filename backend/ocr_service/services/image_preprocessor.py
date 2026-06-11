import io
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Full image preprocessing pipeline for OCR optimization.
    Returns preprocessed image bytes.
    """
    image = Image.open(io.BytesIO(image_bytes))

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = resize_image(image)
    image = enhance_contrast(image)
    image = denoise_image(image)
    image = to_grayscale(image)
    image = binarize_image(image)

    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def resize_image(image: Image.Image, target_dpi: int = 300) -> Image.Image:
    """Resize image to ensure minimum resolution for OCR."""
    width, height = image.size
    if width < 1500 or height < 2000:
        scale = max(1500 / width, 2000 / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    return image


def enhance_contrast(image: Image.Image) -> Image.Image:
    """Enhance image contrast for better OCR."""
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    return image


def denoise_image(image: Image.Image) -> Image.Image:
    """Apply denoising filter."""
    image = image.filter(ImageFilter.MedianFilter(size=3))
    return image


def to_grayscale(image: Image.Image) -> Image.Image:
    """Convert to grayscale."""
    return image.convert("L")


def binarize_image(image: Image.Image) -> Image.Image:
    """Apply adaptive thresholding for binarization."""
    try:
        import cv2
        img_array = np.array(image)
        binary = cv2.adaptiveThreshold(
            img_array,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        return Image.fromarray(binary)
    except ImportError:
        threshold = 128
        return image.point(lambda p: 255 if p > threshold else 0, mode="1").convert("L")


def deskew_image(image: Image.Image) -> Image.Image:
    """Attempt to correct image skew."""
    try:
        import cv2
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))

        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) < 10:
                (h, w) = img_array.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    img_array, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                return Image.fromarray(rotated)
    except Exception as e:
        print(f"Deskew failed: {str(e)}")

    return image


def preprocess_for_table_extraction(image_bytes: bytes) -> bytes:
    """Preprocess specifically for table/line extraction."""
    image = Image.open(io.BytesIO(image_bytes))

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = resize_image(image)

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
