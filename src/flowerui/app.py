import requests
import os
import logging
import streamlit as st
import uuid
import io
import json

#from PIL import Image
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient


# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)

# Decide if we're running in the cloud or locally
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



URL = os.environ["PREDICT_URL"]

if not URL:
    raise ValueError("Environment variable 'PREDICT_URL' is not set. Please configure it.")




def call_predict(image) -> dict|None:
    try:
        files = {"image_file": (image_file.name, image_file, "image/jpg")}
        response = requests.post(URL, files=files)

    except requests.exceptions.ConnectionError as e:
        st.warning("Failed to connect to the backend.")
        return None

    # Handle response
    if response.ok:
        st.write("Prediction: ", response.json())
    else:
        st.warning("Failed to get prediction from the backend.")
        st.write(response.text)
        return None

    return response.json()

# STREAMLIT UI ---------------------------------------------------------------------------

st.title("Upload an image for Prediction")

# Streamlit file uploader
image_file = st.file_uploader("Pick a file", type=["jpg", "jpeg"])

# Ask user to predict the image using REST API backend model
if image_file is not None:

    # Visualize the image
    st.image(image_file, caption = "Uploaded image")

    # Predict the image -button
    if st.button("Predict"):
        predict_json = call_predict(image_file)

    st.write("Not happy with the result? Submit the image with a correct label, so we can improve the model!")

    # Submit the image for training
    flower_list = ['dandelion', 'daisy', 'tulips', 'sunflowers', 'roses']
    label = st.selectbox("Label: ", flower_list)
    label_index = flower_list.index(label)

    # Submit-button
    if st.button("Submit for training"):

        # Upload the image to Azure Blob storage

        with get_blob_service_client() as blob_service_client:
            # Generate unique filename
            blob_name = f"{uuid.uuid4()}_{image_file.name}"

            # Get the container and blob clients
            container_client = blob_service_client.get_container_client(os.environ["STORAGE_CONTAINER"])
            blob_client = container_client.get_blob_client(blob_name)

            # Upload file to Azure Blob Storage
            with io.BytesIO(image_file.getvalue()) as uploaded_file:
                blob_client.upload_blob(uploaded_file.read(), overwrite=True)

                print(f"File: {blob_name} loaded to blob storage.")

        # Send image name and label to the queue as a json structure
        with get_queue_service_client() as queue_service_client:

            with queue_service_client.get_queue_client(os.environ["STORAGE_QUEUE"]) as queue_client:

                # Construct the queue message with blob URL and label
                message = {
                    "blob_name": blob_name,
                    "label": label_index
                }
                queue_client.send_message(json.dumps(message))

                logging.info(f"Message ({blob_name}) and ({label_index}) sent to Queue ({os.environ['STORAGE_QUEUE']})")
                st.write(f"Sent: {blob_name} as {label_index}")
