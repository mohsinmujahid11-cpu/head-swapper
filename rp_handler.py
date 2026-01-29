import json
import base64
import time
import runpod
import requests
import os
import uuid

# 1. Load the Workflow Template
try:
    with open("workflow_api.json", "r") as f:
        WORKFLOW_TEMPLATE = json.load(f)
    print("✅ Workflow template loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load workflow_api.json: {e}")
    raise

def save_base64_image(b64_string: str, save_path: str):
    """Decodes a Base64 string and saves it as an image file."""
    try:
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]
        
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(b64_string))
    except Exception as e:
        raise Exception(f"Failed to decode base64 image: {str(e)}")

def handler(job):
    job_input = job.get("input", {})
    
    # 2. Generate Unique IDs (Stateless Concurrency)
    job_id = str(uuid.uuid4())
    input_dir = "/ComfyUI/input"
    output_dir = "/ComfyUI/output"
    
    # Unique filenames to prevent collisions
    head_filename = f"head_{job_id}.png"
    body_filename = f"body_{job_id}.png"
    
    head_path = os.path.join(input_dir, head_filename)
    body_path = os.path.join(input_dir, body_filename)
    
    # Track files for cleanup
    files_to_delete = [head_path, body_path]

    try:
        # 3. Get Base64 Inputs
        head_b64 = job_input.get("head_image")
        body_b64 = job_input.get("body_image")
        
        if not head_b64 or not body_b64:
            return {"error": "Missing head_image or body_image (Base64 strings required)"}

        # 4. Save Images to Disk
        save_base64_image(head_b64, head_path)
        save_base64_image(body_b64, body_path)

        # 5. Inject Filenames (The "Option B" Hook)
        workflow = json.loads(json.dumps(WORKFLOW_TEMPLATE))
        
        # We explicitly target the known Node IDs 448 & 449
        workflow["448"]["inputs"]["image"] = head_filename
        workflow["449"]["inputs"]["image"] = body_filename
        
        # 6. Execute via ComfyUI API
        try:
            prompt_req = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": workflow})
            prompt_req.raise_for_status()
            prompt_id = prompt_req.json().get("prompt_id")
        except Exception as err:
            return {"error": f"ComfyUI Connection Failed: {str(err)}"}
        
        # 7. Poll for Completion
        timeout = 300 
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            try:
                history = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}").json()
            except:
                continue
            
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                
                if "458" in outputs:
                    img_info = outputs["458"]["images"][0]
                    out_filename = img_info['filename']
                    out_path = f"{output_dir}/{out_filename}"
                    files_to_delete.append(out_path) # Mark output for deletion
                    
                    if os.path.exists(out_path):
                        with open(out_path, "rb") as f:
                            b64_result = base64.b64encode(f.read()).decode("utf-8")
                        return {"result": b64_result}
        
        return {"error": "Timeout: Generation took longer than 5 minutes"}
    
    except Exception as e:
        return {"error": f"Handler Crash: {str(e)}"}
    
    finally:
        # 8. CLEANUP (The "No Disk Bloat" Guarantee)
        for f in files_to_delete:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

runpod.serverless.start({"handler": handler})