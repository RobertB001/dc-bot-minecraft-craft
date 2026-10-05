import numpy as np
from PIL import Image, ImageOps
from tf_keras.models import load_model


loaded_models = {}


def get_class(model_path, labels_path, image_path):
    if model_path not in loaded_models:
        loaded_models[model_path] = load_model(model_path, compile=False)
    model = loaded_models[model_path]

    with open(labels_path, "r", encoding="utf-8") as f:
        class_names = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

    image = Image.open(image_path).convert("RGB")
    image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)

    image_array = np.asarray(image).astype(np.float32)
    normalized = (image_array / 127.5) - 1
    data = np.expand_dims(normalized, axis=0)

    prediction = model.predict(data, verbose=0)
    index = int(np.argmax(prediction))
    confidence = float(prediction[0][index])

    return class_names[index], confidence