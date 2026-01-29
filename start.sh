#!/bin/bash

echo "🚀 Starting Container..."

# 1. Safety Check
if [ ! -d "/runpod-volume/models" ]; then
    echo "❌ CRITICAL ERROR: Network Volume not found at /runpod-volume/models"
    echo "👉 Check your RunPod Template 'Volume Mount Path'"
    exit 1
fi

# 2. SELECTIVE CACHE STRATEGY (Safe & Fast)
echo "🔗 Linking HuggingFace Cache to Volume..."
mkdir -p /runpod-volume/.cache/huggingface
rm -rf /root/.cache/huggingface
mkdir -p /root/.cache
ln -s /runpod-volume/.cache/huggingface /root/.cache/huggingface

# 3. Create Input/Output directories
mkdir -p /ComfyUI/input /ComfyUI/output

# 4. Start ComfyUI
echo "🔄 Starting ComfyUI..."
python /ComfyUI/main.py --listen 127.0.0.1 --port 8188 &

# 5. Health Check (Robust)
echo "⏳ Waiting for ComfyUI API..."
timeout 90s bash -c 'until curl -s http://127.0.0.1:8188/history > /dev/null; do sleep 2; done'
if [ $? -ne 0 ]; then
    echo "❌ ComfyUI failed to start within 90 seconds."
    exit 1
fi

# 6. Start Handler
echo "⚡ Starting RunPod Handler..."
python /rp_handler.py