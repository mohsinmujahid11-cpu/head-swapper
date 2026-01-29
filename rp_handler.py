import json
import base64
import time
import runpod
import requests
import os

# 1. Load workflow template at startup (Efficient)
try:
    with open("workflow_api.json", "r") as f:
        WORKFLOW_TEMPLATE = json.load(f)
    print("✅ Workflow template loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load workflow_api.json: {e}")
    raise

def download_or_save_image(image_source: str, save_path: str):
    """Support both URL and base64 data URI inputs."""
    try:
        if image_source.startswith("http"):
            # URL download
            response = requests.get(image_source, timeout=30)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(response.content)
        else:
            # Base64 (with or without data URI header)
            if "," in image_source:
                image_source = image_source.split(",", 1)[1]
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(image_source))
    except Exception as e:
        print(f"Error processing image: {e}")
        raise

def handler(job):
    job_input = job.get("input", {})
    
    # 2. Setup Input Directory
    input_dir = "/ComfyUI/input"
    os.makedirs(input_dir, exist_ok=True)
    
    # 3. Exact Filename Mapping (CRITICAL FOR YOUR JSON)
    # Node 448 expects: cut_00003_.png
    # Node 449 expects: ComfyUI_temp_rnpvx_00002_.png
    head_image_path = f"{input_dir}/cut_00003_.png"
    body_image_path = f"{input_dir}/ComfyUI_temp_rnpvx_00002_.png"
    
    # 4. Process Inputs
    try:
        head_source = job_input.get("head_image")
        body_source = job_input.get("body_image")
        
        if not head_source or not body_source:
            return {"error": "Missing head_image or body_image input"}

        download_or_save_image(head_source, head_image_path)
        download_or_save_image(body_source, body_image_path)
    except Exception as e:
        return {"error": f"Failed to process input images: {str(e)}"}
    
    # 5. Prepare Workflow
    workflow = json.loads(json.dumps(WORKFLOW_TEMPLATE))
    
    # 6. Execute via ComfyUI API
    try:
        prompt_response = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow})
        prompt_response.raise_for_status()
        prompt_id = prompt_response.json().get("prompt_id")
        
        if not prompt_id:
            return {"error": "No prompt_id returned from ComfyUI"}
        
        # 7. Poll with SAFETY TIMEOUT (Added from my version)
        timeout = 300 # 5 minutes max runtime
        start_time = time.time()
        
        while True:
            # Safety Break
            if time.time() - start_time > timeout:
                return {"error": "Timeout: Generation took longer than 300s"}

            time.sleep(1)
            history_response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}")
            
            if history_response.status_code != 200:
                continue
                
            history = history_response.json()
            if prompt_id not in history:
                continue
                
            outputs = history[prompt_id].get("outputs", {})
            
            # 8. Retrieve Output from Node 458 (SaveImage)
            if "458" in outputs:
                images = outputs["458"].get("images", [])
                if not images:
                    return {"error": "SaveImage node produced no images"}
                
                filename = images[0]["filename"]
                output_path = f"/ComfyUI/output/{filename}"
                
                if not os.path.exists(output_path):
                    return {"error": f"Output file not found: {output_path}"}
                
                with open(output_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                
                return {"result": encoded}
                
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}

runpod.serverless.start({"handler": handler})