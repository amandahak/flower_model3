import os
import time
import logging

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Decide if we're running in the cloud or locally
CLOUD = os.environ.get("USE_AZURE_CREDENTIAL", "false").lower() == "true"

# Having any of these missign should raise an exception
STORAGE_CONTAINER = os.environ["STORAGE_CONTAINER"]
STORAGE_QUEUE = os.environ["STORAGE_QUEUE"]

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

def container_exists(client: BlobServiceClient, container_name: str):
    containers = client.list_containers(name_starts_with=container_name)
    for container in containers:
        if container.name == container_name:
            return True
    return False

def queue_exists(client: QueueServiceClient, queue_name: str):
    queues = client.list_queues(name_starts_with=queue_name)
    for queue in queues:
        if queue.name == queue_name:
            return True
    return False

def create_timestamp_blob(client: BlobServiceClient, container_name: str):
    timestamp = int(time.time()) # Drop the decimal part
    blob_name = f"created-at-{timestamp}"
    with client.get_blob_client(container_name, blob_name) as blob_client:
        blob_client.upload_blob(b"Hello, World!", overwrite=True)

def create_timestamp_queue(client: QueueServiceClient, queue_name: str):
    timestamp = int(time.time()) # Drop the decimal part
    queue_client = client.get_queue_client(queue_name)
    queue_client.send_message(f"Hello, World! {timestamp}")

if __name__ == "__main__":

    # Set the logging level for this script
    logging.basicConfig(level=logging.INFO)

    # Set the logging level for all azure-* libraries
    azure_logger = logging.getLogger('azure')
    azure_logger.setLevel(logging.WARNING)

    # For 1 hour (60 minutes), create a new blob every 10 seconds
    for i in range(360):

        with get_blob_service_client() as blob_service_client:

            if not container_exists(blob_service_client, STORAGE_CONTAINER):
                raise Exception(f"Container {STORAGE_CONTAINER} does not exist.")

            create_timestamp_blob(blob_service_client, STORAGE_CONTAINER)
            logging.info("Created a new blob.")


        with get_queue_service_client() as queue_service_client:
            if not queue_exists(queue_service_client, STORAGE_QUEUE):
                raise Exception(f"Queue {STORAGE_QUEUE} does not exist.")

            create_timestamp_queue(queue_service_client, STORAGE_QUEUE)
            logging.info("Created a new message.")
        
        logging.info(f"Sleeping for 10 seconds. {i} out of 360.")
        time.sleep(10)
