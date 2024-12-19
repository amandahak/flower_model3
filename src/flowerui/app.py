import requests
import os
import logging
import streamlit as st

#from PIL import Image
from azure.storage.queue import QueueServiceClient


# Set the logging level for this script
logging.basicConfig(level=logging.INFO)

# Set the logging level for all azure-* libraries
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)

# Decide if we're running in the cloud or locally
CLOUD = os.environ.get("USE_AZURE_CREDENTIAL", "false").lower() == "true"

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
        with get_queue_service_client() as queue_service_client:
            with queue_service_client.get_queue_client(os.environ["STORAGE_QUEUE"]) as queue_client:
                compressed_b64 = [image_file, label_index]
                queue_client.send_message(compressed_b64)

                logging.info(f"Message ({label}) as ({compresssed_b64}) sent to Queue ({os.environ['STORAGE_QUEUE']})")
                st.write(f"Sent: {compressed_b64} as {label_index}")
