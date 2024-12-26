import os
import logging
import zlib
import numpy as np
import pandas as pd
import pathlib
import zipfile
import json
from datetime import datetime

from base64 import b64decode
from io import BytesIO, StringIO
from PIL import Image
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from sklearn.linear_model import LogisticRegression
import tensorflow as tf
from tensorflow.keras import preprocessing
from functools import lru_cache

# Are we running in the cloud?
CLOUD = os.environ.get("USE_AZURE_CREDENTIAL", "false").lower() == "true"

def get_blob_service_client():
    """
    The STORAGE_CONNECTION_STRING is only set up when running in the cloud. 
    If it's not set, we're running locally with Azurite.
    """
    if CLOUD:
        from azure.identity import DefaultAzureCredential # type: ignore
        credential = DefaultAzureCredential()
        account_url = os.environ["STORAGE_BLOB_URL"]
        return BlobServiceClient(account_url=account_url, credential=credential)
    else:
        return BlobServiceClient.from_connection_string(os.environ["STORAGE_CONNECTION_STRING"])
    
def get_queue_service_client():
    """
    The STORAGE_CONNECTION_STRING is only set up when running in the cloud. 
    If it's not set, we're running locally with Azurite.
    """
    if CLOUD:
        from azure.identity import DefaultAzureCredential # type: ignore
        credential = DefaultAzureCredential()
        account_url = os.environ["STORAGE_QUEUE_URL"]
        return QueueServiceClient(account_url=account_url, credential=credential)
    else:
        return QueueServiceClient.from_connection_string(os.environ["STORAGE_CONNECTION_STRING"])
    

# Check how many messages are in the queue
def n_images_waiting() -> int:
    with get_queue_service_client() as queue_client:
        queue = queue_client.get_queue_client(os.environ["STORAGE_QUEUE"])
        queue_properties = queue.get_queue_properties()
        message_count = queue_properties.approximate_message_count
        logging.info(f"Labeled images waiting in queue: {message_count}")
        return message_count


# Function to check latest model version
def latest_model_version() -> int:
    """
    Retrieve the latest model version based on the Unix timestamp in the model file name.
    If no Unix-formatted models are found, default to 'flowers_1.keras'.
    """
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        blobs = container_client.list_blobs(name_starts_with="models/")

        model_versions = []

        for blob in blobs:
            try:
                # Attempt to extract the Unix timestamp from the model name
                version = int(blob.name.split("_")[1].split(".")[0])
                model_versions.append(version)
            except (IndexError, ValueError):
                logging.warning(f"Skipping non-standard model name: {blob.name}")

        if model_versions:
            latest = max(model_versions)
            unix_to_iso = datetime.fromtimestamp(latest).isoformat()
            logging.info(f"latest_model_version() seeing: {latest} created at {unix_to_iso}")
            return latest
        else:
            # Fallback to default model name
            logging.info("No Unix-formatted model found, defaulting to flowers_1.keras")
            return 1

# Function to load the wanted model version
@lru_cache(maxsize=5)
def load_model(version:int):
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        blob_client = container_client.get_blob_client(f"models/flowers_{version}.keras")
        logging.info(f"Loading model version {version}.")
        # Download the blob content into memory
        blob_data = blob_client.download_blob()
        # If it's a binary file, you can read it directly as bytes
        file_bytes = blob_data.readall()
        return file_bytes


def load_valdata():
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        blob_client = container_client.get_blob_client("datasets/val_data.zip")

        os.makedirs('./val/', exist_ok=True)
        target_folder = pathlib.Path('./val/')
        blob_stream = blob_client.download_blob()
        zip_data = blob_stream.readall() # Get the entire blob content as bytes

        # Open the zip file from the in-memory bytes and extract it
        with zipfile.ZipFile(BytesIO(zip_data), mode="r") as archive:
            print(f"Extracting contents to {target_folder}...")
            archive.extractall(target_folder)
            print("Extraction complete!")

        return None


# Function to resize training images
def format_image(image):
    IMAGE_RES = 224
    image = tf.image.resize(image, (IMAGE_RES, IMAGE_RES))
    return image

# Function to read training data from queue and blob storage
def get_all_from_queue() -> list[tuple[Image.Image, int]]:
    # Get all images from the queue
    logging.info("Getting all images from the queue.")

    with get_queue_service_client() as queue_service_client:
        queue = queue_service_client.get_queue_client(os.environ["STORAGE_QUEUE"])
        messages = queue.receive_messages(messages_per_page=32)
        new_rows = []

        for msg in messages:
            # Get info from the queue message
            message_content = json.loads(msg.content)
            blob_name = message_content.get("blob_name")
            label = message_content.get("label")

            logging.info(f"Processing message: {msg.id}")
            logging.info(f"Message name: {blob_name}")
            logging.info(f"Message label: {label}")

            # Download corresponding image from blob storage
            with get_blob_service_client() as blob_service_client:
                container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
                blob_client = container_client.get_blob_client(blob_name)

                blob_data = blob_client.download_blob()
                # If it's a binary file, you can read it directly as bytes
                file_bytes = blob_data.readall()
                image = preprocessing.image.load_img(BytesIO(file_bytes))
                image = format_image(image)

                # Delete the blob after downloading
                blob_client.delete_blob()
        
            # Add [image, label] pair to training data list
            new_rows.append((image, label))
            # Delete message from the queue
            queue.delete_message(msg)

    logging.info(f"Got {len(new_rows)} images from the queue. ")
    return new_rows

# Function to upload new model to the storage container
def upload(model_file, file_path:str):
    logging.info("Uploading model to the storage container")
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        with open(model_file, "rb") as data:
            blob_client = container_client.get_blob_client(file_path)
            blob_client.upload_blob(data, overwrite=True)
            logging.info(f"Upload complete for {model_file}.")
