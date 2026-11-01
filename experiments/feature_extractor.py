
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from ela_analyzer import calculate_ela

IMAGE_PATH = "sample-001.jpg"


def extract_features(image):
    rgb = np.asarray(image.convert("RGB"))

    # Convert RGB to grayscale using OpenCV
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Canny edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Sobel gradients
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    gradient = np.sqrt(gx**2 + gy**2)

    # ELA statistics
    ela_map, ela_visual = calculate_ela(image)

    # RGB statistics
    rgb_float = rgb.astype(np.float32)
    mean_rgb = rgb_float.mean(axis=(0, 1))
    std_rgb = rgb_float.std(axis=(0, 1))

    height, width = gray.shape

    features = {
        "ela_mean": float(ela_map.mean()),
        "ela_std": float(ela_map.std()),
        "edge_density": float(np.mean(edges > 0)),
        "mean_gradient": float(gradient.mean()),
        "brightness": float(gray.mean()),
        "grayscale_std": float(gray.std()),
        "red_mean": float(mean_rgb[0]),
        "green_mean": float(mean_rgb[1]),
        "blue_mean": float(mean_rgb[2]),
        "red_std": float(std_rgb[0]),
        "green_std": float(std_rgb[1]),
        "blue_std": float(std_rgb[2]),
        "aspect_ratio": float(width / height),
        "width": width,
        "height": height
    }

    return features, edges


def main():
    image = Image.open(IMAGE_PATH).convert("RGB")

    features, edges = extract_features(image)

    print("\nExtracted Features:")
    for name, value in features.items():
        print(f"{name:20s}: {value}")

    plt.imshow(edges, cmap="gray")
    plt.title("OpenCV Canny Edge Map")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    main()
