import tensorflow as tf
import numpy as np
from PIL import Image

MODEL_PATH = "model/keras_model.h5"

model = tf.keras.models.load_model(MODEL_PATH)

CLASS_NAMES = ["Hose", "Mütze", "Pullover"]

def preprocess_image(image):
    image = image.resize((224, 224))
    image = np.array(image)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image

def predict_category(image):
    processed = preprocess_image(image)
    prediction = model.predict(processed)
    predicted_class = np.argmax(prediction)
    confidence = np.max(prediction)

    if confidence < 0.6:
        return "Sonstiges"

    return CLASS_NAMES[predicted_class]
