#!/bin/bash

# Daily Intensive Reading Backend Startup Script

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate crew

# Set working directory
cd /home/ubuntu/github/daily_intensive_reading_backend

# Start gunicorn with appropriate settings
gunicorn -w 4 \
  -b 0.0.0.0:5000 \
  --timeout 600 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --log-level info \
  app.app:app
