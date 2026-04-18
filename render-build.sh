#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running migrations..."
flask db upgrade

echo "Build complete."
