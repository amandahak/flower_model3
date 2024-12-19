# Use the official Python image as a base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the local code to the container image
COPY app.py ./

EXPOSE 80

HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0"]
