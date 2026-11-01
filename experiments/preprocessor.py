
from PIL import Image, ImageFilter, ImageOps

IMAGE_PATH = "sample-001.jpg"


def preprocess_image(image):
    # Handle transparency
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")

    # Resize if larger than 2048 pixels
    if max(image.size) > 2048:
        image.thumbnail(
            (2048, 2048),
            Image.Resampling.LANCZOS
        )

    # Mild blur
    image = image.filter(
        ImageFilter.GaussianBlur(radius=0.5)
    )

    # Contrast enhancement
    image = ImageOps.autocontrast(image, cutoff=1)

    return image


def main():
    original = Image.open(IMAGE_PATH)
    processed = preprocess_image(original)

    processed.save("preprocessed.png")

    print("Original:", original.size)
    print("Processed:", processed.size)
    print("Saved: preprocessed.png")


if __name__ == "__main__":
    main()
