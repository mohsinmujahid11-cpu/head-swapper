#!/bin/bash

# Move to ComfyUI custom_nodes directory
cd /ComfyUI/custom_nodes

echo "⬇️ Cloning Mandatory Custom Nodes (Slim Mode)..."

# Clone Qwen Image Edit
git clone --depth 1 https://github.com/Comfy-Org/Qwen-Image-Edit_ComfyUI.git
rm -rf Qwen-Image-Edit_ComfyUI/.git

# Clone AuraFlow
git clone --depth 1 https://github.com/huchenlei/ComfyUI-AuraFlow.git
rm -rf ComfyUI-AuraFlow/.git

# Clone Flux Kontext
git clone --depth 1 https://github.com/pamparamm/ComfyUI-Flux-Kontext-Image-Scale.git
rm -rf ComfyUI-Flux-Kontext-Image-Scale/.git

echo "✅ Setup Complete (Custom nodes only, no history bloat)"