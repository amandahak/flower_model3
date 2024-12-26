import os
import logging

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from azure.core.exceptions import ResourceExistsError

# Decide if we're running in the cloud or locally
CLOUD = os.environ.get("USE_AZURE_CREDENTIAL", "false").lower() == "true"

# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)

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
    
if __name__ == "__main__":

    # Having any of these missign should raise an exception
    STORAGE_CONTAINER = os.environ["STORAGE_CONTAINER"]
    STORAGE_QUEUE = os.environ["STORAGE_QUEUE"]

    with get_blob_service_client() as blob_service_client:

        # Create the storage container if it doesn't exist
        try:
            blob_service_client.create_container(STORAGE_CONTAINER)
        except ResourceExistsError:
            print(f"Container {STORAGE_CONTAINER} already exists.")
        else:
            print(f"Container {STORAGE_CONTAINER} created.")

    with get_queue_service_client() as queue_service_client:

        # Create the storage queue if it doesn't exist
        try:
            queue_service_client.create_queue(STORAGE_QUEUE)
        except ResourceExistsError:
            print(f"Queue {STORAGE_QUEUE} already exists.")
        else:
            print(f"Queue {STORAGE_QUEUE} created.")

    # Upload following files to the storage container
    files = [
        ("models/", "flowers_1.keras"),
        ("datasets/", "val_data.zip"),
    ]

    with get_blob_service_client() as blob_service_client:
        for prefix, file in files:
            with open(file, "rb") as data:
                blob_client = blob_service_client.get_blob_client(STORAGE_CONTAINER, prefix + file)
                blob_client.upload_blob(data, overwrite=True)
                logging.info(f"Uploaded {prefix + file} to {STORAGE_CONTAINER}.")