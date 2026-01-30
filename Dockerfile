# Base image (Keep devel for custom node compilation support)
FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to ComfyUI (Standard Convention)
WORKDIR /ComfyUI

# Clone ComfyUI (shallow clone, remove .git)
# Note: We clone into the current directory (.) because WORKDIR is already set
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git . \
    && rm -rf .git

# COPY your custom requirements (Renamed to prevent overwriting ComfyUI's file)
COPY requirements.txt requirements_custom.txt

# Install dependencies (ComfyUI's first, then Yours)
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir \
        -r requirements.txt \
        -r requirements_custom.txt

# Install Custom Nodes
COPY setup.sh .
RUN sed -i 's/\r$//' setup.sh && chmod +x setup.sh && ./setup.sh

# Connect to Network Volume
COPY extra_model_paths.yaml .

# Copy scripts (Relative paths now work perfectly)
COPY rp_handler.py .
COPY workflow_api.json .
COPY start.sh .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

CMD ["./start.sh"]