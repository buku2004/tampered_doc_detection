
import io
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

IMAGE_PATH = "sample-001.jpg"


def calculate_ela(image, quality=90):
    image = image.convert("RGB")

    # Recompress image as JPEG
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    recompressed = Image.open(buffer).convert("RGB")

    # Pixel difference
    original_arr = np.asarray(image, dtype=np.int16)
    recompressed_arr = np.asarray(recompressed, dtype=np.int16)

    difference = np.abs(original_arr - recompressed_arr)
    ela_map = difference.mean(axis=2)

    # Enhance for visualization
    max_value = ela_map.max()

    if max_value > 0:
        ela_visual = np.clip(
            ela_map * (255.0 / max_value), 0, 255
        ).astype(np.uint8)
    else:
        ela_visual = np.zeros_like(ela_map, dtype=np.uint8)

    return ela_map, ela_visual


def main():
    image = Image.open(IMAGE_PATH).convert("RGB")

    ela_map, ela_visual = calculate_ela(image)

    print("ELA mean:", ela_map.mean())
    print("ELA std:", ela_map.std())

    plt.imshow(ela_visual, cmap="gray")
    plt.title("ELA Visualization")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    main()
