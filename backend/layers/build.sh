#!/bin/bash
# Build script for Lambda layers

set -e

echo "Building Lambda layer..."

# Create layer directory structure
mkdir -p python/lib/python3.11/site-packages

# Install dependencies
pip install -r requirements.txt -t python/lib/python3.11/site-packages

# Create zip file for layer
zip -r lambda-layer.zip python

echo "Lambda layer built successfully: lambda-layer.zip"
echo "Upload this file to AWS Lambda Layers"
