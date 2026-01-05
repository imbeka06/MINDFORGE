import os
import json
import shutil
import gc
import time 

DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_projects():
    ensure_data_dir()
    projects = {}
    if not os.path.exists(DATA_DIR): return {}
    
    for folder_name in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder_name)
        if os.path.isdir(folder_path):
            notes_file = os.path.join(folder_path, "notes.json")
            notes_content = ""
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, "r") as f:
                        notes_content = json.load(f).get("notes", "")
                except: pass
            
            projects[folder_name] = {"path": folder_path, "notes": notes_content}
    return projects

def delete_project(project_name):
    """
    Tries 3 times to delete the folder to fix 'File in Use' errors.
    """
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    
    # 1. Force Python to release file locks
    gc.collect()
    
    # 2. Retry Logic
    if os.path.exists(folder_path):
        for i in range(3): 
            try:
                shutil.rmtree(folder_path, ignore_errors=False)
                return True 
            except Exception as e:
                time.sleep(0.5) 
                if i == 2: 
                    try:
                        shutil.rmtree(folder_path, ignore_errors=True)
                        return True
                    except:
                        return False
    return False

def create_project(project_name):
    ensure_data_dir()
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        with open(os.path.join(folder_path, "notes.json"), "w") as f: json.dump({"notes": ""}, f)
        with open(os.path.join(folder_path, "chat_history.json"), "w") as f: json.dump([], f)
    return safe_name

def update_project_notes(project_name, new_notes):
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    
    # --- FIX STARTS HERE ---
    # Safety Check: If the folder is missing (Ghost Unit), recreate it!
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # --- FIX ENDS HERE ---

    with open(os.path.join(folder_path, "notes.json"), "w") as f: 
        json.dump({"notes": new_notes}, f)