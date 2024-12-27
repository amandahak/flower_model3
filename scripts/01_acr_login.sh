#!/bin/bash

set -e

# The scripts/ is hard-coded to be one-level up from the current directory
PROJECT_DIR=$(cd $(dirname $0)/..; pwd)

# Change directory to the Terraform Azure Container Registry module
cd $PROJECT_DIR/infra/tf/container_registry

# Fetch Azure Container Registry credentials using Terraform output
acr_name=$(terraform output -raw registry_name)

# Use the fetched credentials to log in to Azure Container Registry
echo "Logging in to Azure Container Registry..."
az acr login --name $acr_name --expose-token

# Output message indicating successful login
echo "Successfully logged in to Azure Container Registry."
