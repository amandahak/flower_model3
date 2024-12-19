import joblib
import time
import logging
import time

from datetime import datetime

from io import BytesIO

from utils import (
    n_images_waiting,
    load_dataset,
    get_all_from_queue,
    images_to_csv,
    upload,
    train_model,
)

# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.WARNING)

while True:
    n_images = n_images_waiting()
    if n_images > 1:
        # Use current UNIX time as the version of the model
        model_version = int(time.time())
        iso_time = datetime.fromtimestamp(model_version).isoformat()
        logging.info(
            f"Found {n_images} images in Queue at {model_version} ({iso_time})."
        )

        # Load the existing dataset
        current_dataset = load_dataset()

        # Get all the images from the queue, deleting them from the queue
        # Note that this is a risk; if the following process fails, the images are lost
        new_images = get_all_from_queue()

        # Convert each tuple(Image, int) into a CSV-row string
        new_rows = images_to_csv(new_images)

        logging.info(f"First row of new data: {new_rows.splitlines()[0]}")
        logging.info(f"Second row of new data: {new_rows.splitlines()[1]}")

        # Sum the new data to the existing dataset
        new_dataset = current_dataset + new_rows

        # Overwrite the dataset with the new data
        upload(new_dataset, "datasets/dataset.csv")

        model = train_model(new_dataset, model_version)

        # Materialize the model to bytes first
        with BytesIO() as data:
            joblib.dump(model, data)
            data.seek(0)
            model = data.read()

        # Then upload the model to Azure Storage
        upload(model, f"models/model_{model_version}.joblib")

        logging.info(f"Model version {model_version} is now available.")
    else:
        logging.info("No images to process.")

    time.sleep(10)
