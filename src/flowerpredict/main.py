import os
import logging
import tempfile

from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from datetime import datetime
from sklearn.linear_model import LogisticRegression


import tensorflow as tf
from models import Prediction
from utils import latest_model_version, load_model

IMAGE_RES = 224

def format_image(image):
    image = tf.image.resize(image, (IMAGE_RES, IMAGE_RES))/255.0
    return image

# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)

app = FastAPI()

@app.post("/predict")
def predict_hello(image_file: UploadFile = File(...)) -> Prediction:

    # Check the MIME type
    if image_file.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only JPEG files ar allowed")

    # Load .keras model
    latest_version = latest_model_version()
    logging.info(f"Latest version: {latest_version}")
    model_bytes = load_model(latest_version)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".keras") as temp_file:
        temp_file.write(model_bytes)
        temp_file_path = temp_file.name
    
    model = tf.keras.models.load_model(temp_file_path)
    logging.info(f"Model: {model.summary(show_trainable=True)}")

    # Load image_file
    image_bytes = image_file.file.read()
    test_image = tf.keras.utils.load_img(BytesIO(image_bytes), target_size=(IMAGE_RES, IMAGE_RES))
    test_image = tf.keras.utils.img_to_array(test_image)
    test_image = format_image(test_image)

    # Predict the image
    output = model.predict(tf.expand_dims(test_image, axis = 0), batch_size=1)
    logging.info(f"Output: {output}")

    # Calculate prediction probability & select corresponding flower label
    output = tf.nn.softmax(output)
    logging.info(f"Output: {output}")
    output_index = tf.argmax(output, axis=1).numpy()[0]
    flower_list = ['dandelion', 'daisy', 'tulips', 'sunflowers', 'roses']
    prediction = flower_list[int(output_index)]
    logging.info(f"Output: {output}")

    return Prediction(
        label=int(output_index),
        confidence=float(output[0][int(output_index)]),
        prediction=prediction,
        version=latest_version,
        version_iso=datetime.fromtimestamp(latest_version).isoformat()

    )    

