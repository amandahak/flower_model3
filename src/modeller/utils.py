import os
import logging
import zlib
import numpy as np
import pandas as pd

from base64 import b64decode
from io import StringIO
from PIL import Image
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from sklearn.linear_model import LogisticRegression

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

def deserialize_grayscale(compressed_b64:str, size=(20, 40), has_label=False) -> tuple[Image.Image, int]:
    """Decompress the base64 string and convert it to an image.
    """

    label=None

    # Base64 => bytes
    decoded = b64decode(compressed_b64)

    if has_label:
        # Extract the label
        label = int.from_bytes(decoded[-1:], byteorder="big")
        decoded = decoded[:-1]

    uncompressed = zlib.decompress(decoded)

    # Convert back to numpy array
    img = Image.fromarray(np.frombuffer(uncompressed, dtype=np.bool_).reshape(size))

    return img, label

def load_dataset(file_path="datasets/dataset.csv") -> str:
    """Load is as a raw string from the storage container.
    """
    logging.info(f"Loading dataset from {file_path}.")
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        # blob_client = container_client.get_blob_service_client(file_path)

        with container_client.get_blob_client(file_path) as blob_client:
            blob = blob_client.download_blob()
            content = blob.content_as_text()
            logging.info(f"Loaded # samples from {file_path}: {len(content.splitlines())}")
            return content

def get_all_from_queue() -> list[tuple[Image.Image, int]]:
    """Get all the images from the queue.
    """
    logging.info("Getting all images from the queue.")
    with get_queue_service_client() as queue_service_client:
        queue = queue_service_client.get_queue_client(os.environ["STORAGE_QUEUE"])
        messages = queue.receive_messages(messages_per_page=32)
        new_rows = []
        for msg in messages:
            logging.info(f"Processing message: {msg.id}")
            logging.info(f"Message content: {msg.content}")
            logging.info(f"Message type: {type(msg.content)}")
            img, label = deserialize_grayscale(msg.content, has_label=True)
            new_rows.append((img, label))
            queue.delete_message(msg)
        logging.info(f"Got {len(new_rows)} images from the queue.")
        return new_rows

def upload(csv_data:str, file_path:str):
    """Append the new data to the dataset.
    """
    logging.info("Uploading {type(csv_data)} to {file_path}.")
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        blob_client = container_client.get_blob_client(file_path)
        blob_client.upload_blob(csv_data, overwrite=True)
        logging.info(f"Upload complete for {file_path}.")

def images_to_csv(images: list[tuple[Image.Image, int]]) -> str:
    """Convert a list of images to a CSV string.
    """
    new_rows = []
    for img, label in images:
        # Convert the image to a binary string
        pixel_data = [str(int(x / 255)) for x in img.getdata()]
        pixel_csv = ",".join(pixel_data)
        new_rows.append(f"{pixel_csv},{label}")
    logging.info(f"The first incoming row: {new_rows[0][:25]}...")
    
    # Convert to a single newline-separated string
    new_rows = "\n".join(new_rows) + "\n"
    return new_rows

def train_model(dataset: str, model_version: int) -> LogisticRegression:
    """Train a model on the given dataset.
    """
    logging.info(f"Training the model on {len(dataset.splitlines())} samples.")
    df = pd.read_csv(StringIO(dataset), header=None)
    logging.info(f"Loaded {len(df)} samples from the dataset.")
    logging.info(f"Last row: {df.iloc[-1]}")
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    model = LogisticRegression()
    model.fit(X, y)

    return model

