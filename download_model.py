import os
import urllib.request
import shutil
import sys

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_DIR = "models"
MODEL_NAME = "hand_landmarker.task"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

def download_model():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"Created directory: {MODEL_DIR}")

    if os.path.exists(MODEL_PATH):
        print(f"Model already exists at: {MODEL_PATH}")
    else:
        print(f"Downloading model from {MODEL_URL}...")
        try:
            with urllib.request.urlopen(MODEL_URL) as response, open(MODEL_PATH, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading model: {e}")
            sys.exit(1)

def update_config():
    config_path = "config.py"
    if not os.path.exists(config_path):
        print(f"Warning: {config_path} not found. Skipping config update.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        updated = False
        for line in lines:
            if line.startswith("HAND_BACKEND ="):
                new_lines.append('HAND_BACKEND = "TASKS"\n')
                updated = True
            elif line.startswith("TASKS_MODEL_PATH ="):
                new_lines.append(f'TASKS_MODEL_PATH = "{MODEL_PATH.replace(os.sep, "/")}"\n')
            else:
                new_lines.append(line)
        
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"Updated {config_path} to use TASKS backend.")
        else:
            print(f"Warning: Could not find HAND_BACKEND in {config_path}.")

    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    print("--- Setting up MediaPipe Tasks Model ---")
    download_model()
    update_config()
    print("--- Setup Complete ---")
    print("You can now run 'python main.py' to start the game with the new backend.")
