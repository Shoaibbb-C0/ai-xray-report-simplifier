from PIL import Image
import numpy as np
import torch
from simple_cnn import SimpleCNN


def resize_with_padding(image, target_size=224):
    image_copy = image.copy()

    image_copy.thumbnail((target_size, target_size))

    canvas = Image.new("L", (target_size, target_size), 0)

    x = (target_size - image_copy.width) // 2
    y = (target_size - image_copy.height) // 2

    canvas.paste(image_copy, (x, y))

    return canvas


from pathlib import Path

_image_path = Path(__file__).parent / "sample_image1.jpg"
if not _image_path.exists():
    _image_path = Path("ml/sample_image1.jpg")

image = Image.open(_image_path)

gray_image = image.convert("L")

resized_image = resize_with_padding(gray_image)

image_array = np.array(resized_image)

normalized_array = image_array.astype(np.float32) / 255.0

image_tensor = torch.from_numpy(normalized_array)

image_tensor = image_tensor.unsqueeze(0)

batched_tensor = image_tensor.unsqueeze(0)

print("Original size:", gray_image.size)
print("Final size:", resized_image.size)
print("Tensor shape:", image_tensor.shape)
print("Batch shape:", batched_tensor.shape)

model = SimpleCNN()
output = model(batched_tensor)
print(output.shape)
print(output)

predicted_class = torch.argmax(output, dim=1)
print(predicted_class.item())