# Base image (Keep devel for custom node compilation support)
FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1

# Optimization: Added --no-install-recommends to skip useless extras
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    nano \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

# Clone ComfyUI (Optimization: --depth 1 and remove .git folder)
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git \
    && rm -rf ComfyUI/.git

# Install Dependencies (Optimization: --no-cache-dir)
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r /requirements.txt --no-cache-dir
RUN pip install -r ComfyUI/requirements.txt --no-cache-dir

# Install Custom Nodes
COPY setup.sh /setup.sh
RUN sed -i 's/\r$//' /setup.sh && chmod +x /setup.sh && /setup.sh

# CRITICAL: Connects ComfyUI to the Network Volume
COPY extra_model_paths.yaml /ComfyUI/extra_model_paths.yaml

# Copy Scripts & Workflow
COPY rp_handler.py /rp_handler.py
COPY workflow_api.json /workflow_api.json
COPY start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

CMD ["/start.sh"]