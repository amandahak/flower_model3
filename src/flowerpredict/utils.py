import zlib
import numpy as np
import os
import logging
import joblib
from tensorflow.keras.models import load_model
import tensorflow as tf


from io import BytesIO
from azure.storage.blob import BlobServiceClient
from base64 import b64decode, b64encode
from PIL import Image
from datetime import datetime
from functools import lru_cache

# Are we running in the cloud?
CLOUD = os.environ.get("USE_AZURE_CREDENTIAL", "false").lower() == "true"

# def deserialize_grayscale(compressed_b64:str, size=(20, 40), has_label=False) -> tuple[Image.Image, int]:
#     """Decompress the base64 string and convert it to an image.
#     """

#     label=None

#     # Base64 => bytes
#     decoded = b64decode(compressed_b64)

#     if has_label:
#         # Extract the label
#         label = int.from_bytes(decoded[-1:], byteorder="big")
#         decoded = decoded[:-1]

#     uncompressed = zlib.decompress(decoded)

#     # Convert back to numpy array
#     img = Image.fromarray(np.frombuffer(uncompressed, dtype=np.bool_).reshape(size))

#     return img, label

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


def latest_model_version() -> int:
    """
    Retrieve the latest model version based on the Unix timestamp in the model file name.
    If no Unix-formatted models are found, default to 'model_1.keras'.
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
            logging.info("No Unix-formatted model found, defaulting to model_1.keras")
            return 1

@lru_cache(maxsize=5)
def load_model(version:int):
    # Find the latest model from /models folder in the storage container
    # The model name follows the pattern model_{unix_seconds}.keras
    with get_blob_service_client() as blob_service_client:
        container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
        blob_client = container_client.get_blob_client(f"models/model_{version}.keras")
        logging.info(f"Loading model version {version}.")

        with BytesIO() as data:
            blob_client.download_blob().readinto(data)
            data.seek(0)
            return data.read()
