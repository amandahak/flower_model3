#!/bin/bash

set -e

# The scripts/ is hard-coded to be one-level up from the current directory
PROJECT_DIR=$(cd $(dirname $0)/..; pwd)

# Check that ARG 1 and ARG 2 are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <APP_NAME> <IMAGE_VERSION>"
    exit 1
fi

APP_DIR="$PROJECT_DIR/src/$1"
IMAGE_VERSION=$2

# Check that app directory exists
if [ ! -d "$PROJECT_DIR/src/$1" ]; then
    echo "App directory $PROJECT_DIR/src/$1 does not exist. Check the APP_NAME argument."
    exit 1
fi

# # Get output in Terraform Azure Container Registry module
cd $PROJECT_DIR/infra/tf/container_registry
ACR=$(terraform output -raw registry_name)


# Change to build directory
cd $PROJECT_DIR/src/$1

# Build the image
az acr build --registry $ACR --image $1:$IMAGE_VERSION --file $PROJECT_DIR/src/$1/Dockerfile  .
