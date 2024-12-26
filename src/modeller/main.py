
import time
import logging
import os
import tempfile
import tensorflow as tf
import keras
import shutil

from keras.preprocessing import image
from tensorflow.keras import preprocessing
from datetime import datetime
from utils import *


BLOB_CONTAINER_NAME = "uploaded-files"
IMAGE_RES = 224

# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.WARNING)

# Load the validation data and rename the folders to get the same order as in the model
load_valdata()

flower_list =  ['dandelion', 'daisy', 'tulips', 'sunflowers', 'roses']
for old_name, new_name in [
    ('./val/dandelion', './val/0_dandelion'),
    ('./val/daisy', './val/1_daisy'),
    ('./val/tulips', './val/2_tulips'),
    ('./val/sunflowers', './val/3_sunflowers'),
    ('./val/roses', './val/4_roses'),
]:
    if os.path.exists(new_name):
        logging.info(f"Directory {new_name} already exists. Skipping rename.")
        continue
    if os.path.exists(old_name):
        shutil.move(old_name, new_name)
        logging.info(f"Renamed {old_name} to {new_name}.")

# Running the main loop

while True:
    n_images = n_images_waiting()
    # If there are more than N images in the queue, let's train the model
    if n_images > 4:

        # Load .keras model
        latest_version = latest_model_version()
        logging.info(f"Latest version: {latest_version}")
        model_bytes = load_model(latest_version)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".keras") as temp_file:
            temp_file.write(model_bytes)
            temp_file_path = temp_file.name
        
        model = tf.keras.models.load_model(temp_file_path)
        logging.info(f"Model: {model.summary(show_trainable=True)}")
        
        # Use current UNIX time as the version of the model
        model_version = int(time.time())
        iso_time = datetime.fromtimestamp(model_version).isoformat()
        logging.info(f"Found {n_images} images in Queue at {model_version} ({iso_time}).")

        # Read all messages from queue and load corresponding images from blob
        # Then delete messages from queue & images from blob
        data_pairs = get_all_from_queue()

        # Get all the images from the queue, deleting them from the queue
        # Note that this is a risk; if the following process fails, the images are lost
        new_images = get_all_from_queue()

        # Separate images and labels
        images = [pair[0] for pair in data_pairs] # List of image arrays
        labels = [pair[1] for pair in data_pairs] # List of labels

        logging.info(f"len(data_pairs): {len(data_pairs)}.")

        # If queue reading was succesfull, we can train the model
        if len(data_pairs) > 0:
            
            # Convert to tf.data.Datasets
            train_ds = tf.data.Dataset.from_tensor_slices((images, labels))
            train_ds = train_ds.batch(len(data_pairs)).shuffle(len(data_pairs))

            # Create validation dataset from loaded validation data
            val_ds = keras.utils.image_dataset_from_directory(
                './val/',
                validation_split=None,
                seed=123,
                image_size=(IMAGE_RES, IMAGE_RES),
                batch_size=32                
                    )

            # Image preprocessing
            def format_train_image(image, label):
                image = tf.image.resize(image, (IMAGE_RES, IMAGE_RES))/255.0 # Normalization is needed
                return image, label
            
            def format_val_image(image, label):
                image = tf.image.resize(image, (IMAGE_RES, IMAGE_RES))/255.0
                return image, label
            
            train_batches = train_ds.map(format_train_image).prefetch(tf.data.AUTOTUNE)
            val_batches = val_ds.map(format_val_image).prefetch(tf.data.AUTOTUNE)

            # Train the model
            history = model.fit(train_batches,
                        epochs=3,
                        batch_size=len(data_pairs),
                        )

            # Evaluate the model
            model.evaluate(val_batches, verbose=2)

            # Upload the model to Azure Storage
            model.save("temp_model.keras")
            upload("temp_model.keras", f"models/model_{model_version}.keras")
    
    else: 
        logging.info("No images to process")

    time.sleep(10)
