import cv2
import matplotlib.pyplot as plt
import numpy as np

from PIL import Image

# Load document
pil_img = Image.open("sample-001.jpg").convert("RGB")

# PIL RGB -> OpenCV-compatible NumPy BGR
img = cv2.cvtColor(
    np.array(pil_img),
    cv2.COLOR_RGB2BGR
)

# Grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Edge detection
edges = cv2.Canny(gray, 100, 200)

# Display
fig, ax = plt.subplots(1, 2, figsize=(12, 6))

ax[0].imshow(pil_img)
ax[0].set_title("Original document")
ax[0].axis("off")

ax[1].imshow(edges, cmap="gray")
ax[1].set_title("OpenCV Canny edges")
ax[1].axis("off")

plt.tight_layout()
plt.show()

print("Edge density:", np.mean(edges > 0))