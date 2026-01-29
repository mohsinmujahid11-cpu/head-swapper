#!/bin/bash

echo "🚀 Starting Container..."

# Safety Check: Verify Network Volume is attached
if [ ! -d "/runpod-volume/models" ]; then
    echo "❌ CRITICAL ERROR: Network Volume not found at /runpod-volume/models"
    echo "👉 Ensure you attached the Network Volume and mounted it to '/runpod-volume' in the Template!"
    exit 1
fi

echo "✅ Network Volume detected. Models are ready."

# CRITICAL FIX: Create Input/Output directories for rp_handler.py
mkdir -p /ComfyUI/input /ComfyUI/output

# Start ComfyUI in background
python /ComfyUI/main.py --listen 127.0.0.1 --port 8188 &

echo "Waiting 30 seconds for ComfyUI initialization..."
sleep 30

echo "⚡ Starting RunPod Handler..."
python /rp_handler.py