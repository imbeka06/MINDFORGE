import os
import json
import shutil 

DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_projects():
    ensure_data_dir()
    projects = {}
    # Ensure we are looking at the most current version of the disk
    if not os.path.exists(DATA_DIR):
        return {}
        
    for folder_name in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder_name)
        if os.path.isdir(folder_path):
            notes_file = os.path.join(folder_path, "notes.json")
            notes_content = ""
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, "r") as f:
                        notes_content = json.load(f).get("notes", "")
                except:
                    notes_content = ""
            
            projects[folder_name] = {
                "path": folder_path,
                "notes": notes_content
            }
    return projects

def create_project(project_name):
    ensure_data_dir()
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        with open(os.path.join(folder_path, "notes.json"), "w") as f:
            json.dump({"notes": ""}, f)
        with open(os.path.join(folder_path, "chat_history.json"), "w") as f:
            json.dump([], f)
    return safe_name

def delete_project(project_name):
    """Completely nukes the folder."""
    # Clean name to match how it was stored
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            return True
        except Exception as e:
            print(f"Error during physical delete: {e}")
    return False

def update_project_notes(project_name, new_notes):
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    folder_path = os.path.join(DATA_DIR, safe_name)
    notes_file = os.path.join(folder_path, "notes.json")
    with open(notes_file, "w") as f:
        json.dump({"notes": new_notes}, f)